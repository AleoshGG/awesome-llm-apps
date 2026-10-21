import { useEffect, useMemo, useRef, useState, useTransition } from 'react'
import { useCases } from '../../../../core/di/useCasesContainer'
import type { ProductDetailEntity } from '../../domain/entities/productDetail.entity'

export type SortOption = 'featured' | 'price-asc' | 'price-desc' | 'name-asc'

export interface UseCatalogPresentationReturn {
  allProducts: ProductDetailEntity[]
  filteredProducts: ProductDetailEntity[]
  isLoading: boolean
  isSearching: boolean
  error: string | null
  searchText: string
  sortBy: SortOption
  activeProduct: ProductDetailEntity | null
  currentPage: number
  totalPages: number
  totalItems: number
  pageSize: number
  setPage: (page: number) => void
  setSearchText: (value: string) => void
  setSortBy: (sort: SortOption) => void
  openProductDetail: (product: ProductDetailEntity) => void
  closeProductDetail: () => void
  resetFilters: () => void
  reloadCatalog: () => void
}

const PAGE_SIZE = 24

/**
 * Hook de gestión de estado para la pantalla Tienda (Home).
 * Conecta con los endpoints GraphQL `products`, `searchProducts` y `product(productId)`.
 * Incluye paginación en el servidor y búsqueda no bloqueante con AbortController y useTransition.
 */
export function useCatalogPresentation(): UseCatalogPresentationReturn {
  const [allProducts, setAllProducts] = useState<ProductDetailEntity[]>([])
  const [searchedProducts, setSearchedProducts] = useState<
    ProductDetailEntity[] | null
  >(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isSearchingNetwork, setIsSearchingNetwork] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [searchText, setSearchTextState] = useState<string>('')
  const [sortBy, setSortBy] = useState<SortOption>('featured')
  const [activeProduct, setActiveProduct] =
    useState<ProductDetailEntity | null>(null)
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [totalProductsCount, setTotalProductsCount] = useState<number>(0)
  const [reloadTick, setReloadTick] = useState<number>(0)

  // React Concurrent transition for search rendering
  const [isPending, startTransition] = useTransition()
  const searchControllerRef = useRef<AbortController | null>(null)

  const isSearching = isSearchingNetwork || isPending

  // Carga paginada del catálogo desde GraphQL (`products` con limit y offset)
  useEffect(() => {
    let active = true
    setIsLoading(true)

    const offset = (currentPage - 1) * PAGE_SIZE

    void Promise.all([
      useCases.products.count.execute().catch(() => 0),
      useCases.products.findAll.execute(PAGE_SIZE, offset),
    ])
      .then(([count, products]) => {
        if (!active) return
        if (count > 0) {
          setTotalProductsCount(count)
        }
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
  }, [currentPage, reloadTick])

  // Búsqueda optimizada contra GraphQL (`searchProducts`) con AbortController, debounce y useTransition
  useEffect(() => {
    const trimmed = searchText.trim()
    if (!trimmed) {
      if (searchedProducts !== null) {
        setSearchedProducts(null)
      }
      setIsSearchingNetwork(false)
      return
    }

    // Cancel previous in-flight search request
    searchControllerRef.current?.abort()
    const controller = new AbortController()
    searchControllerRef.current = controller

    setIsSearchingNetwork(true)

    const timer = window.setTimeout(() => {
      void useCases.products.findByQuery
        .execute({ name: trimmed, limit: 50 }, controller.signal)
        .then((results) => {
          if (controller.signal.aborted) return
          startTransition(() => {
            setSearchedProducts(results)
            setError(null)
            setIsSearchingNetwork(false)
          })
        })
        .catch((err: unknown) => {
          if (controller.signal.aborted) return
          const isAbort =
            err instanceof DOMException && err.name === 'AbortError'
          if (!isAbort) {
            startTransition(() => {
              setError(
                err instanceof Error
                  ? err.message
                  : 'Ocurrió un problema al buscar productos.',
              )
              setIsSearchingNetwork(false)
            })
          }
        })
    }, 300)

    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [searchText])

  const setSearchText = (value: string) => {
    // Immediate responsive update to the text field
    setSearchTextState(value)
    if (!value.trim()) {
      searchControllerRef.current?.abort()
      setSearchedProducts(null)
      setIsSearchingNetwork(false)
    }
  }

  const setPage = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const isSearchActive = searchText.trim().length > 0 && searchedProducts !== null

  const filteredProducts = useMemo(() => {
    const baseList = isSearchActive ? searchedProducts : allProducts

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
  }, [allProducts, searchedProducts, isSearchActive, sortBy])

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
    searchControllerRef.current?.abort()
    setSearchTextState('')
    setSearchedProducts(null)
    setSortBy('featured')
    setCurrentPage(1)
  }

  const reloadCatalog = () => {
    setIsLoading(true)
    setError(null)
    setReloadTick((prev) => prev + 1)
  }

  const totalItems = isSearchActive
    ? searchedProducts.length
    : totalProductsCount

  const totalPages = Math.max(
    1,
    Math.ceil((isSearchActive ? searchedProducts.length : totalProductsCount) / PAGE_SIZE),
  )

  return {
    allProducts,
    filteredProducts,
    isLoading,
    isSearching,
    error,
    searchText,
    sortBy,
    activeProduct,
    currentPage,
    totalPages,
    totalItems,
    pageSize: PAGE_SIZE,
    setPage,
    setSearchText,
    setSortBy,
    openProductDetail,
    closeProductDetail,
    resetFilters,
    reloadCatalog,
  }
}
