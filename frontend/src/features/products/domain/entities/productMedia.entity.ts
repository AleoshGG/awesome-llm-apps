/**
 * Entidad pura de dominio para recursos multimedia (imágenes) de un producto.
 */
export interface ProductMediaEntity {
  id: string
  url: string
  productId: string
  isMain: boolean
}
