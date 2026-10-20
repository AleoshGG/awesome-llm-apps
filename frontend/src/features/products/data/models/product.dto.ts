import type { ProviderDto } from '../../../providers/data/models/provider.dto'

export interface CategoryDto {
  id: string
  name: string
}

export interface ProductMediaDto {
  id: string
  url: string
  productId: string
  isMain: boolean
}

export interface ProductDetailDto {
  id: string
  name: string
  description: string
  priceListCents: number
  category: CategoryDto
  provider: ProviderDto
  media: ProductMediaDto[]
}

export interface ProductQueryInputDto {
  name?: string | null
  description?: string | null
  categoryName?: string | null
  providerName?: string | null
  minPriceCents?: number | null
  maxPriceCents?: number | null
}
