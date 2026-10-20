import { useEffect, useMemo, useState } from 'react'
import { useCases } from '../../../../core/di/useCasesContainer'
import type { SaleEntity } from '../../domain/entities/sale.entity'

export interface UsePurchasesPresentationReturn {
  sales: SaleEntity[]
  filteredSales: SaleEntity[]
  isLoading: boolean
  error: string | null
  searchFolio: string
  expandedSaleId: string | null
  totalOrdersCount: number
  totalSpentCents: number
  setSearchFolio: (query: string) => void
  toggleExpandedSale: (saleId: string) => void
  prependNewSale: (sale: SaleEntity) => void
  refreshSales: () => void
}

/**
 * Hook de gestión de estado para la pantalla "Mis compras".
 * Conecta con la query GraphQL `sales`.
 */
export function usePurchasesPresentation(): UsePurchasesPresentationReturn {
  const [sales, setSales] = useState<SaleEntity[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [searchFolio, setSearchFolio] = useState<string>('')
  const [expandedSaleId, setExpandedSaleId] = useState<string | null>(null)
  const [reloadTick, setReloadTick] = useState<number>(0)

  useEffect(() => {
    let active = true

    void useCases.sales.getSales
      .execute()
      .then((fetchedSales) => {
        if (!active) return
        const sorted = [...fetchedSales].sort(
          (a, b) =>
            new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
        )
        setSales(sorted)
        setExpandedSaleId((current) => current ?? sorted[0]?.id ?? null)
        setError(null)
        setIsLoading(false)
      })
      .catch((err: unknown) => {
        if (!active) return
        setError(
          err instanceof Error
            ? err.message
            : 'No fue posible cargar el historial de compras.',
        )
        setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadTick])

  const filteredSales = useMemo(() => {
    const query = searchFolio.trim().toLowerCase()
    if (!query) return sales

    return sales.filter((sale) =>
      sale.items.some(
        (item) =>
          item.product.name.toLowerCase().includes(query) ||
          item.product.provider.name.toLowerCase().includes(query),
      ),
    )
  }, [sales, searchFolio])

  const totalOrdersCount = sales.length

  const totalSpentCents = useMemo(
    () =>
      sales.reduce(
        (acc, sale) =>
          acc +
          sale.items.reduce(
            (sub, item) => sub + item.product.priceListCents * item.quantity,
            0,
          ),
        0,
      ),
    [sales],
  )

  const toggleExpandedSale = (saleId: string) => {
    setExpandedSaleId((current) => (current === saleId ? null : saleId))
  }

  const prependNewSale = (sale: SaleEntity) => {
    setSales((current) => [
      sale,
      ...current.filter((item) => item.id !== sale.id),
    ])
    setExpandedSaleId(sale.id)
  }

  const refreshSales = () => {
    setIsLoading(true)
    setError(null)
    setReloadTick((prev) => prev + 1)
  }

  return {
    sales,
    filteredSales,
    isLoading,
    error,
    searchFolio,
    expandedSaleId,
    totalOrdersCount,
    totalSpentCents,
    setSearchFolio,
    toggleExpandedSale,
    prependNewSale,
    refreshSales,
  }
}
