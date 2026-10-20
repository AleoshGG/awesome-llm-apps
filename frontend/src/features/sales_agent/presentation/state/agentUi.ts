import type { ProductDetailEntity } from '../../../products/domain/entities/productDetail.entity'
import type { SaleEntity } from '../../../sales/domain/entities/sale.entity'
import type { UiCommand } from './salesAgentState'

type View = 'home' | 'cart' | 'purchases'

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' ? value as Record<string, unknown> : null
}

function text(value: unknown): string { return typeof value === 'string' ? value : '' }

export function productFromAgent(value: unknown): ProductDetailEntity | null {
  const item = record(value)
  const category = record(item?.category)
  const provider = record(item?.provider)
  const media = Array.isArray(item?.media) ? item.media.map(record).filter((entry): entry is Record<string, unknown> => entry !== null) : []
  const price = item?.price_list_cents ?? item?.priceListCents
  if (!item || !text(item.id) || !text(item.name) || typeof price !== 'number' || !category || !provider) return null
  return {
    id: text(item.id), name: text(item.name), description: text(item.description), priceListCents: price,
    category: { id: text(category.id), name: text(category.name) },
    provider: { id: text(provider.id), name: text(provider.name), address: text(provider.address),
      logoUrl: text(provider.logo_url ?? provider.logoUrl) },
    media: media.map((image) => ({ id: text(image.id), url: text(image.url),
      productId: text(image.product_id ?? image.productId), isMain: Boolean(image.is_main ?? image.isMain) })),
  }
}

export function productsFromCommand(command: UiCommand): ProductDetailEntity[] {
  if (command.action !== 'catalog_search' || !Array.isArray(command.payload.products)) return []
  return command.payload.products.map(productFromAgent).filter((item): item is ProductDetailEntity => item !== null)
}

export function saleFromCommand(command: UiCommand): SaleEntity | null {
  const sale = record(command.payload.sale)
  if (!sale || !text(sale.id) || !Array.isArray(sale.items)) return null
  const items = sale.items.map((value) => {
    const item = record(value)
    const product = productFromAgent(item?.product)
    return product && typeof item?.quantity === 'number' ? { product, quantity: item.quantity } : null
  }).filter((item): item is NonNullable<typeof item> => item !== null)
  return { id: text(sale.id), createdAt: text(sale.created_at ?? sale.createdAt), items }
}

export function navigationForCommand(command: UiCommand): View | null {
  if (command.action === 'catalog_search' || command.action === 'catalog_product') return 'home'
  if (command.action === 'cart_update') return 'cart'
  if (command.action === 'checkout') return command.phase === 'done' ? 'purchases' : 'cart'
  return null
}
