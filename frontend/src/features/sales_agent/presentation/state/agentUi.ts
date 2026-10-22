import type { ProductDetailEntity } from '../../../products/domain/entities/productDetail.entity'
import type { CartItemEntity } from '../../../sales/domain/entities/cartItem.entity'
import type { SaleEntity } from '../../../sales/domain/entities/sale.entity'
import type { AgentTranscriptMessageEntity } from '../../domain/entities/salesAgent.entity'
import type { UiCommand } from './salesAgentState'

type View = 'home' | 'cart' | 'purchases'

const STOPWORDS = new Set([
  'para', 'con', 'del', 'las', 'los', 'una', 'uno', 'unos', 'unas', 'por', 'sin', 'uso', 'tipo', 'color', 'talla',
  'opcion', 'opciones', 'producto', 'productos', 'hablame', 'cuentame', 'dime', 'sobre', 'otro', 'otra',
])

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' ? value as Record<string, unknown> : null
}

function text(value: unknown): string { return typeof value === 'string' ? value : '' }

function normalizeText(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function tokensOf(value: string): string[] {
  return normalizeText(value)
    .split(' ')
    .filter((token) => token.length >= 3 && !STOPWORDS.has(token))
}

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

export function cartFromCommand(command: UiCommand): CartItemEntity[] | null {
  if (command.action !== 'cart_update' || !Array.isArray(command.payload.cart)) return null
  return command.payload.cart.map((value) => {
    const item = record(value)
    const product = productFromAgent(item?.product)
    return product && typeof item?.quantity === 'number' ? { product, quantity: item.quantity } : null
  }).filter((item): item is CartItemEntity => item !== null)
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

export function matchProductInText(content: string, products: ProductDetailEntity[]): ProductDetailEntity | null {
  const normalizedContent = normalizeText(content)
  if (!normalizedContent || products.length === 0) return null

  const exactMatches = products
    .map((product) => ({ product, index: normalizedContent.indexOf(normalizeText(product.name)) }))
    .filter((entry) => entry.index >= 0)
    .sort((a, b) => a.index - b.index)
  if (exactMatches.length === 1) return exactMatches[0].product

  const productTokens = products.map((product) => ({
    product,
    tokens: tokensOf(product.name),
  }))
  const tokenFrequency = new Map<string, number>()
  for (const { tokens } of productTokens) {
    for (const token of new Set(tokens)) {
      tokenFrequency.set(token, (tokenFrequency.get(token) ?? 0) + 1)
    }
  }

  const contentWords = new Set(normalizedContent.split(' '))
  let bestProduct: ProductDetailEntity | null = null
  let bestScore = 0
  let bestFirstPos = Number.MAX_SAFE_INTEGER

  for (const { product, tokens } of productTokens) {
    let score = 0
    let distinctiveMatches = 0
    let firstPos = Number.MAX_SAFE_INTEGER
    for (const token of tokens) {
      if (contentWords.has(token) || normalizedContent.includes(token)) {
        const isDistinctive = (tokenFrequency.get(token) ?? 0) < products.length
        score += isDistinctive ? 3 : 1
        if (isDistinctive) distinctiveMatches += 1
        const pos = normalizedContent.indexOf(token)
        if (pos >= 0 && pos < firstPos) firstPos = pos
      }
    }
    if ((distinctiveMatches > 0 || (products.length === 1 && score > 0)) &&
        (score > bestScore || (score === bestScore && firstPos < bestFirstPos))) {
      bestScore = score
      bestFirstPos = firstPos
      bestProduct = product
    }
  }

  if (bestProduct) return bestProduct
  return exactMatches[0]?.product ?? null
}

function matchProductByOrdinal(content: string, products: ProductDetailEntity[]): ProductDetailEntity | null {
  const normalized = normalizeText(content)
  if (!normalized || products.length < 2) return null
  if (/\b(tercera|tercero|tercer|opcion 3|numero 3)\b/.test(normalized) && products[2]) {
    return products[2]
  }
  if (/\b(segunda|segundo|opcion 2|numero 2|otra opcion|la otra|el otro|otro modelo|otra alternativa)\b/.test(normalized)) {
    return products[1]
  }
  if (/\b(primera|primero|primer|opcion 1|numero 1)\b/.test(normalized)) {
    return products[0]
  }
  return null
}

export function featuredProductForChat(
  agentProduct: ProductDetailEntity | null,
  agentProducts: ProductDetailEntity[] | null,
  messages: AgentTranscriptMessageEntity[],
  searchMessageIndex = 0,
  isCrossSell = false,
): ProductDetailEntity | null {
  const candidates = agentProducts ?? []
  const recentMessages = messages.slice(Math.max(0, searchMessageIndex))

  if (isCrossSell) {
    if (agentProduct) return agentProduct
    for (let i = recentMessages.length - 1; i >= 0; i -= 1) {
      if (recentMessages[i].speaker === 'agent') {
        const matched = matchProductInText(recentMessages[i].text, candidates)
        if (matched) return matched
      }
    }
    return candidates[0] ?? null
  }

  const firstUserFollowUpIndex = recentMessages.findIndex((msg) => msg.speaker === 'user')
  if (firstUserFollowUpIndex >= 0 && candidates.length > 0) {
    const followUpMessages = recentMessages.slice(firstUserFollowUpIndex)
    for (let i = followUpMessages.length - 1; i >= 0; i -= 1) {
      const msg = followUpMessages[i]
      const matchedByName = matchProductInText(msg.text, candidates)
      if (matchedByName) return matchedByName
      if (msg.speaker === 'user') {
        const matchedOrdinal = matchProductByOrdinal(msg.text, candidates)
        if (matchedOrdinal) return matchedOrdinal
      }
    }
  }

  return agentProduct ?? candidates[0] ?? null
}

export function navigationForCommand(command: UiCommand): View | null {
  if (command.action === 'catalog_search' || command.action === 'catalog_product') {
    return command.payload.cross_sell === true ? null : 'home'
  }
  if (command.action === 'cart_update') return 'cart'
  if (command.action === 'checkout') return command.phase === 'done' ? 'purchases' : 'cart'
  return null
}
