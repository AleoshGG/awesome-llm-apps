import type { ProductDetailDto } from '../../../products/data/models/product.dto'

export interface CartItemDto {
  product: ProductDetailDto
  quantity: number
}

export interface SaleItemDto {
  product: ProductDetailDto
  quantity: number
}

export interface SaleDto {
  id: string
  createdAt: string
  items: SaleItemDto[]
}
