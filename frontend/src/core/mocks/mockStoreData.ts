import type { CategoryEntity } from '../../features/products/domain/entities/category.entity'
import type { ProductDetailEntity } from '../../features/products/domain/entities/productDetail.entity'
import type { ProviderEntity } from '../../features/providers/domain/entities/provider.entity'
import type { CartItemEntity } from '../../features/sales/domain/entities/cartItem.entity'
import type { SaleEntity } from '../../features/sales/domain/entities/sale.entity'
import type { AgentTranscriptMessageEntity } from '../../features/sales_agent/domain/entities/salesAgent.entity'

export const MOCK_CATEGORIES: CategoryEntity[] = [
  { id: 'cat-shampoo', name: 'Shampoo' },
  { id: 'cat-boots', name: 'Botas' },
  { id: 'cat-mice', name: 'Mouse' },
  { id: 'cat-fans', name: 'Ventiladores' },
  { id: 'cat-gifts', name: 'Regalos' },
  { id: 'cat-accessories', name: 'Accesorios' },
]

export const MOCK_PROVIDERS: ProviderEntity[] = [
  {
    id: 'prov-care',
    name: 'Natura Care México',
    address: 'Av. Insurgentes Sur 1602, Ciudad de México',
    logoUrl: 'https://placehold.co/256x256/0F766E/FFFFFF.png?text=NC',
  },
  {
    id: 'prov-outdoor',
    name: 'Sierra Norte Outfitters',
    address: 'Av. Universidad 1001, Monterrey, Nuevo León',
    logoUrl: 'https://placehold.co/256x256/78350F/FFFFFF.png?text=SN',
  },
  {
    id: 'prov-tech',
    name: 'Pixel Supply',
    address: 'Av. Vallarta 3300, Guadalajara, Jalisco',
    logoUrl: 'https://placehold.co/256x256/1E3A8A/FFFFFF.png?text=PS',
  },
  {
    id: 'prov-home',
    name: 'Casa Brisa',
    address: 'Blvd. Atlixco 3156, Puebla, Puebla',
    logoUrl: 'https://placehold.co/256x256/0369A1/FFFFFF.png?text=CB',
  },
  {
    id: 'prov-gifts',
    name: 'Órbita Regalos',
    address: 'Calle República de Cuba 43, Ciudad de México',
    logoUrl: 'https://placehold.co/256x256/6D28D9/FFFFFF.png?text=OR',
  },
  {
    id: 'prov-style',
    name: 'Tiempo y Vista',
    address: 'Av. Patria 1891, Zapopan, Jalisco',
    logoUrl: 'https://placehold.co/256x256/111827/FFFFFF.png?text=TV',
  },
]

const categoryById = Object.fromEntries(MOCK_CATEGORIES.map((c) => [c.id, c]))
const providerById = Object.fromEntries(MOCK_PROVIDERS.map((p) => [p.id, p]))

