import { Button, Card, Chip, Separator } from '@heroui/react'
import { formatCentsToMXN, formatIsoDate } from '../../../../core/utils/formatters'
import type { SaleEntity } from '../../domain/entities/sale.entity'

interface CheckoutSuccessBannerProps {
  sale: SaleEntity
  onViewPurchases: () => void
  onBackToStore: () => void
}

export function CheckoutSuccessBanner({
  sale,
  onViewPurchases,
  onBackToStore,
}: CheckoutSuccessBannerProps) {
  const totalCents = sale.items.reduce(
    (sum, item) => sum + item.product.priceListCents * item.quantity,
    0,
  )

  return (
    <Card className="mx-auto max-w-2xl rounded-3xl border border-blue-200 bg-white p-6 sm:p-8 shadow-2xs">
      <Card.Header className="flex flex-col items-start gap-2">
        <Chip color="accent" variant="soft" size="sm">
          <Chip.Label>Compra realizada</Chip.Label>
        </Chip>

        <Card.Title className="font-display text-2xl font-extrabold text-slate-900">
          ¡Gracias por tu compra!
        </Card.Title>
        <Card.Description className="text-xs sm:text-sm text-slate-600">
          Pedido registrado el {formatIsoDate(sale.createdAt)}. Puedes revisar
          los detalles en cualquier momento desde Mis compras.
        </Card.Description>
      </Card.Header>

      <Separator className="my-4" />

      <Card.Content className="space-y-3">
        <h3 className="text-xs font-semibold text-slate-500">
          Artículos adquiridos
        </h3>

        <ul className="space-y-2">
          {sale.items.map((item) => (
            <li
              key={item.product.id}
              className="flex items-center justify-between rounded-xl bg-slate-50 px-3.5 py-2.5 text-xs"
            >
              <div>
                <span className="font-semibold text-slate-900">
                  {item.product.name}
                </span>
                <span className="ml-2 text-slate-500">× {item.quantity}</span>
              </div>
              <span className="font-semibold text-slate-900 tabular-price">
                {formatCentsToMXN(item.product.priceListCents * item.quantity)}
              </span>
            </li>
          ))}
        </ul>

        <div className="flex items-center justify-between rounded-xl border border-blue-100 bg-blue-50/60 px-4 py-3">
          <span className="text-xs font-semibold text-blue-950">
            Total pagado
          </span>
          <span className="font-display text-lg font-extrabold text-blue-900 tabular-price">
            {formatCentsToMXN(totalCents)}
          </span>
        </div>
      </Card.Content>

      <Card.Footer className="mt-4 flex flex-wrap items-center justify-end gap-3">
        <Button variant="secondary" onPress={onBackToStore}>
          Seguir comprando
        </Button>
        <Button
          variant="primary"
          onPress={onViewPurchases}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          Ir a Mis compras
        </Button>
      </Card.Footer>
    </Card>
  )
}
