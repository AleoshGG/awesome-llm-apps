import { Button, Spinner } from '@heroui/react'
import type { ProductDetailEntity } from '../../domain/entities/productDetail.entity'
import { CatalogFilterBar } from '../components/CatalogFilterBar'
import { PaginationControls } from '../components/PaginationControls'
import { ProductCard } from '../components/ProductCard'
import { ProductDetailModal } from '../components/ProductDetailModal'
import { useCatalogPresentation } from '../hooks/useCatalogPresentation'

interface HomePageProps {
  getProductQuantityInCart: (productId: string) => number
  onAddToCart: (product: ProductDetailEntity, quantity?: number) => void
  agentProducts?: ProductDetailEntity[] | null
  agentSearchPhase?: 'running' | 'done' | 'error' | 'cancelled' | null
  agentProduct?: ProductDetailEntity | null
  onDismissAgentProduct?: () => void
  onClearAgentResults?: () => void
}

export function HomePage({
  getProductQuantityInCart,
  onAddToCart,
  agentProducts = null,
  agentSearchPhase = null,
  agentProduct = null,
  onDismissAgentProduct,
  onClearAgentResults,
}: HomePageProps) {
  const catalog = useCatalogPresentation()

  const hasActiveFilters =
    catalog.searchText.trim().length > 0 ||
    catalog.selectedCategory !== null ||
    catalog.sortBy !== 'featured'

  const displayCount = agentProducts !== null
    ? agentProducts.length
    : catalog.totalItems

  return (
    <div className="space-y-6">
      <CatalogFilterBar
        searchText={catalog.searchText}
        selectedCategory={catalog.selectedCategory}
        sortBy={catalog.sortBy}
        resultsCount={displayCount}
        hasActiveFilters={hasActiveFilters}
        onSearchChange={(value) => {
          onClearAgentResults?.()
          catalog.setSearchText(value)
        }}
        onCategoryChange={(category) => {
          onClearAgentResults?.()
          catalog.setSelectedCategory(category)
        }}
        onSortChange={catalog.setSortBy}
        onResetFilters={() => {
          onClearAgentResults?.()
          catalog.resetFilters()
        }}
        isAgentSearching={agentSearchPhase === 'running'}
        isSearching={catalog.isSearching}
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
      ) : (agentProducts ?? catalog.filteredProducts).length === 0 ? (
        <div className="rounded-2xl border border-blue-100 bg-white p-10 text-center space-y-3">
          <h3 className="font-display text-lg font-bold text-slate-900">
            No encontramos coincidencias
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Intenta con otro término o restablece el buscador para ver todos los
            artículos disponibles.
          </p>
          <div className="pt-1">
            <Button
              size="sm"
              variant="secondary"
              onPress={() => {
                onClearAgentResults?.()
                catalog.resetFilters()
              }}
            >
              Ver todos los productos
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {(agentProducts ?? catalog.filteredProducts).map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              quantityInCart={getProductQuantityInCart(product.id)}
              onAddToCart={(item) => onAddToCart(item, 1)}
              onOpenDetail={catalog.openProductDetail}
              isHighlighted={agentSearchPhase === 'done' && agentProducts !== null}
            />
          ))}
        </div>
      )}

      {agentProducts === null && !catalog.isLoading && catalog.totalPages > 1 && (
        <PaginationControls
          currentPage={catalog.currentPage}
          totalPages={catalog.totalPages}
          totalItems={catalog.totalItems}
          pageSize={catalog.pageSize}
          onPageChange={catalog.setPage}
          isLoading={catalog.isLoading}
        />
      )}

      <ProductDetailModal
        product={agentProduct ?? catalog.activeProduct}
        quantityInCart={
          (agentProduct ?? catalog.activeProduct)
            ? getProductQuantityInCart((agentProduct ?? catalog.activeProduct)!.id)
            : 0
        }
        onClose={agentProduct ? (onDismissAgentProduct ?? catalog.closeProductDetail) : catalog.closeProductDetail}
        onAddToCart={onAddToCart}
      />
    </div>
  )
}
