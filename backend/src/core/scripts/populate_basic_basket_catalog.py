#!/usr/bin/env python3
"""
Populate Basic Basket Catalog Script
Extracts real grocery products from VTEX (Chedraui Mexico) specifically
to satisfy all 24 items required by the Mexican Basic Basket (BASIC_BASKET)
used by DeterministicBasicBasketService.

Transforms API responses into SQLAlchemy models:
- CategoryModel
- ProviderModel
- ProductModel
- ProductMediaModel

Generates an executable SQL seed:
backend/src/core/db/seeds/basic_basket_products.sql

Optionally (or by default) applies the SQL directly to the PostgreSQL database
and performs an end-to-end verification of candidate coverage for all 24 items.
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# Configure paths
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parents[2]
ROOT_DIR = SCRIPT_DIR.parents[3]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load environment variables
env_file_path = ROOT_DIR / ".env"


def load_root_env(path: Path) -> None:
    """Loads environment variables from the project root .env file."""
    if not path.is_file():
        logging.warning("Root .env file not found at %s; using system environment.", path)
        return

    try:
        from dotenv import load_dotenv

        load_dotenv(path)
        logging.info("Loaded environment variables from %s via python-dotenv", path)
    except ImportError:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val
        logging.info("Loaded environment variables from %s via fallback parser", path)


load_root_env(env_file_path)

# Import SQLAlchemy domain models
from src.features.products.data.models.category_model import CategoryModel  # noqa: E402
from src.features.products.data.models.product_media_model import ProductMediaModel  # noqa: E402
from src.features.products.data.models.product_model import ProductModel  # noqa: E402
from src.features.providers.data.models.provider_model import ProviderModel  # noqa: E402
from src.features.sales_agent.data.services.deterministic_basic_basket_service import BASIC_BASKET  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("basic_basket_populator")


def slugify(text: str) -> str:
    """Converts a text string into an URL/ID safe slug."""
    text = text.lower()
    text = re.sub(r"[áàäâ]", "a", text)
    text = re.sub(r"[éèëê]", "e", text)
    text = re.sub(r"[íìïî]", "i", text)
    text = re.sub(r"[óòöô]", "o", text)
    text = re.sub(r"[úùüû]", "u", text)
    text = re.sub(r"[ñ]", "n", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def clean_html(text: str | None) -> str:
    """Removes HTML tags and unescapes entities."""
    if not text:
        return ""
    unescaped = html.unescape(text)
    clean = re.sub(r"<[^>]+>", " ", unescaped)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def clean_product_description(text: str, prod_name: str = "") -> str:
    """Removes eCommerce noise and disclaimers from descriptions."""
    if not text:
        return prod_name

    disclaimers = [
        r"Las imágenes[^.]*?(?:pueden cambiar[^\.]*\.?|sin previo aviso\.?|\.)",
        r"El diseño[s]? de etiquetas[^.]*?(?:pueden cambiar[^\.]*\.?|sin previo aviso\.?|\.)",
        r"Imágenes ilustrativas[^.]*?(?:\.)?",
    ]
    for d in disclaimers:
        text = re.sub(d, "", text, flags=re.IGNORECASE)

    noise_specs = [
        r"Fraud Check:\s*[^|\-]+",
        r"Tipo de envío:\s*[^|\-]+",
        r"Máximo de venta:\s*[^|\-]+",
        r"MultiEan:\s*[^|\-]+",
        r"Identificador Externo(?: de Categoría)?:\s*[^|\-]+",
        r"\bBenefits(?:\s*\d+)?(?::\s*[^|\-]+)?",
        r"URL Video:\s*[^|\-]+",
        r"Preventa:\s*[^|\-]+",
    ]
    for pattern in noise_specs:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"(\s*\|\s*)+", " | ", text)
    text = re.sub(r"(\s*-\s*\|\s*)+", " - ", text)
    text = re.sub(r"(\s*\|\s*-\s*)+", " - ", text)
    text = re.sub(r"\s*\|\s*$", "", text)
    text = re.sub(r"\s*-\s*$", "", text)
    text = re.sub(r"^\s*-\s*", "", text)
    text = re.sub(r"^\s*\|\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip(" -|")

    if not text and prod_name:
        text = prod_name
    return text


def escape_sql(value: Any) -> str:
    """Escapes string literals for PostgreSQL insertion."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    clean_val = re.sub(r"[\r\n\t]+", " ", str(value)).strip()
    escaped = clean_val.replace("'", "''").replace("\0", "")
    return f"'{escaped}'"


