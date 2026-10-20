import { useEffect, useMemo, useState } from 'react'
import { useCases } from '../../../../core/di/useCasesContainer'
import type { ProductDetailEntity } from '../../domain/entities/productDetail.entity'

export type SortOption = 'featured' | 'price-asc' | 'price-desc' | 'name-asc'

export interface UseCatalogPresentationReturn {
  allProducts: ProductDetailEntity[]
  filteredProducts: ProductDetailEntity[]
  isLoading: boolean
  error: string | null
  searchText: string
  sortBy: SortOption
  activeProduct: ProductDetailEntity | null
  setSearchText: (value: string) => void
  setSortBy: (sort: SortOption) => void
  openProductDetail: (product: ProductDetailEntity) => void
  closeProductDetail: () => void
  resetFilters: () => void
  reloadCatalog: () => void
}

/**
 * Hook de gestión de estado para la pantalla Tienda (Home).
 * Conecta con los endpoints GraphQL `products`, `searchProducts` y `product(productId)`.
 */
export function useCatalogPresentation(): UseCatalogPresentationReturn {
  const [allProducts, setAllProducts] = useState<ProductDetailEntity[]>([])
  const [searchedProducts, setSearchedProducts] = useState<
    ProductDetailEntity[] | null
  >(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [searchText, setSearchTextState] = useState<string>('')
  const [sortBy, setSortBy] = useState<SortOption>('featured')
  const [activeProduct, setActiveProduct] =
    useState<ProductDetailEntity | null>(null)
  const [reloadTick, setReloadTick] = useState<number>(0)

  // Carga inicial del catálogo completo desde GraphQL (`products`)
  useEffect(() => {
    let active = true

    void useCases.products.findAll
      .execute()
      .then((products) => {
        if (!active) return
        setAllProducts(products)
        setError(null)
        setIsLoading(false)
      })
      .catch((err: unknown) => {
        if (!active) return
        setError(
          err instanceof Error
            ? err.message
            : 'No fue posible cargar los productos de la tienda.',
        )
        setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadTick])

  // Búsqueda contra GraphQL (`searchProducts`) con debounce de 250 ms
  useEffect(() => {
    const trimmed = searchText.trim()
    if (!trimmed) {
      return
    }

    let active = true
    const timer = window.setTimeout(() => {
      void useCases.products.findByQuery
        .execute({ name: trimmed })
        .then((results) => {
          if (!active) return
          setSearchedProducts(results)
          setError(null)
        })
        .catch((err: unknown) => {
          if (!active) return
          setError(
            err instanceof Error
              ? err.message
              : 'Ocurrió un problema al buscar productos.',
          )
        })
    }, 250)

    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [searchText])

  const setSearchText = (value: string) => {
    setSearchTextState(value)
    if (!value.trim()) {
      setSearchedProducts(null)
    }
  }

  const filteredProducts = useMemo(() => {
    const trimmed = searchText.trim()
    const baseList =
      trimmed && searchedProducts !== null ? searchedProducts : allProducts

    if (sortBy === 'price-asc') {
      return [...baseList].sort(
        (a, b) => a.priceListCents - b.priceListCents,
      )
    }
    if (sortBy === 'price-desc') {
      return [...baseList].sort(
        (a, b) => b.priceListCents - a.priceListCents,
      )
    }
    if (sortBy === 'name-asc') {
      return [...baseList].sort((a, b) => a.name.localeCompare(b.name, 'es'))
    }
    return baseList
  }, [allProducts, searchedProducts, searchText, sortBy])

  const openProductDetail = (product: ProductDetailEntity) => {
    setActiveProduct(product)
    void useCases.products.findById
      .execute(product.id)
      .then((freshProduct) => {
        if (freshProduct) {
          setActiveProduct((current) =>
            current?.id === freshProduct.id ? freshProduct : current,
          )
        }
      })
      .catch(() => {
        // Conserva el detalle ya visible si falla el refresco secundario
      })
  }

  const closeProductDetail = () => {
    setActiveProduct(null)
  }

  const resetFilters = () => {
    setSearchTextState('')
    setSearchedProducts(null)
    setSortBy('featured')
  }

  const reloadCatalog = () => {
    setIsLoading(true)
    setError(null)
    setReloadTick((prev) => prev + 1)
  }

  return {
    allProducts,
    filteredProducts,
    isLoading,
    error,
    searchText,
    sortBy,
    activeProduct,
    setSearchText,
    setSortBy,
    openProductDetail,
    closeProductDetail,
    resetFilters,
    reloadCatalog,
  }
}
