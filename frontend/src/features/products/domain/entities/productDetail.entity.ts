import type { ProviderEntity } from '../../../providers/domain/entities/provider.entity'
import type { CategoryEntity } from './category.entity'
import type { ProductMediaEntity } from './productMedia.entity'

/**
 * Entidad pura de dominio con el detalle completo de un producto del catálogo.
 * `priceListCents` se expresa en centavos de MXN (enteros).
 */
export interface ProductDetailEntity {
  id: string
  name: string
  description: string
  priceListCents: number
  category: CategoryEntity
  provider: ProviderEntity
  media: ProductMediaEntity[]
}
