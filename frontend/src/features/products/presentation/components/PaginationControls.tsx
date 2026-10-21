import { Button } from '@heroui/react'

interface PaginationControlsProps {
  currentPage: number
  totalPages: number
  totalItems: number
  pageSize: number
  onPageChange: (page: number) => void
  isLoading?: boolean
}

export function PaginationControls({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  isLoading = false,
}: PaginationControlsProps) {
  if (totalPages <= 1) {
    return null
  }

  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1
  const endItem = Math.min(currentPage * pageSize, totalItems)

  // Calculate visible page numbers with ellipsis
  const getPageNumbers = (): (number | 'ellipsis')[] => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }

    if (currentPage <= 4) {
      return [1, 2, 3, 4, 5, 'ellipsis', totalPages]
    }

    if (currentPage >= totalPages - 3) {
      return [
        1,
        'ellipsis',
        totalPages - 4,
        totalPages - 3,
        totalPages - 2,
        totalPages - 1,
        totalPages,
      ]
    }

    return [
      1,
      'ellipsis',
      currentPage - 1,
      currentPage,
      currentPage + 1,
      'ellipsis',
      totalPages,
    ]
  }

  const pages = getPageNumbers()

  return (
    <nav
      aria-label="Paginación de productos"
      className="flex flex-col items-center justify-between gap-4 rounded-2xl border border-blue-100 bg-white p-4 shadow-2xs sm:flex-row"
    >
      <div className="text-xs font-medium text-slate-500 tabular-price">
        Mostrando <strong className="text-slate-900">{startItem}</strong> -{' '}
        <strong className="text-slate-900">{endItem}</strong> de{' '}
        <strong className="text-slate-900">{totalItems.toLocaleString('es-MX')}</strong>{' '}
        productos
      </div>

      <div className="flex items-center gap-1 sm:gap-1.5">
        <Button
          size="sm"
          variant="secondary"
          isDisabled={currentPage <= 1 || isLoading}
          onPress={() => onPageChange(currentPage - 1)}
          className="text-xs"
        >
          ← Anterior
        </Button>

        <div className="flex items-center gap-1">
          {pages.map((p, idx) => {
            if (p === 'ellipsis') {
              return (
                <span
                  key={`ellipsis-${idx}`}
                  className="px-1.5 py-1 text-xs text-slate-400 select-none"
                >
                  …
                </span>
              )
            }

            const isActive = p === currentPage
            return (
              <Button
                key={p}
                size="sm"
                variant={isActive ? 'primary' : 'ghost'}
                isDisabled={isLoading}
                onPress={() => onPageChange(p)}
                className={`min-w-8 h-8 px-2 text-xs font-semibold ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-700 hover:bg-blue-50 hover:text-blue-700'
                }`}
              >
                {p}
              </Button>
            )
          })}
        </div>

        <Button
          size="sm"
          variant="secondary"
          isDisabled={currentPage >= totalPages || isLoading}
          onPress={() => onPageChange(currentPage + 1)}
          className="text-xs"
        >
          Siguiente →
        </Button>
      </div>
    </nav>
  )
}
