import { Button, Spinner } from '@heroui/react'
import type { ProductDetailEntity } from '../../domain/entities/productDetail.entity'
import { CatalogFilterBar } from '../components/CatalogFilterBar'
import { ProductCard } from '../components/ProductCard'
import { ProductDetailModal } from '../components/ProductDetailModal'
import { useCatalogPresentation } from '../hooks/useCatalogPresentation'

interface HomePageProps {
  getProductQuantityInCart: (productId: string) => number
  onAddToCart: (product: ProductDetailEntity, quantity?: number) => void
}

export function HomePage({
  getProductQuantityInCart,
  onAddToCart,
}: HomePageProps) {
  const catalog = useCatalogPresentation()

  const hasActiveFilters =
    catalog.searchText.trim().length > 0 || catalog.sortBy !== 'featured'

  return (
    <div className="space-y-6">
      <CatalogFilterBar
        searchText={catalog.searchText}
        sortBy={catalog.sortBy}
        resultsCount={catalog.filteredProducts.length}
        hasActiveFilters={hasActiveFilters}
        onSearchChange={catalog.setSearchText}
        onSortChange={catalog.setSortBy}
        onResetFilters={catalog.resetFilters}
      />

      {catalog.error && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-blue-200 bg-blue-50/70 px-4 py-3 text-xs text-blue-950">
          <span>{catalog.error}</span>
          <Button size="sm" variant="secondary" onPress={catalog.reloadCatalog}>
            Reintentar
          </Button>
        </div>
      )}

      {catalog.isLoading ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-blue-100 bg-white py-16 text-center">
          <Spinner size="md" />
          <p className="text-xs font-medium text-slate-500">
            Cargando catálogo de productos...
          </p>
        </div>
      ) : catalog.filteredProducts.length === 0 ? (
        <div className="rounded-2xl border border-blue-100 bg-white p-10 text-center space-y-3">
          <h3 className="font-display text-lg font-bold text-slate-900">
            No encontramos productos con esa búsqueda
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Intenta con otro término o restablece el buscador para ver todos los
            artículos disponibles.
          </p>
          <div className="pt-1">
            <Button
              size="sm"
              variant="secondary"
              onPress={catalog.resetFilters}
            >
              Ver todos los productos
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {catalog.filteredProducts.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              quantityInCart={getProductQuantityInCart(product.id)}
              onAddToCart={(item) => onAddToCart(item, 1)}
              onOpenDetail={catalog.openProductDetail}
            />
          ))}
        </div>
      )}

      <ProductDetailModal
        product={catalog.activeProduct}
        quantityInCart={
          catalog.activeProduct
            ? getProductQuantityInCart(catalog.activeProduct.id)
            : 0
        }
        onClose={catalog.closeProductDetail}
        onAddToCart={onAddToCart}
      />
    </div>
  )
}
