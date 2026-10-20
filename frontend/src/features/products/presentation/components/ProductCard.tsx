import { Button, Card, Chip } from '@heroui/react'
import { formatCentsToMXN } from '../../../../core/utils/formatters'
import type { ProductDetailEntity } from '../../domain/entities/productDetail.entity'

interface ProductCardProps {
  product: ProductDetailEntity
  quantityInCart: number
  onAddToCart: (product: ProductDetailEntity) => void
  onOpenDetail: (product: ProductDetailEntity) => void
  isHighlighted?: boolean
}

export function ProductCard({
  product,
  quantityInCart,
  onAddToCart,
  onOpenDetail,
  isHighlighted = false,
}: ProductCardProps) {
  const mainImage =
    product.media.find((item) => item.isMain)?.url ?? product.media[0]?.url

  return (
    <Card className={`group flex h-full flex-col justify-between overflow-hidden rounded-2xl border border-blue-100/90 bg-white shadow-2xs transition-colors hover:border-blue-300 ${isHighlighted ? 'agent-result-highlight' : ''}`}>
      <div>
        <div className="relative aspect-4/3 w-full overflow-hidden bg-slate-100">
          {mainImage ? (
            <img
              src={mainImage}
              alt={product.name}
              loading="lazy"
              className="h-full w-full object-cover object-center transition-transform duration-300 group-hover:scale-103"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-xs text-slate-400">
              Sin imagen
            </div>
          )}

          {quantityInCart > 0 && (
            <div className="absolute top-3 right-3">
              <Chip size="sm" color="accent" variant="primary">
                <Chip.Label>{quantityInCart} en el carrito</Chip.Label>
              </Chip>
            </div>
          )}
        </div>

        <Card.Header className="flex flex-col items-start gap-1 px-4 pt-4 pb-2">
          <span className="text-[11px] font-medium text-blue-700">
            {product.provider.name}
          </span>
          <Card.Title className="font-display text-base font-bold text-slate-900 line-clamp-1">
            {product.name}
          </Card.Title>
          <Card.Description className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
            {product.description}
          </Card.Description>
        </Card.Header>
      </div>

      <Card.Footer className="mt-2 flex items-center justify-between gap-2 border-t border-slate-100 px-4 py-3">
        <div>
          <span className="block text-[10px] text-slate-400">Precio</span>
          <span className="font-display text-base font-bold text-slate-900 tabular-price">
            {formatCentsToMXN(product.priceListCents)}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            size="sm"
            variant="ghost"
            onPress={() => onOpenDetail(product)}
            className="text-blue-700 hover:bg-blue-50"
          >
            Ver
          </Button>
          <Button
            size="sm"
            variant="primary"
            onPress={() => onAddToCart(product)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Agregar
          </Button>
        </div>
      </Card.Footer>
    </Card>
  )
}
