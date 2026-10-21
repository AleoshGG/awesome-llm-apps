import { useEffect, useState } from 'react'
import { Avatar, Button, Chip, Modal, Separator } from '@heroui/react'
import { formatCentsToMXN } from '../../../../core/utils/formatters'
import type { ProductDetailEntity } from '../../domain/entities/productDetail.entity'

interface ProductDetailModalProps {
  product: ProductDetailEntity | null
  quantityInCart: number
  onClose: () => void
  onAddToCart: (product: ProductDetailEntity, quantity?: number) => void
}

export function ProductDetailModal({
  product,
  quantityInCart,
  onClose,
  onAddToCart,
}: ProductDetailModalProps) {
  const [selectedImageIndex, setSelectedImageIndex] = useState<number>(0)

  useEffect(() => {
    setSelectedImageIndex(0)
  }, [product?.id])

  if (!product) {
    return null
  }

  const mediaList = product.media.filter((item) => Boolean(item.url))
  const currentImage =
    mediaList[selectedImageIndex]?.url ??
    product.media.find((item) => item.isMain)?.url ??
    product.media[0]?.url

  return (
    <Modal
      isOpen={Boolean(product)}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <Modal.Backdrop isDismissable>
        <Modal.Container size="lg" placement="center">
          <Modal.Dialog>
            <Modal.Header className="flex items-start justify-between gap-3">
              <div>
                <span className="block text-xs font-semibold text-blue-700 pb-0.5">
                  {product.provider.name}
                </span>
                <Modal.Heading className="font-display text-xl font-bold text-slate-900">
                  {product.name}
                </Modal.Heading>
              </div>
              <Modal.CloseTrigger />
            </Modal.Header>

            <Modal.Body className="space-y-4">
              {currentImage && (
                <div className="aspect-16/10 w-full overflow-hidden rounded-2xl bg-slate-100 border border-slate-100">
                  <img
                    src={currentImage}
                    alt={product.name}
                    className="h-full w-full object-cover object-center transition-all duration-200"
                  />
                </div>
              )}

              {mediaList.length > 1 && (
                <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-0.5">
                  {mediaList.map((item, idx) => (
                    <button
                      key={item.id || idx}
                      type="button"
                      onClick={() => setSelectedImageIndex(idx)}
                      className={`relative aspect-square w-14 shrink-0 overflow-hidden rounded-xl border-2 transition-all cursor-pointer ${
                        selectedImageIndex === idx
                          ? 'border-blue-600 ring-2 ring-blue-600/20 scale-102'
                          : 'border-slate-200 opacity-70 hover:opacity-100 hover:border-slate-300'
                      }`}
                    >
                      <img
                        src={item.url}
                        alt={`${product.name} - vista ${idx + 1}`}
                        className="h-full w-full object-cover object-center"
                      />
                    </button>
                  ))}
                </div>
              )}

              <p className="text-sm text-slate-700 leading-relaxed">
                {product.description}
              </p>

              <Separator />

              <div className="flex items-center justify-between rounded-xl border border-blue-100 bg-blue-50/40 p-3">
                <div className="flex items-center gap-3">
                  <Avatar size="sm">
                    <Avatar.Image
                      src={product.provider.logoUrl}
                      alt={product.provider.name}
                    />
                    <Avatar.Fallback>
                      {product.provider.name.slice(0, 2)}
                    </Avatar.Fallback>
                  </Avatar>
                  <div>
                    <span className="block text-xs font-semibold text-slate-900">
                      Vendido y enviado por {product.provider.name}
                    </span>
                    <span className="block text-[11px] text-slate-500">
                      {product.provider.address}
                    </span>
                  </div>
                </div>
              </div>
            </Modal.Body>

            <Modal.Footer className="flex items-center justify-between gap-3 pt-2">
              <div>
                <span className="block text-xs text-slate-500">
                  Precio unitario
                </span>
                <span className="font-display text-xl font-extrabold text-slate-900 tabular-price">
                  {formatCentsToMXN(product.priceListCents)}
                </span>
              </div>

              <div className="flex items-center gap-2">
                {quantityInCart > 0 && (
                  <Chip size="sm" color="accent" variant="soft">
                    <Chip.Label>{quantityInCart} en el carrito</Chip.Label>
                  </Chip>
                )}
                <Button variant="secondary" onPress={onClose}>
                  Cerrar
                </Button>
                <Button
                  variant="primary"
                  onPress={() => {
                    onAddToCart(product, 1)
                    onClose()
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Agregar al carrito
                </Button>
              </div>
            </Modal.Footer>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal>
  )
}
