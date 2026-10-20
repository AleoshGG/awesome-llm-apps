import { Button, Chip } from '@heroui/react'
import type { ReactNode } from 'react'

export type AppView = 'home' | 'cart' | 'purchases'

interface AppShellProps {
  activeView: AppView
  cartItemsCount: number
  purchasesCount: number
  onNavigate: (view: AppView) => void
  children: ReactNode
}

export function AppShell({
  activeView,
  cartItemsCount,
  purchasesCount,
  onNavigate,
  children,
}: AppShellProps) {
  return (
    <div className="min-h-screen flex flex-col bg-[var(--canvas-bg)] text-slate-900 pb-24">
      <header className="sticky top-0 z-30 border-b border-blue-100 bg-white/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3.5 sm:px-6">
          <button
            type="button"
            onClick={() => onNavigate('home')}
            className="flex items-center gap-2.5 text-left cursor-pointer"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 font-display text-sm font-extrabold text-white shadow-xs">
              BA
            </span>
            <div>
              <span className="block font-display text-base font-extrabold tracking-tight text-slate-900 leading-none">
                Bazar Azul
              </span>
              <span className="block text-[11px] font-medium text-slate-500">
                Tienda en línea
              </span>
            </div>
          </button>

          <nav
            aria-label="Navegación principal de la tienda"
            className="flex items-center gap-1.5 sm:gap-2"
          >
            <Button
              size="sm"
              variant={activeView === 'home' ? 'primary' : 'ghost'}
              onPress={() => onNavigate('home')}
              className={
                activeView === 'home'
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'text-slate-700 hover:bg-blue-50'
              }
            >
              Tienda
            </Button>

            <Button
              size="sm"
              variant={activeView === 'cart' ? 'primary' : 'ghost'}
              onPress={() => onNavigate('cart')}
              className={
                activeView === 'cart'
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'text-slate-700 hover:bg-blue-50'
              }
            >
              <span>Carrito</span>
              <Chip
                size="sm"
                color="accent"
                variant={activeView === 'cart' ? 'secondary' : 'soft'}
                className="ml-1"
              >
                <Chip.Label>{cartItemsCount}</Chip.Label>
              </Chip>
            </Button>

            <Button
              size="sm"
              variant={activeView === 'purchases' ? 'primary' : 'ghost'}
              onPress={() => onNavigate('purchases')}
              className={
                activeView === 'purchases'
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'text-slate-700 hover:bg-blue-50'
              }
            >
              <span>Mis compras</span>
              <Chip size="sm" color="accent" variant="soft" className="ml-1">
                <Chip.Label>{purchasesCount}</Chip.Label>
              </Chip>
            </Button>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
        {children}
      </main>
    </div>
  )
}
