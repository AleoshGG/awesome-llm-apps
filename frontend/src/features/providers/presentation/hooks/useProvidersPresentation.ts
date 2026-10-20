import { useEffect, useMemo, useState } from 'react'
import { useCases } from '../../../../core/di/useCasesContainer'
import type { ProviderEntity } from '../../domain/entities/provider.entity'

export interface UseProvidersPresentationReturn {
  providers: ProviderEntity[]
  isLoading: boolean
  error: string | null
  selectedProviderId: string | null
  selectedProvider: ProviderEntity | null
  selectProvider: (providerId: string | null) => void
  toggleProvider: (providerId: string) => void
  reloadProviders: () => void
}

export function useProvidersPresentation(): UseProvidersPresentationReturn {
  const [providers, setProviders] = useState<ProviderEntity[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(
    null,
  )
  const [reloadTick, setReloadTick] = useState<number>(0)

  useEffect(() => {
    let active = true

    void useCases.providers.findAll
      .execute()
      .then((result) => {
        if (!active) return
        setProviders(result)
        setError(null)
        setIsLoading(false)
      })
      .catch((err: unknown) => {
        if (!active) return
        setError(
          err instanceof Error
            ? err.message
            : 'No fue posible cargar las marcas disponibles.',
        )
        setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadTick])

  const selectedProvider = useMemo(
    () => providers.find((item) => item.id === selectedProviderId) ?? null,
    [providers, selectedProviderId],
  )

  const selectProvider = (providerId: string | null) => {
    setSelectedProviderId(providerId)
  }

  const toggleProvider = (providerId: string) => {
    setSelectedProviderId((current) =>
      current === providerId ? null : providerId,
    )
  }

  const reloadProviders = () => {
    setIsLoading(true)
    setError(null)
    setReloadTick((prev) => prev + 1)
  }

  return {
    providers,
    isLoading,
    error,
    selectedProviderId,
    selectedProvider,
    selectProvider,
    toggleProvider,
    reloadProviders,
  }
}