export const MOCK_PRODUCTS: ProductDetailEntity[] = [
  {
    id: 'prod-shampoo-01',
    name: 'Shampoo Hidratación Coco 400 ml',
    description:
      'Shampoo hidratante de uso diario con aroma a coco para cabello seco; fórmula botánica sin sulfatos.',
    priceListCents: 18900,
    category: categoryById['cat-shampoo'],
    provider: providerById['prov-care'],
    media: [
      {
        id: 'media-shampoo-01',
        url: 'https://fitnessbeautyart.com/wp-content/uploads/2024/02/1bfa5f59thumbnail-682x1024.jpeg',
        productId: 'prod-shampoo-01',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-shampoo-03',
    name: 'Shampoo Reparación Keratina 500 ml',
    description:
      'Fórmula reparadora intensiva con keratina vegetal para cabello teñido o maltratado por calor.',
    priceListCents: 22900,
    category: categoryById['cat-shampoo'],
    provider: providerById['prov-care'],
    media: [
      {
        id: 'media-shampoo-03',
        url: 'https://developers.openai.com/cookbook/assets/images/extract_product_gpt-image-2.png',
        productId: 'prod-shampoo-03',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-boots-01',
    name: 'Botas Senderismo Roble',
    description:
      'Botas de senderismo color café con suela de alto agarre y soporte acolchado al tobillo.',
    priceListCents: 149900,
    category: categoryById['cat-boots'],
    provider: providerById['prov-outdoor'],
    media: [
      {
        id: 'media-boots-01',
        url: 'https://contents.mediadecathlon.com/p2904892/k%247e0c1b8961d34b51491cb8227b85eecb/picture.jpg',
        productId: 'prod-boots-01',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-boots-02',
    name: 'Botas Urbanas Chelsea Ébano',
    description:
      'Botas Chelsea negras con paneles elásticos laterales, corte limpio y suela antiderrapante.',
    priceListCents: 119900,
    category: categoryById['cat-boots'],
    provider: providerById['prov-outdoor'],
    media: [
      {
        id: 'media-boots-02',
        url: 'https://jans.com/cdn/shop/files/SOR00233_Tobacco-and-Black.02.jpg?v=1764449380&width=1080',
        productId: 'prod-boots-02',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-boots-05',
    name: 'Botas Lluvia Grafito',
    description:
      'Botas impermeables de media caña con acabado grafito mate y suela texturizada todo terreno.',
    priceListCents: 89900,
    category: categoryById['cat-boots'],
    provider: providerById['prov-outdoor'],
    media: [
      {
        id: 'media-boots-05',
        url: 'https://respect-shoes.ru/upload/iblock/4fe/9m58w5ou7293rgxaddzt9hbxxygc30of.JPG',
        productId: 'prod-boots-05',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-mouse-01',
    name: 'Mouse Inalámbrico Pulse M10',
    description:
      'Mouse inalámbrico compacto de 1600 DPI, receptor USB de baja latencia y autonomía de seis meses.',
    priceListCents: 34900,
    category: categoryById['cat-mice'],
    provider: providerById['prov-tech'],
    media: [
      {
        id: 'media-mouse-01',
        url: 'https://images.unsplash.com/photo-1707592691247-5c3a1c7ba0e3?auto=format&fit=crop&w=1000&q=85',
        productId: 'prod-mouse-01',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-mouse-02',
    name: 'Mouse Ergonómico Arc M20',
    description:
      'Mouse vertical ergonómico con seis botones programables y sensibilidad ajustable de hasta 2400 DPI.',
    priceListCents: 64900,
    category: categoryById['cat-mice'],
    provider: providerById['prov-tech'],
    media: [
      {
        id: 'media-mouse-02',
        url: 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=1000&q=85',
        productId: 'prod-mouse-02',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-fan-02',
    name: 'Ventilador de Pedestal Aire 16',
    description:
      'Ventilador de pedestal de 16 pulgadas con altura ajustable, cabezal oscilante y rejilla reforzada.',
    priceListCents: 109900,
    category: categoryById['cat-fans'],
    provider: providerById['prov-home'],
    media: [
      {
        id: 'media-fan-02',
        url: 'https://cdn.mos.cms.futurecdn.net/V7kXsBgjn37QdPFyFQXDgB.jpg',
        productId: 'prod-fan-02',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-fan-04',
    name: 'Ventilador Torre Boreal',
    description:
      'Ventilador tipo torre silencioso con oscilación de 75°, temporizador y tres modos de brisa.',
    priceListCents: 139900,
    category: categoryById['cat-fans'],
    provider: providerById['prov-home'],
    media: [
      {
        id: 'media-fan-04',
        url: 'https://fs.modenoffice.com/imgRoot/0001/shp/code/2024/09/M770549_500.jpg',
        productId: 'prod-fan-04',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-gift-01',
    name: 'Funko Pop Batman Classic',
    description:
      'Figura coleccionable estilo Funko Pop de Batman clásico con traje negro y cinturón amarillo.',
    priceListCents: 39900,
    category: categoryById['cat-gifts'],
    provider: providerById['prov-gifts'],
    media: [
      {
        id: 'media-gift-01',
        url: 'https://funko.com/on/demandware.static/-/Sites-funko-master-catalog/default/dwef747fbc/images/funko/11496-PX-1MA-1.png',
        productId: 'prod-gift-01',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-gift-03',
    name: 'Pato de Hule Clásico',
    description:
      'Pato de hule amarillo flotante con pico naranja, ideal para regalo o escritorio creativo.',
    priceListCents: 9900,
    category: categoryById['cat-gifts'],
    provider: providerById['prov-gifts'],
    media: [
      {
        id: 'media-gift-03',
        url: 'https://www.museumofplay.org/app/uploads/2021/08/rubber-duck-sq.jpg',
        productId: 'prod-gift-03',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-gift-06',
    name: 'Esfera Galaxia 3D 8 cm',
    description:
      'Esfera de cristal óptico de 8 cm con sistema estelar grabado en láser 3D y base de madera LED.',
    priceListCents: 59900,
    category: categoryById['cat-gifts'],
    provider: providerById['prov-gifts'],
    media: [
      {
        id: 'media-gift-06',
        url: 'https://acdn-us.mitiendanube.com/stores/003/229/070/products/d_nq_np_2x_947026-mla77029921814_062024-f-65dae4c8209f5dfba717328374889675-1024-1024.webp',
        productId: 'prod-gift-06',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-accessory-01',
    name: 'Lentes de Sol Noir',
    description:
      'Lentes de sol negros con armazón clásico de acetato, mica polarizada y protección UV400.',
    priceListCents: 54900,
    category: categoryById['cat-accessories'],
    provider: providerById['prov-style'],
    media: [
      {
        id: 'media-accessory-01',
        url: 'https://cdn.dummyjson.com/product-images/sunglasses/black-sun-glasses/thumbnail.webp',
        productId: 'prod-accessory-01',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-accessory-03',
    name: 'Reloj Analógico Heritage',
    description:
      'Reloj analógico con carátula blanca minimalista, caja de acero cepillado y correa de piel café.',
    priceListCents: 149900,
    category: categoryById['cat-accessories'],
    provider: providerById['prov-style'],
    media: [
      {
        id: 'media-accessory-03',
        url: 'https://cdn.dummyjson.com/product-images/mens-watches/brown-leather-belt-watch/thumbnail.webp',
        productId: 'prod-accessory-03',
        isMain: true,
      },
    ],
  },
  {
    id: 'prod-accessory-04',
    name: 'Reloj Acero Meridian',
    description:
      'Reloj analógico de acero inoxidable con carátula azul profundo y resistencia al agua de 5 ATM.',
    priceListCents: 219900,
    category: categoryById['cat-accessories'],
    provider: providerById['prov-style'],
    media: [
      {
        id: 'media-accessory-04',
        url: 'https://cdn.dummyjson.com/product-images/womens-watches/iwc-ingenieur-automatic-steel/thumbnail.webp',
        productId: 'prod-accessory-04',
        isMain: true,
      },
    ],
  },
]

export const INITIAL_CART_ITEMS: CartItemEntity[] = [
  {
    product: MOCK_PRODUCTS[0], // Shampoo Hidratación Coco
    quantity: 2,
  },
  {
    product: MOCK_PRODUCTS[6], // Mouse Ergonómico Arc M20
    quantity: 1,
  },
]

export const INITIAL_SALES_HISTORY: SaleEntity[] = [
  {
    id: 'vta-2026-0842',
    createdAt: '2026-10-19T17:42:10-06:00',
    items: [
      {
        product: MOCK_PRODUCTS[2], // Botas Senderismo Roble
        quantity: 1,
      },
      {
        product: MOCK_PRODUCTS[10], // Pato de Hule Clásico
        quantity: 2,
      },
    ],
  },
  {
    id: 'vta-2026-0791',
    createdAt: '2026-10-15T13:18:00-06:00',
    items: [
      {
        product: MOCK_PRODUCTS[12], // Lentes de Sol Noir
        quantity: 1,
      },
      {
        product: MOCK_PRODUCTS[11], // Esfera Galaxia 3D 8 cm
        quantity: 1,
      },
    ],
  },
]

export const INITIAL_AGENT_MESSAGES: AgentTranscriptMessageEntity[] = [
  {
    id: 'msg-welcome-1',
    speaker: 'agent',
    text: '¡Hola! ¿En qué puedo ayudarte hoy? Puedo buscar productos de la tienda, mostrarte precios o agregar artículos a tu carrito.',
    final: true,
    timestamp: '12:00',
  },
  {
    id: 'msg-user-2',
    speaker: 'user',
    text: '¿Tienes algún mouse ergonómico y shampoo sin sulfatos?',
    final: true,
    timestamp: '12:01',
  },
  {
    id: 'msg-agent-3',
    speaker: 'agent',
    text: 'Claro. Agregué el Shampoo Hidratación Coco (2 pzas) y el Mouse Ergonómico Arc M20 a tu carrito de compras.',
    final: true,
    timestamp: '12:01',
  },
]
