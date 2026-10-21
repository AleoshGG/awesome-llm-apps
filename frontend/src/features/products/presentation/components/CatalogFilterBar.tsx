import { Button, SearchField, Spinner } from '@heroui/react'
import {
  STORE_CATEGORIES,
  type SortOption,
} from '../hooks/useCatalogPresentation'

interface CatalogFilterBarProps {
  searchText: string
  selectedCategory: string | null
  sortBy: SortOption
  resultsCount: number
  hasActiveFilters: boolean
  onSearchChange: (value: string) => void
  onCategoryChange: (category: string | null) => void
  onSortChange: (sort: SortOption) => void
  onResetFilters: () => void
  isAgentSearching?: boolean
  isSearching?: boolean
}

export function CatalogFilterBar({
  searchText,
  selectedCategory,
  sortBy,
  resultsCount,
  hasActiveFilters,
  onSearchChange,
  onCategoryChange,
  onSortChange,
  onResetFilters,
  isAgentSearching = false,
  isSearching = false,
}: CatalogFilterBarProps) {
  return (
    <section
      aria-label="Buscador de productos"
      className={`relative overflow-hidden rounded-2xl border border-blue-100 bg-white p-4 shadow-2xs space-y-3.5 ${isAgentSearching ? 'agent-search-scan' : ''}`}
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
              {isSearching ? (
                <div className="pl-3 flex items-center justify-center text-blue-600">
                  <Spinner size="sm" />
                </div>
              ) : (
                <SearchField.SearchIcon />
              )}
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

      <div
        role="group"
        aria-label="Filtrar por categoría"
        className="flex items-center gap-1.5 overflow-x-auto border-t border-slate-100 pt-3 no-scrollbar"
      >
        <span className="mr-1 shrink-0 text-xs font-medium text-slate-500">
          Categorías:
        </span>

        <Button
          size="sm"
          variant={selectedCategory === null ? 'primary' : 'ghost'}
          onPress={() => onCategoryChange(null)}
          className={`shrink-0 rounded-full px-3 text-xs font-medium ${
            selectedCategory === null
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'border border-slate-200/80 bg-slate-50/70 text-slate-700 hover:bg-blue-50 hover:text-blue-700'
          }`}
        >
          Todas
        </Button>

        {STORE_CATEGORIES.map((category) => {
          const isSelected = selectedCategory === category
          return (
            <Button
              key={category}
              size="sm"
              variant={isSelected ? 'primary' : 'ghost'}
              onPress={() =>
                onCategoryChange(isSelected ? null : category)
              }
              className={`shrink-0 rounded-full px-3.5 text-xs font-medium ${
                isSelected
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'border border-slate-200/80 bg-slate-50/70 text-slate-700 hover:bg-blue-50 hover:text-blue-700'
              }`}
            >
              {category}
            </Button>
          )
        })}
      </div>
    </section>
  )
}
