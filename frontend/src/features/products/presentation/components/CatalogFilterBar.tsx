import { Button, SearchField } from '@heroui/react'
import type { SortOption } from '../hooks/useCatalogPresentation'

interface CatalogFilterBarProps {
  searchText: string
  sortBy: SortOption
  resultsCount: number
  hasActiveFilters: boolean
  onSearchChange: (value: string) => void
  onSortChange: (sort: SortOption) => void
  onResetFilters: () => void
  isAgentSearching?: boolean
}

export function CatalogFilterBar({
  searchText,
  sortBy,
  resultsCount,
  hasActiveFilters,
  onSearchChange,
  onSortChange,
  onResetFilters,
  isAgentSearching = false,
}: CatalogFilterBarProps) {
  return (
    <section
      aria-label="Buscador de productos"
      className={`relative overflow-hidden rounded-2xl border border-blue-100 bg-white p-4 shadow-2xs ${isAgentSearching ? 'agent-search-scan' : ''}`}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="w-full md:max-w-lg">
          <SearchField
            fullWidth
            value={searchText}
            onChange={onSearchChange}
            aria-label="Buscar productos en la tienda"
          >
            <SearchField.Group>
              <SearchField.SearchIcon />
              <SearchField.Input placeholder="Buscar productos por nombre o marca..." />
              <SearchField.ClearButton />
            </SearchField.Group>
          </SearchField>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs font-medium text-slate-500 tabular-price">
            <strong className="text-slate-900">{resultsCount}</strong>{' '}
            {resultsCount === 1 ? 'producto disponible' : 'productos disponibles'}
          </span>

          <div className="flex items-center gap-2">
            <label htmlFor="catalog-sort" className="text-xs text-slate-500">
              Ordenar por:
            </label>
            <select
              id="catalog-sort"
              value={sortBy}
              onChange={(event) =>
                onSortChange(event.target.value as SortOption)
              }
              className="rounded-lg border border-blue-100 bg-blue-50/40 px-2.5 py-1.5 text-xs font-medium text-slate-800 focus:border-blue-600 focus:outline-none"
            >
              <option value="featured">Destacados</option>
              <option value="price-asc">Menor precio</option>
              <option value="price-desc">Mayor precio</option>
              <option value="name-asc">Nombre (A - Z)</option>
            </select>

            {hasActiveFilters && (
              <Button size="sm" variant="ghost" onPress={onResetFilters}>
                Limpiar
              </Button>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
