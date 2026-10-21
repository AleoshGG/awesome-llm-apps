/**
 * Entidad de criterios de búsqueda y filtrado de productos.
 */
export interface ProductQueryEntity {
  name?: string | null
  description?: string | null
  categoryName?: string | null
  providerName?: string | null
  minPriceCents?: number | null
  maxPriceCents?: number | null
  limit?: number | null
  offset?: number | null
}
