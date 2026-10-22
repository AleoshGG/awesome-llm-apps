import type { CartItemEntity } from '../entities/cartItem.entity'

export interface CartRepository {
  getCart(): Promise<CartItemEntity[]>
  addProduct(productId: string, quantity?: number): Promise<CartItemEntity[]>
  removeProduct(productId: string): Promise<CartItemEntity[]>
  clearCart(): Promise<CartItemEntity[]>
}
