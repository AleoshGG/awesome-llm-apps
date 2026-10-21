#!/usr/bin/env python3
"""
VTEX Catalog Extractor Script
Extracts real product catalog data from public VTEX stores for specified departments:
- Línea Blanca
- Electrónica
- Oficina
- Abarrotes

Transforms the API responses into SQLAlchemy models (CategoryModel, ProviderModel,
ProductModel, ProductMediaModel) and exports them into an executable SQL seed:
backend/src/core/db/seeds/vtex_catalog.sql
"""

from __future__ import annotations

import argparse
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

# Configure paths:
# Script: backend/src/core/scripts/extract_vtex_catalog.py
# SCRIPT_DIR -> backend/src/core/scripts
# BACKEND_DIR -> backend
# ROOT_DIR -> project root (outside backend)
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parents[2]
ROOT_DIR = SCRIPT_DIR.parents[3]

# Add backend directory to sys.path so src.* modules can be imported
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load environment variables from ROOT_DIR / ".env"
env_file_path = ROOT_DIR / ".env"


def load_root_env(path: Path) -> None:
    """Loads environment variables from the project root .env file."""
    if not path.is_file():
        logging.warning("Root .env file not found at %s; using system environment variables.", path)
        return

    try:
        from dotenv import load_dotenv
        load_dotenv(path)
        logging.info("Loaded environment variables from %s via python-dotenv", path)
    except ImportError:
        # Fallback line-by-line parser if dotenv is not installed
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

# Import SQLAlchemy domain models from the existing codebase
from src.features.products.data.models.category_model import CategoryModel  # noqa: E402
from src.features.products.data.models.product_media_model import ProductMediaModel  # noqa: E402
from src.features.products.data.models.product_model import ProductModel  # noqa: E402
from src.features.providers.data.models.provider_model import ProviderModel  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("vtex_extractor")


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
    """Removes HTML tags and unescapes HTML entities from a string."""
    if not text:
        return ""
    unescaped = html.unescape(text)
    clean = re.sub(r"<[^>]+>", " ", unescaped)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


IGNORED_SPECIFICATIONS = {
    "fraud check",
    "tipo de envío",
    "máximo de venta",
    "multiean",
    "identificador externo de categoría",
    "url video",
    "preventa",
}


