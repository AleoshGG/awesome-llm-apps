import { Button, Spinner } from '@heroui/react'
import type { ProductDetailEntity } from '../../../products/domain/entities/productDetail.entity'
import type { CartItemEntity } from '../../domain/entities/cartItem.entity'
import type { SaleEntity } from '../../domain/entities/sale.entity'
import { CartItemList } from '../components/CartItemList'
import { CheckoutSuccessBanner } from '../components/CheckoutSuccessBanner'
import { OrderSummaryCard } from '../components/OrderSummaryCard'
import type { CheckoutStep } from '../hooks/useCartPresentation'

interface CartPageProps {
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
  onIncrementItem: (product: ProductDetailEntity) => void
  onDecrementItem: (productId: string) => void
  onRemoveItem: (productId: string) => void
  onClearCart: () => void
  onSetCheckoutStep: (step: CheckoutStep) => void
  onConfirmPurchase: () => void
  onRefreshCart: () => void
  onNavigateToStore: () => void
  onNavigateToPurchases: () => void
}

export function CartPage({
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
  onIncrementItem,
  onDecrementItem,
  onRemoveItem,
  onClearCart,
  onSetCheckoutStep,
  onConfirmPurchase,
  onRefreshCart,
  onNavigateToStore,
  onNavigateToPurchases,
}: CartPageProps) {
  if (checkoutStep === 'completed' && lastCompletedSale) {
    return (
      <div className="py-4">
        <CheckoutSuccessBanner
          sale={lastCompletedSale}
          onViewPurchases={onNavigateToPurchases}
          onBackToStore={() => {
            onSetCheckoutStep('review')
            onNavigateToStore()
          }}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4 rounded-2xl border border-blue-100 bg-white p-5 shadow-2xs">
        <div>
          <h1 className="font-display text-2xl font-extrabold text-slate-900">
            Carrito de compras
          </h1>
          <p className="text-xs sm:text-sm text-slate-500">
            Revisa tus productos seleccionados y confirma tu pedido.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button size="sm" variant="secondary" onPress={onNavigateToStore}>
            Seguir comprando
          </Button>
          {items.length > 0 && (
            <Button
              size="sm"
              variant="ghost"
              isDisabled={isSubmitting}
              onPress={onClearCart}
            >
              Vaciar bolsa
            </Button>
          )}
        </div>
      </header>

      {error && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-blue-200 bg-blue-50/70 px-4 py-3 text-xs text-blue-950">
          <span>{error}</span>
          <Button size="sm" variant="secondary" onPress={onRefreshCart}>
            Actualizar carrito
          </Button>
        </div>
      )}

      {isLoading ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-blue-100 bg-white py-16 text-center">
          <Spinner size="md" />
          <p className="text-xs font-medium text-slate-500">
            Cargando tu bolsa de compra...
          </p>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-12 lg:items-start">
          <div className="lg:col-span-8">
            <CartItemList
              items={items}
              onIncrement={onIncrementItem}
              onDecrement={onDecrementItem}
              onRemove={onRemoveItem}
              onContinueShopping={onNavigateToStore}
            />
          </div>

          <aside className="lg:col-span-4">
            <OrderSummaryCard
              totalItemsCount={totalItemsCount}
              subtotalCents={subtotalCents}
              shippingCents={shippingCents}
              totalCents={totalCents}
              checkoutStep={checkoutStep}
              isSubmitting={isSubmitting}
              onRequestConfirm={() => onSetCheckoutStep('confirm')}
              onCancelConfirm={() => onSetCheckoutStep('review')}
              onConfirmPurchase={onConfirmPurchase}
            />
          </aside>
        </div>
      )}
    </div>
  )
}
