import { Button, Card, Chip } from '@heroui/react'
import { formatCentsToMXN } from '../../../../core/utils/formatters'
import type { ProductDetailEntity } from '../../../products/domain/entities/productDetail.entity'
import type { CartItemEntity } from '../../domain/entities/cartItem.entity'

interface CartItemListProps {
  items: CartItemEntity[]
  onIncrement: (product: ProductDetailEntity) => void
  onDecrement: (productId: string) => void
  onRemove: (productId: string) => void
  onContinueShopping: () => void
}

export function CartItemList({
  items,
  onIncrement,
  onDecrement,
  onRemove,
  onContinueShopping,
}: CartItemListProps) {
  if (items.length === 0) {
    return (
      <Card className="rounded-2xl border border-blue-100 bg-white p-8 text-center">
        <Card.Header className="flex flex-col items-center gap-2">
          <Chip size="sm" color="accent" variant="soft">
            <Chip.Label>Bolsa vacía</Chip.Label>
          </Chip>
          <Card.Title className="font-display text-xl font-bold text-slate-900">
            Aún no tienes artículos en tu bolsa de compra
          </Card.Title>
          <Card.Description className="max-w-md text-xs sm:text-sm text-slate-500">
            Explora el catálogo de la tienda para agregar los productos que te
            interesen.
          </Card.Description>
        </Card.Header>
        <Card.Footer className="flex justify-center pt-4">
          <Button
            variant="primary"
            onPress={onContinueShopping}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Ir a la tienda
          </Button>
        </Card.Footer>
      </Card>
    )
  }

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const mainImage =
          item.product.media.find((m) => m.isMain)?.url ??
          item.product.media[0]?.url
        const lineTotalCents = item.product.priceListCents * item.quantity

        return (
          <Card
            key={item.product.id}
            className="rounded-2xl border border-blue-100 bg-white p-4 shadow-2xs"
          >
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-start gap-3.5">
                <div className="h-20 w-20 shrink-0 overflow-hidden rounded-xl bg-slate-100 border border-slate-200/60">
                  {mainImage ? (
                    <img
                      src={mainImage}
                      alt={item.product.name}
                      className="h-full w-full object-cover object-center"
                    />
                  ) : null}
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-medium text-blue-700">
                    {item.product.provider.name}
                  </span>

                  <h3 className="font-display text-sm sm:text-base font-bold text-slate-900">
                    {item.product.name}
                  </h3>

                  <p className="text-xs text-slate-500 tabular-price">
                    Precio unitario:{' '}
                    <span className="font-medium text-slate-700">
                      {formatCentsToMXN(item.product.priceListCents)}
                    </span>
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between gap-4 border-t border-slate-100 pt-3 sm:border-t-0 sm:pt-0">
                <div className="flex items-center gap-1.5 rounded-xl border border-blue-100 bg-blue-50/40 p-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    isIconOnly
                    aria-label={`Disminuir cantidad de ${item.product.name}`}
                    onPress={() => onDecrement(item.product.id)}
                  >
                    −
                  </Button>
                  <span className="min-w-7 text-center text-xs font-bold text-slate-900 tabular-price">
                    {item.quantity}
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    isIconOnly
                    aria-label={`Aumentar cantidad de ${item.product.name}`}
                    onPress={() => onIncrement(item.product)}
                  >
                    +
                  </Button>
                </div>

                <div className="text-right min-w-28">
                  <span className="block text-[10px] text-slate-400">
                    Subtotal
                  </span>
                  <span className="font-display text-base font-extrabold text-slate-900 tabular-price">
                    {formatCentsToMXN(lineTotalCents)}
                  </span>
                  <button
                    type="button"
                    onClick={() => onRemove(item.product.id)}
                    className="block ml-auto text-[11px] font-medium text-blue-700 hover:underline cursor-pointer"
                  >
                    Quitar
                  </button>
                </div>
              </div>
            </div>
          </Card>
        )
      })}
    </div>
  )
}
