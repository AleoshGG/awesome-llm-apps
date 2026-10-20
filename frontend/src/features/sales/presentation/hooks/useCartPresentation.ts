import { useEffect, useMemo, useState } from 'react'
import { useCases } from '../../../../core/di/useCasesContainer'
import type { ProductDetailEntity } from '../../../products/domain/entities/productDetail.entity'
import type { CartItemEntity } from '../../domain/entities/cartItem.entity'
import type { SaleEntity } from '../../domain/entities/sale.entity'

export type CheckoutStep = 'review' | 'confirm' | 'completed'

export interface UseCartPresentationReturn {
  items: CartItemEntity[]
  isLoading: boolean
  isSubmitting: boolean
  error: string | null
  totalItemsCount: number
  subtotalCents: number
  shippingCents: number
  totalCents: number
  checkoutStep: CheckoutStep
  lastCompletedSale: SaleEntity | null
  getProductQuantity: (productId: string) => number
  addItem: (product: ProductDetailEntity, quantity?: number) => void
  decrementItem: (productId: string) => void
  removeItem: (productId: string) => void
  clearCart: () => void
  setCheckoutStep: (step: CheckoutStep) => void
  completePurchase: (onSaleCreated?: (sale: SaleEntity) => void) => void
  refreshCart: () => void
}

/**
 * Hook de gestión de estado para la pantalla Carrito de Compras y Checkout.
 * Conecta con GraphQL `cart`, `addProductToCart`, `removeProductFromCart` y `registerSale`.
 */
export function useCartPresentation(): UseCartPresentationReturn {
  const [items, setItems] = useState<CartItemEntity[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [checkoutStep, setCheckoutStep] = useState<CheckoutStep>('review')
  const [lastCompletedSale, setLastCompletedSale] =
    useState<SaleEntity | null>(null)
  const [reloadTick, setReloadTick] = useState<number>(0)

  useEffect(() => {
    let active = true

    void useCases.sales.getCart
      .execute()
      .then((cartItems) => {
        if (!active) return
        setItems(cartItems)
        setError(null)
        setIsLoading(false)
      })
      .catch((err: unknown) => {
        if (!active) return
        setError(
          err instanceof Error
            ? err.message
            : 'No fue posible cargar tu carrito de compras.',
        )
        setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadTick])

  const totalItemsCount = useMemo(
    () => items.reduce((sum, item) => sum + item.quantity, 0),
    [items],
  )

  const subtotalCents = useMemo(
    () =>
      items.reduce(
        (sum, item) => sum + item.product.priceListCents * item.quantity,
        0,
      ),
    [items],
  )

  const shippingCents = 0
  const totalCents = subtotalCents + shippingCents

  const getProductQuantity = (productId: string): number => {
    const found = items.find((item) => item.product.id === productId)
    return found ? found.quantity : 0
  }

  const addItem = (product: ProductDetailEntity, quantity = 1) => {
    setCheckoutStep('review')
    setError(null)
    setIsSubmitting(true)

    void useCases.sales.addProductToCart
      .execute(product.id, quantity)
      .then((updatedCart) => {
        setItems(updatedCart)
      })
      .catch((err: unknown) => {
        setError(
          err instanceof Error
            ? err.message
            : 'No se pudo agregar el producto al carrito.',
        )
      })
      .finally(() => {
        setIsSubmitting(false)
      })
  }

  const decrementItem = (productId: string) => {
    const currentItem = items.find((item) => item.product.id === productId)
    if (!currentItem) return

    setError(null)
    setIsSubmitting(true)

    const targetQty = currentItem.quantity - 1

    const operation =
      targetQty <= 0
        ? useCases.sales.removeProductFromCart.execute(productId)
        : useCases.sales.removeProductFromCart
            .execute(productId)
            .then(() =>
              useCases.sales.addProductToCart.execute(productId, targetQty),
            )

    void operation
      .then((updatedCart) => {
        setItems(updatedCart)
      })
      .catch((err: unknown) => {
        setError(
          err instanceof Error
            ? err.message
            : 'No se pudo actualizar la cantidad del producto.',
        )
      })
      .finally(() => {
        setIsSubmitting(false)
      })
  }

  const removeItem = (productId: string) => {
    setError(null)
    setIsSubmitting(true)

    void useCases.sales.removeProductFromCart
      .execute(productId)
      .then((updatedCart) => {
        setItems(updatedCart)
      })
      .catch((err: unknown) => {
        setError(
          err instanceof Error
            ? err.message
            : 'No se pudo quitar el producto del carrito.',
        )
      })
      .finally(() => {
        setIsSubmitting(false)
      })
  }

  const clearCart = () => {
    if (items.length === 0) return

    setError(null)
    setIsSubmitting(true)

    const productIds = items.map((item) => item.product.id)

    void (async () => {
      let latestCart: CartItemEntity[] = items
      for (const productId of productIds) {
        latestCart =
          await useCases.sales.removeProductFromCart.execute(productId)
      }
      return latestCart
    })()
      .then((updatedCart) => {
        setItems(updatedCart)
        setCheckoutStep('review')
      })
      .catch((err: unknown) => {
        setError(
          err instanceof Error
            ? err.message
            : 'No se pudo vaciar la bolsa de compra.',
        )
      })
      .finally(() => {
        setIsSubmitting(false)
      })
  }

  const completePurchase = (onSaleCreated?: (sale: SaleEntity) => void) => {
    if (items.length === 0 || isSubmitting) return

    setError(null)
    setIsSubmitting(true)

    void useCases.sales.registerSale
      .execute()
      .then((registeredSale) => {
        setLastCompletedSale(registeredSale)
        setItems([])
        setCheckoutStep('completed')
        onSaleCreated?.(registeredSale)
      })
      .catch((err: unknown) => {
        setError(
          err instanceof Error
            ? err.message
            : 'No fue posible registrar tu compra.',
        )
      })
      .finally(() => {
        setIsSubmitting(false)
      })
  }

  const refreshCart = () => {
    setIsLoading(true)
    setError(null)
    setReloadTick((prev) => prev + 1)
  }

  return {
    items,
    isLoading,
    isSubmitting,
    error,
    totalItemsCount,
    subtotalCents,
    shippingCents,
    totalCents,
    checkoutStep,
    lastCompletedSale,
    getProductQuantity,
    addItem,
    decrementItem,
    removeItem,
    clearCart,
    setCheckoutStep,
    completePurchase,
    refreshCart,
  }
}
