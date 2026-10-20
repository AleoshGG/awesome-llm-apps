import { Avatar, Button, Chip } from '@heroui/react'
import type { ProviderEntity } from '../../domain/entities/provider.entity'

interface ProviderStripProps {
  providers: ProviderEntity[]
  selectedProviderId: string | null
  onToggleProvider: (providerId: string) => void
  onClearProvider: () => void
}

export function ProviderStrip({
  providers,
  selectedProviderId,
  onToggleProvider,
  onClearProvider,
}: ProviderStripProps) {
  return (
    <section
      aria-label="Marcas y proveedores"
      className="rounded-2xl border border-blue-100 bg-white p-4 shadow-2xs"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3">
        <h2 className="font-display text-sm font-bold text-slate-900">
          Marcas disponibles
        </h2>

        {selectedProviderId && (
          <Button size="sm" variant="ghost" onPress={onClearProvider}>
            Ver todas
          </Button>
        )}
      </div>

      <div className="flex gap-2.5 overflow-x-auto pb-1">
        {providers.map((provider) => {
          const isSelected = provider.id === selectedProviderId
          const initials = provider.name
            .split(' ')
            .slice(0, 2)
            .map((part) => part[0])
            .join('')

          return (
            <button
              key={provider.id}
              type="button"
              onClick={() => onToggleProvider(provider.id)}
              className={`group flex shrink-0 items-center gap-3 rounded-xl border px-3.5 py-2.5 text-left transition-colors cursor-pointer ${
                isSelected
                  ? 'border-blue-600 bg-blue-50/70 text-slate-900'
                  : 'border-slate-200/80 bg-slate-50/60 hover:border-blue-300 hover:bg-white'
              }`}
            >
              <Avatar size="sm" className="shrink-0">
                <Avatar.Image src={provider.logoUrl} alt={provider.name} />
                <Avatar.Fallback>{initials}</Avatar.Fallback>
              </Avatar>

              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="truncate text-xs font-semibold text-slate-900">
                    {provider.name}
                  </span>
                  {isSelected && (
                    <Chip size="sm" color="accent" variant="soft">
                      <Chip.Label>Seleccionada</Chip.Label>
                    </Chip>
                  )}
                </div>
                <p className="max-w-[180px] truncate text-[11px] text-slate-500">
                  {provider.address}
                </p>
              </div>
            </button>
          )
        })}
      </div>
    </section>
  )
}
