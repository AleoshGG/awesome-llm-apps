import { Button, Card, SearchField, Spinner } from '@heroui/react'
import { formatCentsToMXN } from '../../../../core/utils/formatters'
import type { ProductDetailEntity } from '../../../products/domain/entities/productDetail.entity'
import type { SaleEntity } from '../../domain/entities/sale.entity'
import { PurchaseOrderCard } from '../components/PurchaseOrderCard'

interface PurchasesPageProps {
  sales: SaleEntity[]
  isLoading: boolean
  error: string | null
  searchFolio: string
  expandedSaleId: string | null
  totalOrdersCount: number
  totalSpentCents: number
  onSearchFolioChange: (value: string) => void
  onToggleExpandSale: (saleId: string) => void
  onReorderProduct: (product: ProductDetailEntity, quantity: number) => void
  onRefreshSales: () => void
  onNavigateToStore: () => void
  highlightedSaleId?: string | null
}

export function PurchasesPage({
  sales,
  isLoading,
  error,
  searchFolio,
  expandedSaleId,
  totalOrdersCount,
  totalSpentCents,
  onSearchFolioChange,
  onToggleExpandSale,
  onReorderProduct,
  onRefreshSales,
  onNavigateToStore,
  highlightedSaleId = null,
}: PurchasesPageProps) {
  return (
    <div className="space-y-6">
      <header className="grid gap-4 rounded-2xl border border-blue-100 bg-white p-5 shadow-2xs md:grid-cols-12 md:items-center">
        <div className="md:col-span-7 space-y-1">
          <h1 className="font-display text-2xl font-extrabold text-slate-900">
            Mis compras
          </h1>
          <p className="text-xs sm:text-sm text-slate-500">
            Consulta los productos que has comprado en la tienda.
          </p>
        </div>

        <div className="md:col-span-5 grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-blue-100 bg-blue-50/40 p-3">
            <span className="block text-[11px] text-slate-500">
              Pedidos realizados
            </span>
            <span className="font-display text-xl font-extrabold text-slate-900 tabular-price">
              {totalOrdersCount}
            </span>
          </div>
          <div className="rounded-xl border border-blue-100 bg-blue-50/40 p-3">
            <span className="block text-[11px] text-slate-500">
              Total acumulado
            </span>
            <span className="font-display text-lg font-extrabold text-blue-700 tabular-price">
              {formatCentsToMXN(totalSpentCents)}
            </span>
          </div>
        </div>
      </header>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-blue-100 bg-white p-4 shadow-2xs">
        <div className="w-full sm:max-w-md">
          <SearchField
            fullWidth
            value={searchFolio}
            onChange={onSearchFolioChange}
            aria-label="Buscar en mis compras por producto o marca"
          >
            <SearchField.Group>
              <SearchField.SearchIcon />
              <SearchField.Input placeholder="Buscar en mis compras por producto o marca..." />
              <SearchField.ClearButton />
            </SearchField.Group>
          </SearchField>
        </div>

        <Button size="sm" variant="secondary" onPress={onNavigateToStore}>
          Volver a la tienda
        </Button>
      </div>

      {error && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-blue-200 bg-blue-50/70 px-4 py-3 text-xs text-blue-950">
          <span>{error}</span>
          <Button size="sm" variant="secondary" onPress={onRefreshSales}>
            Reintentar
          </Button>
        </div>
      )}

      {isLoading ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-blue-100 bg-white py-16 text-center">
          <Spinner size="md" />
          <p className="text-xs font-medium text-slate-500">
            Cargando tus compras...
          </p>
        </div>
      ) : sales.length === 0 ? (
        <Card className="rounded-2xl border border-blue-100 bg-white p-8 text-center">
          <Card.Header className="flex flex-col items-center gap-2">
            <Card.Title className="font-display text-lg font-bold text-slate-900">
              No se encontraron compras
            </Card.Title>
            <Card.Description className="text-xs text-slate-500">
              Intenta con otro nombre de producto o realiza un pedido desde tu
              carrito.
            </Card.Description>
          </Card.Header>
        </Card>
      ) : (
        <div className="space-y-3">
          {sales.map((sale) => (
            <PurchaseOrderCard
              key={sale.id}
              sale={sale}
              isExpanded={expandedSaleId === sale.id}
              onToggleExpand={onToggleExpandSale}
              onReorderProduct={onReorderProduct}
              isHighlighted={highlightedSaleId === sale.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}