# Keyword enrichments for specific basic basket specs so that ProductRepositoryAdapter.find_by_query
# matches products whose commercial names differ slightly (e.g. 'Pechuga de pollo' -> 'carne de pollo')
SPEC_ENRICHMENT_TAGS: dict[str, str] = {
    "corn_tortilla": "Tortilla de maíz nixtamalizada básica mexicana",
    "rice": "Arroz en grano super extra",
    "black_beans": "Frijol negro mexicano seleccionado",
    "white_bread": "Pan blanco de caja clásico",
    "soup_pasta": "Pasta para sopa de trigo",
    "vegetable_oil": "Aceite vegetal comestible puro",
    "standard_sugar": "Azúcar estándar de caña pura",
    "flaked_tuna": "Atún en hojuelas en conserva",
    "tomato_sardines": "Sardina en salsa de tomate mexicana",
    "cow_milk": "Leche entera de vaca pasteurizada",
    "chicken_eggs": "Huevo de gallina blanco fresco",
    "chicken_meat": "Carne de pollo fresca y limpia",
    "beef": "Carne de res fresca corte selecto",
    "pork": "Carne de cerdo fresca corte selecto",
    "tomato": "Jitomate saladet fresco por kg",
    "white_onion": "Cebolla blanca fresca por kg",
    "jalapeno": "Chile jalapeño fresco mexicano por kg",
    "white_potato": "Papa blanca fresca por kg",
    "carrot": "Zanahoria fresca por kg",
    "lime": "Limón fresco mexicano",
    "apple": "Manzana fresca seleccionada",
    "banana": "Plátano fresco mexicano",
    "bar_soap": "Jabón de tocador en barra humectante",
    "toilet_paper": "Papel higiénico suave y rendidor",
}


CATEGORIES_DEFINITION = [
    {"id": "cat-frutas-verduras", "name": "Frutas y Verduras"},
    {"id": "cat-carnes", "name": "Carnes, Pescados y Mariscos"},
    {"id": "cat-lacteos-huevo", "name": "Lácteos y Huevo"},
    {"id": "cat-panaderia-tortilleria", "name": "Panadería y Tortillería"},
    {"id": "cat-desechables-higiene", "name": "Desechables y Papel"},
    {"id": "cat-cuidado-personal", "name": "Cuidado e Higiene Personal"},
    {"id": "cat-abarrotes", "name": "Abarrotes"},
]


