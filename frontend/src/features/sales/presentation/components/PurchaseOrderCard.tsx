import { Button, Card, Chip, Separator } from '@heroui/react'
import { formatCentsToMXN, formatIsoDate } from '../../../../core/utils/formatters'
import type { ProductDetailEntity } from '../../../products/domain/entities/productDetail.entity'
import type { SaleEntity } from '../../domain/entities/sale.entity'

interface PurchaseOrderCardProps {
  sale: SaleEntity
  isExpanded: boolean
  onToggleExpand: (saleId: string) => void
  onReorderProduct: (product: ProductDetailEntity, quantity: number) => void
  isHighlighted?: boolean
}

export function PurchaseOrderCard({
  sale,
  isExpanded,
  onToggleExpand,
  onReorderProduct,
  isHighlighted = false,
}: PurchaseOrderCardProps) {
  const totalPieces = sale.items.reduce((sum, item) => sum + item.quantity, 0)
  const totalAmountCents = sale.items.reduce(
    (sum, item) => sum + item.product.priceListCents * item.quantity,
    0,
  )

  return (
    <Card className={`rounded-2xl border border-blue-100 bg-white shadow-2xs overflow-hidden ${isHighlighted ? 'agent-result-highlight' : ''}`}>
      <Card.Header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between px-5 py-4">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <Chip size="sm" color="accent" variant="soft">
              <Chip.Label>Compra completada</Chip.Label>
            </Chip>
            <span className="text-xs font-medium text-slate-600">
              {formatIsoDate(sale.createdAt)}
            </span>
          </div>
          <p className="text-xs text-slate-600">
            {totalPieces} {totalPieces === 1 ? 'artículo' : 'artículos'} ·{' '}
            {sale.items.map((i) => i.product.name).join(', ')}
          </p>
        </div>

        <div className="flex items-center justify-between sm:justify-end gap-4">
          <div className="text-left sm:text-right">
            <span className="block text-[10px] text-slate-400">
              Importe total
            </span>
            <span className="font-display text-base font-extrabold text-slate-900 tabular-price">
              {formatCentsToMXN(totalAmountCents)}
            </span>
          </div>

          <Button
            size="sm"
            variant="secondary"
            onPress={() => onToggleExpand(sale.id)}
          >
            {isExpanded ? 'Ocultar productos' : 'Ver productos'}
          </Button>
        </div>
      </Card.Header>

      {isExpanded && (
        <>
          <Separator />
          <Card.Content className="bg-blue-50/30 px-5 py-4 space-y-3">
            <ul className="divide-y divide-blue-100/80">
              {sale.items.map((item) => {
                const mainImg =
                  item.product.media.find((m) => m.isMain)?.url ??
                  item.product.media[0]?.url

                return (
                  <li
                    key={item.product.id}
                    className="flex flex-col gap-3 py-3 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-slate-200 bg-white p-1">
                        {mainImg ? (
                          <img
                            src={mainImg}
                            alt={item.product.name}
                            className="max-h-full max-w-full object-contain object-center"
                          />
                        ) : null}
                      </div>
                      <div>
                        <p className="text-xs font-bold text-slate-900">
                          {item.product.name}
                        </p>
                        <p className="text-[11px] text-slate-500 tabular-price">
                          {item.product.provider.name} · {item.quantity} ×{' '}
                          {formatCentsToMXN(item.product.priceListCents)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between sm:justify-end gap-3">
                      <span className="text-xs font-bold text-slate-900 tabular-price">
                        {formatCentsToMXN(
                          item.product.priceListCents * item.quantity,
                        )}
                      </span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onPress={() =>
                          onReorderProduct(item.product, item.quantity)
                        }
                        className="text-blue-700 hover:bg-blue-100/60"
                      >
                        Comprar de nuevo
                      </Button>
                    </div>
                  </li>
                )
              })}
            </ul>
          </Card.Content>
        </>
      )}
    </Card>
  )
}
