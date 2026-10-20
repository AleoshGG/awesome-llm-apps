import { Button, Card, Chip, Separator } from '@heroui/react'
import { formatCentsToMXN } from '../../../../core/utils/formatters'
import type { CheckoutStep } from '../hooks/useCartPresentation'

interface OrderSummaryCardProps {
  totalItemsCount: number
  subtotalCents: number
  shippingCents: number
  totalCents: number
  checkoutStep: CheckoutStep
  isSubmitting?: boolean
  onRequestConfirm: () => void
  onCancelConfirm: () => void
  onConfirmPurchase: () => void
}

export function OrderSummaryCard({
  totalItemsCount,
  subtotalCents,
  shippingCents,
  totalCents,
  checkoutStep,
  isSubmitting = false,
  onRequestConfirm,
  onCancelConfirm,
  onConfirmPurchase,
}: OrderSummaryCardProps) {
  const isDisabled = totalItemsCount === 0 || isSubmitting

  return (
    <Card className="sticky top-22 rounded-2xl border border-blue-100 bg-white shadow-2xs">
      <Card.Header className="flex flex-col items-start gap-1">
        <div className="flex w-full items-center justify-between">
          <Card.Title className="font-display text-lg font-bold text-slate-900">
            Tu bolsa de compra
          </Card.Title>
          <Chip size="sm" color="accent" variant="soft">
            <Chip.Label>{totalItemsCount} pzas</Chip.Label>
          </Chip>
        </div>
        <Card.Description className="text-xs text-slate-500">
          Resumen de tu pedido
        </Card.Description>
      </Card.Header>

      <Separator />

      <Card.Content className="space-y-3 py-4 text-sm">
        <div className="flex items-center justify-between text-slate-600">
          <span>Productos ({totalItemsCount})</span>
          <span className="font-medium text-slate-900 tabular-price">
            {formatCentsToMXN(subtotalCents)}
          </span>
        </div>

        <div className="flex items-center justify-between text-slate-600">
          <span>Envío estándar</span>
          <span className="font-medium text-blue-700 tabular-price">
            {shippingCents === 0 ? 'Gratis' : formatCentsToMXN(shippingCents)}
          </span>
        </div>

        <Separator />

        <div className="flex items-baseline justify-between pt-1">
          <span className="font-display text-sm font-bold text-slate-900">
            Total a pagar
          </span>
          <span className="font-display text-xl font-extrabold text-slate-900 tabular-price">
            {formatCentsToMXN(totalCents)}
          </span>
        </div>

        {checkoutStep === 'confirm' && (
          <div className="rounded-xl border border-blue-200 bg-blue-50/80 p-3 text-xs text-blue-950 space-y-1">
            <p className="font-semibold">¿Confirmar tu pedido?</p>
            <p className="text-[11px] text-blue-800 leading-relaxed">
              Al confirmar, registraremos tu compra y podrás consultarla en la
              sección Mis compras.
            </p>
          </div>
        )}
      </Card.Content>

      <Separator />

      <Card.Footer className="flex flex-col gap-2.5 pt-3">
        {checkoutStep === 'review' ? (
          <Button
            fullWidth
            variant="primary"
            isDisabled={isDisabled}
            onPress={onRequestConfirm}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold"
          >
            Continuar con la compra
          </Button>
        ) : (
          <div className="flex w-full flex-col gap-2">
            <Button
              fullWidth
              variant="primary"
              isDisabled={isDisabled}
              onPress={onConfirmPurchase}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold"
            >
              {isSubmitting ? 'Procesando compra...' : 'Confirmar compra'}
            </Button>
            <Button
              fullWidth
              variant="ghost"
              size="sm"
              isDisabled={isSubmitting}
              onPress={onCancelConfirm}
            >
              Modificar carrito
            </Button>
          </div>
        )}
      </Card.Footer>
    </Card>
  )
}