class VtexBasicBasketPopulator:
    """Extracts products specifically to satisfy Mexican Basic Basket specifications."""

    def __init__(
        self,
        account_name: str,
        environment: str = "vtexcommercestable",
        request_delay: float = 0.25,
    ) -> None:
        self.account_name = account_name
        self.environment = environment
        self.request_delay = request_delay
        self.base_url = f"https://{self.account_name}.{self.environment}.com.br"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        }

    def fetch_products(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Queries the VTEX catalog search API."""
        encoded_query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        url = f"{self.base_url}/api/catalog_system/pub/products/search?{encoded_query}"
        req = urllib.request.Request(url, headers=self.headers)

        for attempt in range(1, 4):
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status in (200, 206):
                        content = resp.read().decode("utf-8")
                        return json.loads(content)
            except Exception as e:
                logger.warning("Attempt %d/3 failed for URL %s: %s", attempt, url, e)
                time.sleep(1.0 * attempt)

        return []

    def process_raw_products(
        self,
        raw_items: list[dict[str, Any]],
        category_id: str,
        enrichment_tag: str | None,
        required_tokens: list[str],
        reject_keywords: list[str],
        categories_dict: dict[str, CategoryModel],
        providers_dict: dict[str, ProviderModel],
        products_dict: dict[str, ProductModel],
        media_list: list[ProductMediaModel],
        max_items: int = 6,
    ) -> int:
        """Parses raw VTEX products and inserts them into dictionaries."""
        added = 0
        for p in raw_items:
            if added >= max_items:
                break

            # Filter out non-food categories (e.g. toys, pet accessories)
            categories_hierarchy = p.get("categories", [])
            is_invalid = any(
                ("Mascotas" in c or "Jugueteria" in c or "Vehiculos" in c)
                for c in categories_hierarchy
            )
            if is_invalid:
                continue

            prod_name = p.get("productName", "").strip()
            name_lower = prod_name.lower()

            # Must contain at least one required token in the name
            if required_tokens and not any(rt in name_lower for rt in required_tokens):
                continue

            # Must not contain any reject keyword
            if any(rk in name_lower for rk in reject_keywords):
                continue

            prod_raw_id = str(p.get("productId") or "")
            if not prod_raw_id:
                continue

            prod_id = f"prod-vtex-{prod_raw_id}"
            if prod_id in products_dict:
                continue

            # Provider / Brand
            brand_name = (p.get("brand") or "Genérico").strip()
            prov_id = f"prov-{slugify(brand_name)}"
            if not prov_id or prov_id == "prov-":
                prov_id = "prov-generico"

            if prov_id not in providers_dict:
                providers_dict[prov_id] = ProviderModel(
                    id=prov_id,
                    name=brand_name,
                    address=f"Distribuidor Autorizado {brand_name}, México",
                    logo_url=(
                        f"https://placehold.co/256x256/1E3A8A/FFFFFF.png?text="
                        f"{urllib.parse.quote_plus(brand_name[:14])}"
                    ),
                )

            # SKUs and Price
            skus = p.get("items", [])
            if not skus:
                continue
            main_sku = skus[0]
            sellers = main_sku.get("sellers", [])
            if not sellers:
                continue
            offer = sellers[0].get("commertialOffer", {})
            price = offer.get("Price") or offer.get("ListPrice") or 0.0
            price_cents = int(round(float(price) * 100))
            if price_cents <= 0:
                continue

            # Media
            sku_images = main_sku.get("images", [])
            if not sku_images:
                continue

            raw_desc = clean_product_description(clean_html(p.get("description")), prod_name)

            desc_parts = [prod_name]
            if enrichment_tag:
                desc_parts.append(enrichment_tag)
            if raw_desc and raw_desc != prod_name:
                desc_parts.append(raw_desc)

            final_desc = " - ".join(desc_parts)[:900]

            # ProductModel
            products_dict[prod_id] = ProductModel(
                id=prod_id,
                name=prod_name,
                description=final_desc,
                price_list_cents=price_cents,
                provider_id=prov_id,
                category_id=category_id,
            )

            # MediaModels
            for idx, img in enumerate(sku_images[:3]):
                img_url = img.get("imageUrl")
                if img_url:
                    media_list.append(
                        ProductMediaModel(
                            id=f"media-vtex-{prod_raw_id}-{idx+1}",
                            url=img_url,
                            product_id=prod_id,
                            is_main=(idx == 0),
                        )
                    )

            added += 1

        return added


# Targeted search configurations with category scoping, required name tokens, and negative keywords
BASKET_SEARCH_SPECS: list[dict[str, Any]] = [
    {
        "key": "corn_tortilla",
        "category_id": "cat-panaderia-tortilleria",
        "department_filter": "C:/1/109/",
        "queries": ["tortilla de maíz", "tortilla maiz", "tortilla"],
        "required_tokens": ["tortilla"],
        "reject": ["harina", "trigo"],
        "max_products": 6,
    },
    {
        "key": "rice",
        "category_id": "cat-abarrotes",
        "department_filter": "C:/1/107/",
        "queries": ["arroz super extra", "arroz en grano", "arroz"],
        "required_tokens": ["arroz"],
        "reject": ["arrocera", "leche de arroz", "galletas", "vinagre"],
        "max_products": 6,
    },
    {
        "key": "black_beans",
        "category_id": "cat-abarrotes",
        "department_filter": "C:/1/107/",
        "queries": ["frijol negro queretaro", "frijol negro"],
        "required_tokens": ["frijol"],
        "reject": [],
        "max_products": 6,
    },
    {
        "key": "white_bread",
        "category_id": "cat-panaderia-tortilleria",
        "department_filter": "C:/1/109/",
        "queries": ["pan blanco de caja", "pan blanco bimbo", "pan blanco"],
        "required_tokens": ["pan"],
        "reject": ["tostado", "molido", "integral"],
        "max_products": 6,
    },
    {
        "key": "soup_pasta",
        "category_id": "cat-abarrotes",
        "department_filter": "C:/1/107/",
        "queries": ["pasta para sopa fideo", "pasta para sopa la moderna", "pasta para sopa"],
        "required_tokens": ["pasta", "fideo"],
        "reject": [],
        "max_products": 6,
    },
    {
        "key": "vegetable_oil",
        "category_id": "cat-abarrotes",
        "department_filter": "C:/1/107/",
        "queries": ["aceite vegetal nutrioli", "aceite canola canoil", "aceite vegetal"],
        "required_tokens": ["aceite"],
        "reject": ["sardina", "atún", "oliva", "motor"],
        "max_products": 6,
    },
    {
        "key": "standard_sugar",
        "category_id": "cat-abarrotes",
        "department_filter": "C:/1/107/",
        "queries": ["azúcar chedraui estándar", "azúcar estándar", "azucar estandar"],
        "required_tokens": ["azúcar", "azucar"],
        "reject": ["sin azúcar", "sin azucar", "yoghurt", "yogurt", "splenda", "sustituto", "glass", "café", "cafe"],
        "max_products": 6,
    },
    {
        "key": "flaked_tuna",
        "category_id": "cat-abarrotes",
        "department_filter": "C:/1/107/",
        "queries": ["atún en hojuelas", "atún aleta amarilla en agua", "atún dolores"],
        "required_tokens": ["atún", "atun"],
        "reject": ["shampoo", "crema", "chilorio", "ensalada"],
        "max_products": 6,
    },
    {
        "key": "tomato_sardines",
        "category_id": "cat-abarrotes",
        "department_filter": "C:/1/107/",
        "queries": ["sardina en tomate dolores", "sardina en salsa de tomate", "sardina tomate"],
        "required_tokens": ["sardina"],
        "reject": ["caldo", "cubos", "consomate"],
        "max_products": 6,
    },
    {
        "key": "cow_milk",
        "category_id": "cat-lacteos-huevo",
        "department_filter": "C:/1/105/",
        "queries": ["leche entera lala", "leche selecto entera", "leche entera alpura"],
        "required_tokens": ["leche"],
        "reject": ["saborizada", "chocolate", "yomi", "condensada", "polvo", "galletas", "dulce de leche", "combinado", "crema"],
        "max_products": 8,
    },
    {
        "key": "chicken_eggs",
        "category_id": "cat-lacteos-huevo",
        "department_filter": "C:/1/105/",
        "queries": ["huevo blanco bachoco", "huevo blanco san juan", "huevo blanco 18 piezas"],
        "required_tokens": ["huevo"],
        "reject": ["clara", "liquida", "codorniz", "crepera", "juguete", "hatchimals", "chocolate"],
        "max_products": 8,
    },
    {
        "key": "chicken_meat",
        "category_id": "cat-carnes",
        "department_filter": "C:/1/102/",
        "queries": ["pechuga de pollo", "milanesa de pollo", "pierna y muslo de pollo", "pollo entero"],
        "required_tokens": ["pollo"],
        "reject": ["chorizo", "molleja", "carnaza", "croquetas", "hueso"],
        "max_products": 8,
    },
    {
        "key": "beef",
        "category_id": "cat-carnes",
        "department_filter": "C:/1/102/",
        "queries": ["bistec de res", "molida de res", "milanesa de res"],
        "required_tokens": ["res"],
        "reject": ["brocheta", "albóndiga", "albondiga", "empanada", "snack", "jerky"],
        "max_products": 8,
    },
    {
        "key": "pork",
        "category_id": "cat-carnes",
        "department_filter": "C:/1/102/",
        "queries": ["chuleta de cerdo", "milanesa de cerdo", "bistec de cerdo"],
        "required_tokens": ["cerdo"],
        "reject": ["manteca", "chorizo", "chicharrón"],
        "max_products": 8,
    },
    {
        "key": "tomato",
        "category_id": "cat-frutas-verduras",
        "department_filter": "C:/1/101/",
        "queries": ["tomate saladet", "jitomate saladet"],
        "required_tokens": ["tomate", "jitomate"],
        "reject": ["semilla", "hortaflor", "puré", "pasta"],
        "max_products": 6,
    },
    {
        "key": "white_onion",
        "category_id": "cat-frutas-verduras",
        "department_filter": "C:/1/101/",
        "queries": ["cebolla blanca por kg", "cebolla blanca"],
        "required_tokens": ["cebolla"],
        "reject": ["semilla", "hortaflor", "polvo", "sandia", "sandía"],
        "max_products": 6,
    },
    {
        "key": "jalapeno",
        "category_id": "cat-frutas-verduras",
        "department_filter": "C:/1/101/",
        "queries": ["chile jalapeño por kg", "chile jalapeño"],
        "required_tokens": ["jalapeño", "jalapeno", "chile"],
        "reject": ["semilla", "hortaflor", "salsa", "frijoles"],
        "max_products": 6,
    },
    {
        "key": "white_potato",
        "category_id": "cat-frutas-verduras",
        "department_filter": "C:/1/101/",
        "queries": ["papa blanca por kg", "papa blanca"],
        "required_tokens": ["papa"],
        "reject": ["semilla", "fritas", "sabritas", "puré", "papaya"],
        "max_products": 6,
    },
    {
        "key": "carrot",
        "category_id": "cat-frutas-verduras",
        "department_filter": "C:/1/101/",
        "queries": ["zanahoria por kg", "zanahoria"],
        "required_tokens": ["zanahoria"],
        "reject": ["pastel", "jugo", "sopa", "maruchan"],
        "max_products": 6,
    },
    {
        "key": "lime",
        "category_id": "cat-frutas-verduras",
        "department_filter": "C:/1/101/",
        "queries": ["limón sin semilla", "limón colima", "limón por kg"],
        "required_tokens": ["limón", "limon"],
        "reject": [
            "fibra",
            "esponja",
            "mayonesa",
            "detergente",
            "polvo",
            "té",
            "te",
            "sustituto",
            "refresco",
            "maruchan",
            "filón",
            "semilla",
        ],
        "max_products": 6,
    },
    {
        "key": "apple",
        "category_id": "cat-frutas-verduras",
        "department_filter": "C:/1/101/",
        "queries": ["manzana golden por kg", "manzana red delicious", "manzana fuji"],
        "required_tokens": ["manzana"],
        "reject": ["jugo", "polvo", "tang", "clight", "vinagre", "compota"],
        "max_products": 6,
    },
    {
        "key": "banana",
        "category_id": "cat-frutas-verduras",
        "department_filter": "C:/1/101/",
        "queries": ["plátano chiapas por kg", "plátano tabasco", "plátano macho"],
        "required_tokens": ["plátano", "platano"],
        "reject": ["frito", "chips", "dulce"],
        "max_products": 6,
    },
    {
        "key": "bar_soap",
        "category_id": "cat-cuidado-personal",
        "department_filter": "C:/11/1103/",
        "queries": ["jabón de tocador palmolive", "jabón de tocador lirio", "jabón de tocador nordiko"],
        "required_tokens": ["jabón", "jabon"],
        "reject": ["líquido", "liquido", "trastes", "lavandería", "ropa", "polvo", "detergente", "shampoo"],
        "max_products": 6,
    },
    {
        "key": "toilet_paper",
        "category_id": "cat-desechables-higiene",
        "department_filter": "C:/1/",
        "queries": ["papel higiénico pétalo", "papel higiénico premier", "papel higiénico suavel"],
        "required_tokens": ["papel higiénico", "papel higienico", "higiénico", "higienico"],
        "reject": ["servilleta", "toalla", "pañuelo", "facial"],
        "max_products": 6,
    },
]


def generate_sql_seed(
    categories: list[CategoryModel],
    providers: list[ProviderModel],
    products: list[ProductModel],
    media: list[ProductMediaModel],
    output_path: Path,
) -> None:
    """Serializes database models into an executable SQL seed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("-- Real VTEX Mexican Basic Basket Catalog Seed for PostgreSQL\n")
        f.write(f"-- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(
            f"-- Summary: {len(categories)} categories, {len(providers)} providers, "
            f"{len(products)} products, {len(media)} media records.\n\n"
        )
        f.write("BEGIN;\n\n")

        # 1. Categories
        f.write("-- 1. Categories\n")
        f.write("INSERT INTO categories (id, name) VALUES\n")
        cat_lines = [f"    ({escape_sql(c.id)}, {escape_sql(c.name)})" for c in categories]
        f.write(",\n".join(cat_lines))
        f.write("\nON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;\n\n")

        # 2. Providers
        f.write("-- 2. Providers\n")
        f.write("INSERT INTO providers (id, name, address, logo_url) VALUES\n")
        prov_lines = [
            f"    ({escape_sql(p.id)}, {escape_sql(p.name)}, {escape_sql(p.address)}, {escape_sql(p.logo_url)})"
            for p in providers
        ]
        f.write(",\n".join(prov_lines))
        f.write(
            "\nON CONFLICT (id) DO UPDATE SET "
            "name = EXCLUDED.name, address = EXCLUDED.address, logo_url = EXCLUDED.logo_url;\n\n"
        )

        # 3. Products
        f.write("-- 3. Products\n")
        f.write(
            "INSERT INTO products (id, name, description, price_list_cents, provider_id, category_id) VALUES\n"
        )
        prod_lines = [
            f"    ({escape_sql(pr.id)}, {escape_sql(pr.name)}, {escape_sql(pr.description)}, "
            f"{pr.price_list_cents}, {escape_sql(pr.provider_id)}, {escape_sql(pr.category_id)})"
            for pr in products
        ]
        f.write(",\n".join(prod_lines))
        f.write(
            "\nON CONFLICT (id) DO UPDATE SET "
            "name = EXCLUDED.name, description = EXCLUDED.description, "
            "price_list_cents = EXCLUDED.price_list_cents, provider_id = EXCLUDED.provider_id, "
            "category_id = EXCLUDED.category_id;\n\n"
        )

        # 4. Media
        f.write("-- 4. Media\n")
        f.write("INSERT INTO media_products (id, url, product_id, is_main) VALUES\n")
        media_lines = [
            f"    ({escape_sql(m.id)}, {escape_sql(m.url)}, {escape_sql(m.product_id)}, {escape_sql(m.is_main)})"
            for m in media
        ]
        f.write(",\n".join(media_lines))
        f.write("\nON CONFLICT (id) DO UPDATE SET url = EXCLUDED.url, is_main = EXCLUDED.is_main;\n\n")

        f.write("COMMIT;\n")

    logger.info("Generated SQL seed written to: %s (%d bytes)", output_path, output_path.stat().st_size)


def apply_sql_to_db(sql_path: Path) -> None:
    """Applies the SQL seed file to PostgreSQL database using sync_engine."""
    from sqlalchemy import text
    from src.core.db.session import sync_engine

    logger.info("Applying SQL seed %s to database...", sql_path)
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    with sync_engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    logger.info("Successfully executed SQL seed in database.")


async def verify_basic_basket_coverage() -> tuple[int, int]:
    """Verifies that all 24 items in BASIC_BASKET have candidates in the database."""
    from src.core.db.session import AsyncSessionLocal
    from src.features.products.data.repositories.product_repository_adapter import (
        ProductRepositoryAdapter,
    )
    from src.features.products.domain.entities.product_query_entity import ProductQuery

    logger.info("Verifying basic basket coverage against database...")
    found_count = 0
    missing_count = 0

    async with AsyncSessionLocal() as session:
        repo = ProductRepositoryAdapter(session)
        print("\n" + "=" * 90)
        print(f"{'BASIC BASKET ITEM':<28} | {'STATUS':<8} | {'TOP CANDIDATES'}")
        print("=" * 90)

        for spec in BASIC_BASKET:
            candidates = []
            for q in spec.queries:
                res = await repo.find_by_query(ProductQuery(name=q, limit=5))
                if res:
                    candidates.extend(res)

            if candidates:
                found_count += 1
                sample_names = ", ".join([f"'{c.name}'" for c in candidates[:2]])
                print(f"{spec.label:<28} | ✅ OK    | {sample_names}")
            else:
                missing_count += 1
                print(f"{spec.label:<28} | ❌ MISS  | No candidate found for {spec.queries}")

        print("=" * 90)
        print(f"Summary: {found_count} / {len(BASIC_BASKET)} items covered ({missing_count} missing)")
        print("=" * 90 + "\n")

    return found_count, missing_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate Mexican basic basket products from VTEX and update database."
    )
    parser.add_argument(
        "--account",
        default=os.getenv("VTEX_STORE_ACCOUNT", "chedrauimx"),
        help="VTEX store account name (default: 'chedrauimx')",
    )
    parser.add_argument(
        "--environment",
        default=os.getenv("VTEX_ENVIRONMENT", "vtexcommercestable"),
        help="VTEX environment (default: 'vtexcommercestable')",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_DIR / "src" / "core" / "db" / "seeds" / "basic_basket_products.sql",
        help="Output path for the generated SQL file",
    )
    parser.add_argument(
        "--apply-db",
        action="store_true",
        default=True,
        help="Apply the SQL seed to the active database (default: True)",
    )
    parser.add_argument(
        "--no-apply-db",
        dest="apply_db",
        action="store_false",
        help="Do not apply SQL to database",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Skip extraction and only run database coverage verification",
    )

    args = parser.parse_args()

    if args.verify_only:
        found, missing = asyncio.run(verify_basic_basket_coverage())
        sys.exit(0 if missing == 0 else 1)

    logger.info("Initializing VTEX Basic Basket Populator (Account: %s)", args.account)

    populator = VtexBasicBasketPopulator(
        account_name=args.account,
        environment=args.environment,
        request_delay=float(os.getenv("VTEX_REQUEST_DELAY_SECONDS", "0.2")),
    )

    categories_dict: dict[str, CategoryModel] = {
        c["id"]: CategoryModel(id=c["id"], name=c["name"])
        for c in CATEGORIES_DEFINITION
    }
    providers_dict: dict[str, ProviderModel] = {}
    products_dict: dict[str, ProductModel] = {}
    media_list: list[ProductMediaModel] = []

    # 1. Fetch targeted products for each basic basket item
    for item_spec in BASKET_SEARCH_SPECS:
        key = item_spec["key"]
        cat_id = item_spec["category_id"]
        queries = item_spec["queries"]
        dept_filter = item_spec.get("department_filter")
        required_tokens = [rt.lower() for rt in item_spec.get("required_tokens", [])]
        reject_list = [r.lower() for r in item_spec.get("reject", [])]
        max_p = item_spec.get("max_products", 6)
        enrichment = SPEC_ENRICHMENT_TAGS.get(key)

        logger.info("Extracting products for basic basket spec '%s'...", key)
        items_for_spec = 0

        for q in queries:
            if items_for_spec >= max_p:
                break
            params: dict[str, Any] = {
                "ft": q,
                "_from": 0,
                "_to": max_p,
                "O": "OrderByTopSaleDESC",
            }
            if dept_filter:
                params["fq"] = dept_filter

            raw_products = populator.fetch_products(params)
            added = populator.process_raw_products(
                raw_items=raw_products,
                category_id=cat_id,
                enrichment_tag=enrichment,
                required_tokens=required_tokens,
                reject_keywords=reject_list,
                categories_dict=categories_dict,
                providers_dict=providers_dict,
                products_dict=products_dict,
                media_list=media_list,
                max_items=max_p - items_for_spec,
            )
            items_for_spec += added
            time.sleep(populator.request_delay)

    logger.info("=" * 60)
    logger.info("Extracted summary for Basic Basket:")
    logger.info("  Categories: %d", len(categories_dict))
    logger.info("  Providers: %d", len(providers_dict))
    logger.info("  Products: %d", len(products_dict))
    logger.info("  Product Media: %d", len(media_list))
    logger.info("=" * 60)

    # 2. Generate SQL file
    generate_sql_seed(
        categories=list(categories_dict.values()),
        providers=list(providers_dict.values()),
        products=list(products_dict.values()),
        media=media_list,
        output_path=args.output,
    )

    # 3. Apply to database if requested
    if args.apply_db:
        apply_sql_to_db(args.output)
        found, missing = asyncio.run(verify_basic_basket_coverage())
        if missing > 0:
            logger.warning("Basic basket has %d missing items after update.", missing)
            sys.exit(1)
        else:
            logger.info("All 24 basic basket items are successfully covered in the database!")


if __name__ == "__main__":
    main()