def clean_product_description(text: str, prod_name: str = "") -> str:
    """
    Cleans product descriptions to remove boilerplate, disclaimers,
    internal eCommerce flags, and repetitive marketing noise.
    """
    if not text:
        return prod_name

    # 1. Remove legal / visual disclaimers (reference images, changing labels/packaging)
    disclaimers = [
        r"Las imágenes[^.]*?(?:pueden cambiar[^\.]*\.?|sin previo aviso\.?|\.)",
        r"El diseño[s]? de etiquetas[^.]*?(?:pueden cambiar[^\.]*\.?|sin previo aviso\.?|\.)",
        r"Imágenes ilustrativas[^.]*?(?:\.)?",
    ]
    for d in disclaimers:
        text = re.sub(d, "", text, flags=re.IGNORECASE)

    # 2. Remove internal operational / boilerplate specs
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

    # 3. Clean up separators and whitespace carefully
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
    """Escapes string literals for PostgreSQL insertion, ensuring single-line strings."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    clean_val = re.sub(r"[\r\n\t]+", " ", str(value)).strip()
    escaped = clean_val.replace("'", "''").replace("\0", "")
    return f"'{escaped}'"


class VtexCatalogExtractor:
    """Extracts catalog data from VTEX and generates database model instances."""

    def __init__(
        self,
        account_name: str,
        environment: str = "vtexcommercestable",
        max_per_category: int = 300,
        page_size: int = 50,
        request_delay: float = 0.2,
    ) -> None:
        self.account_name = account_name
        self.environment = environment
        self.max_per_category = max_per_category
        self.page_size = min(page_size, 50)  # VTEX public search limit is 50 per page
        self.request_delay = request_delay
        self.base_url = f"https://{self.account_name}.{self.environment}.com.br"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

    def fetch_products(self, filter_query: str, offset_from: int, offset_to: int) -> list[dict[str, Any]]:
        """Queries the VTEX catalog search API for a given range and filter."""
        params = {
            "fq": filter_query,
            "_from": offset_from,
            "_to": offset_to,
            "O": "OrderByTopSaleDESC",
        }
        url = f"{self.base_url}/api/catalog_system/pub/products/search?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.headers)

        for attempt in range(1, 4):
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status in (200, 206):
                        content = resp.read().decode("utf-8")
                        return json.loads(content)
                    logger.warning("VTEX returned HTTP status %s on %s", resp.status, url)
            except Exception as e:
                logger.warning("Attempt %d/3 failed for URL %s: %s", attempt, url, e)
                time.sleep(1.0 * attempt)

        return []

    def extract_department_products(
        self,
        category_id: str,
        category_name: str,
        filter_query: str,
        categories_dict: dict[str, CategoryModel],
        providers_dict: dict[str, ProviderModel],
        products_dict: dict[str, ProductModel],
        media_list: list[ProductMediaModel],
    ) -> int:
        """Extracts products for a specific category up to max_per_category."""
        logger.info(
            "Extracting up to %d products for '%s' (%s) with filter '%s'...",
            self.max_per_category,
            category_name,
            category_id,
            filter_query,
        )

        # Register category model instance
        if category_id not in categories_dict:
            categories_dict[category_id] = CategoryModel(
                id=category_id,
                name=category_name,
            )

        extracted_count = 0
        current_offset = 0

        while extracted_count < self.max_per_category:
            batch_limit = min(self.page_size, self.max_per_category - extracted_count)
            offset_from = current_offset
            offset_to = current_offset + batch_limit - 1

            # VTEX legacy search hard limit is 2500
            if offset_from >= 2500:
                logger.info("Reached VTEX search offset ceiling of 2500 items for %s", category_name)
                break

            items = self.fetch_products(filter_query, offset_from, offset_to)
            if not items:
                logger.info("No more items returned by VTEX for %s at offset %d", category_name, offset_from)
                break

            for p in items:
                prod_raw_id = str(p.get("productId") or "")
                if not prod_raw_id:
                    continue

                prod_id = f"prod-vtex-{prod_raw_id}"
                if prod_id in products_dict:
                    continue

                # Extract brand / provider
                brand_name = (p.get("brand") or "Genérico").strip()
                prov_id = f"prov-{slugify(brand_name)}"
                if not prov_id or prov_id == "prov-":
                    prov_id = "prov-generico"

                if prov_id not in providers_dict:
                    providers_dict[prov_id] = ProviderModel(
                        id=prov_id,
                        name=brand_name,
                        address=f"Distribuidor Autorizado {brand_name}, México",
                        logo_url=f"https://placehold.co/256x256/1E3A8A/FFFFFF.png?text={urllib.parse.quote_plus(brand_name[:14])}",
                    )

                # Extract SKU variants, price and media
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

                # Require a valid price
                if price_cents <= 0:
                    continue

                # Extract images
                sku_images = main_sku.get("images", [])
                if not sku_images:
                    continue

                # Build clean description and attach specifications if available
                prod_name = p.get("productName", "").strip()
                raw_desc = clean_product_description(clean_html(p.get("description")), prod_name)
                specs_summary: list[str] = []
                for spec_name in (p.get("allSpecifications") or []):
                    sn_clean = spec_name.strip().lower()
                    if sn_clean in IGNORED_SPECIFICATIONS or sn_clean.startswith("benefits"):
                        continue
                    spec_vals = p.get(spec_name)
                    if spec_vals and isinstance(spec_vals, list):
                        clean_vals = [re.sub(r"[\r\n\t]+", " ", str(v)).strip() for v in spec_vals if str(v).strip()]
                        if clean_vals:
                            specs_summary.append(f"{spec_name}: {', '.join(clean_vals)}")
                    if len(specs_summary) >= 5:
                        break

                desc_parts = [raw_desc] if raw_desc else [prod_name]
                if specs_summary:
                    desc_parts.append(" | ".join(specs_summary))
                joined_desc = " - ".join(desc_parts)
                final_description = clean_product_description(joined_desc, prod_name)

                # Instantiate ProductModel
                product_model = ProductModel(
                    id=prod_id,
                    name=prod_name,
                    description=final_description[:1000],  # Keep within reasonable text size
                    price_list_cents=price_cents,
                    provider_id=prov_id,
                    category_id=category_id,
                )
                products_dict[prod_id] = product_model

                # Instantiate ProductMediaModel instances (up to 3 images per product)
                for idx, img in enumerate(sku_images[:3]):
                    img_url = img.get("imageUrl")
                    if img_url:
                        media_model = ProductMediaModel(
                            id=f"media-vtex-{prod_raw_id}-{idx+1}",
                            url=img_url,
                            product_id=prod_id,
                            is_main=(idx == 0),
                        )
                        media_list.append(media_model)

                extracted_count += 1
                if extracted_count >= self.max_per_category:
                    break

            current_offset += len(items)
            time.sleep(self.request_delay)

        logger.info(
            "Successfully extracted %d products for category '%s'",
            extracted_count,
            category_name,
        )
        return extracted_count


def generate_sql_seed(
    categories: list[CategoryModel],
    providers: list[ProviderModel],
    products: list[ProductModel],
    media: list[ProductMediaModel],
    output_path: Path,
) -> None:
    """Serializes the database models into an executable SQL seed file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("-- Real VTEX Product Catalog Seed for PostgreSQL\n")
        f.write("-- Departments: Línea Blanca, Electrónica, Oficina, Abarrotes\n")
        f.write(f"-- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(
            f"-- Summary: {len(categories)} categories, {len(providers)} providers, "
            f"{len(products)} products, {len(media)} media files.\n\n"
        )
        f.write("BEGIN;\n\n")

        # 1. Categories
        f.write("-- 1. Categories\n")
        f.write("INSERT INTO categories (id, name) VALUES\n")
        cat_lines = [f"    ({escape_sql(c.id)}, {escape_sql(c.name)})" for c in categories]
        f.write(",\n".join(cat_lines))
        f.write("\nON CONFLICT (id) DO NOTHING;\n\n")

        # 2. Providers
        f.write("-- 2. Providers (Brands)\n")
        f.write("INSERT INTO providers (id, name, address, logo_url) VALUES\n")
        prov_lines = [
            f"    ({escape_sql(p.id)}, {escape_sql(p.name)}, {escape_sql(p.address)}, {escape_sql(p.logo_url)})"
            for p in providers
        ]
        f.write(",\n".join(prov_lines))
        f.write("\nON CONFLICT (id) DO NOTHING;\n\n")

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
        f.write("\nON CONFLICT (id) DO NOTHING;\n\n")

        # 4. Media
        f.write("-- 4. Media Products\n")
        f.write("INSERT INTO media_products (id, url, product_id, is_main) VALUES\n")
        media_lines = [
            f"    ({escape_sql(m.id)}, {escape_sql(m.url)}, {escape_sql(m.product_id)}, {escape_sql(m.is_main)})"
            for m in media
        ]
        f.write(",\n".join(media_lines))
        f.write("\nON CONFLICT (id) DO NOTHING;\n\n")

        f.write("COMMIT;\n")

    logger.info("Generated SQL seed written to: %s (%d bytes)", output_path, output_path.stat().st_size)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract real product catalog from VTEX into SQL seed.")
    parser.add_argument(
        "--account",
        default=os.getenv("VTEX_STORE_ACCOUNT", "chedrauimx"),
        help="VTEX store account name (default: from VTEX_STORE_ACCOUNT or 'chedrauimx')",
    )
    parser.add_argument(
        "--environment",
        default=os.getenv("VTEX_ENVIRONMENT", "vtexcommercestable"),
        help="VTEX environment (default: 'vtexcommercestable')",
    )
    parser.add_argument(
        "--max-per-category",
        type=int,
        default=int(os.getenv("VTEX_MAX_PRODUCTS_PER_CATEGORY", "250")),
        help="Max products to fetch per category (default: 250)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_DIR / "src" / "core" / "db" / "seeds" / "vtex_catalog.sql",
        help="Output path for the generated SQL file",
    )
    args = parser.parse_args()

    logger.info("Initializing VTEX Extractor using account: '%s'", args.account)
    logger.info("Max products per category: %d", args.max_per_category)

    extractor = VtexCatalogExtractor(
        account_name=args.account,
        environment=args.environment,
        max_per_category=args.max_per_category,
        page_size=int(os.getenv("VTEX_PAGE_SIZE", "50")),
        request_delay=float(os.getenv("VTEX_REQUEST_DELAY_SECONDS", "0.2")),
    )

    # Required departments configuration:
    # 1. Línea blanca (Chedraui Dept 13: Electrodomesticos y linea blanca)
    # 2. Electrónica (Chedraui Dept 8: Tecnologia)
    # 3. Oficina (Chedraui Dept 14: Papeleria y oficina)
    # 4. Abarrotes (Chedraui Dept 1: Supermercado / Cat 107 Despensa)
    target_departments = [
        {
            "id": "cat-linea-blanca",
            "name": "Línea Blanca",
            "filter": "C:/13/",
        },
        {
            "id": "cat-electronica",
            "name": "Electrónica",
            "filter": "C:/8/",
        },
        {
            "id": "cat-oficina",
            "name": "Oficina",
            "filter": "C:/14/",
        },
        {
            "id": "cat-abarrotes",
            "name": "Abarrotes",
            "filter": "C:/1/107/",
        },
    ]

    categories_dict: dict[str, CategoryModel] = {}
    providers_dict: dict[str, ProviderModel] = {}
    products_dict: dict[str, ProductModel] = {}
    media_list: list[ProductMediaModel] = []

    for dept in target_departments:
        extractor.extract_department_products(
            category_id=dept["id"],
            category_name=dept["name"],
            filter_query=dept["filter"],
            categories_dict=categories_dict,
            providers_dict=providers_dict,
            products_dict=products_dict,
            media_list=media_list,
        )

    logger.info("=" * 60)
    logger.info("Extraction summary:")
    logger.info("  Categories: %d", len(categories_dict))
    logger.info("  Providers (Brands): %d", len(providers_dict))
    logger.info("  Products: %d", len(products_dict))
    logger.info("  Product Media: %d", len(media_list))
    logger.info("=" * 60)

    generate_sql_seed(
        categories=list(categories_dict.values()),
        providers=list(providers_dict.values()),
        products=list(products_dict.values()),
        media=media_list,
        output_path=args.output,
    )

    logger.info("Catalog extraction and SQL generation completed successfully!")


if __name__ == "__main__":
    main()
