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
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 sm:py-3.5">
          <button
            type="button"
            onClick={() => onNavigate('home')}
            className="group flex items-center gap-3 text-left cursor-pointer focus:outline-none"
          >
            <img
              src="/shopping.png"
              alt="Logo de Mi Súper"
              className="h-10 w-10 shrink-0 rounded-xl object-contain transition-transform duration-200 group-hover:scale-105"
            />
            <div>
              <span className="block font-display text-lg font-extrabold tracking-tight text-slate-900 leading-none">
                Mi Súper
              </span>
              <span className="mt-0.5 block text-[11px] font-medium text-slate-500">
                Tienda en línea
              </span>
            </div>
          </button>

          <nav
            aria-label="Navegación principal de la tienda"
            className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-3 gap-1 border-t border-blue-100 bg-white/96 px-2 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] shadow-[0_-8px_24px_rgba(15,23,42,0.08)] backdrop-blur-md sm:static sm:z-auto sm:flex sm:items-center sm:gap-1.5 sm:border-0 sm:bg-transparent sm:p-0 sm:shadow-none"
          >
            <Button
              size="sm"
              variant={activeView === 'home' ? 'primary' : 'ghost'}
              onPress={() => onNavigate('home')}
              className={`w-full sm:w-auto ${
                activeView === 'home'
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'text-slate-700 hover:bg-blue-50'
              }`}
            >
              Tienda
            </Button>

            <Button
              size="sm"
              variant={activeView === 'cart' ? 'primary' : 'ghost'}
              onPress={() => onNavigate('cart')}
              className={`w-full sm:w-auto inline-flex items-center gap-1.5 ${
                activeView === 'cart'
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'text-slate-700 hover:bg-blue-50'
              }`}
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4 w-4 shrink-0"
              >
                <circle cx="8" cy="21" r="1" />
                <circle cx="19" cy="21" r="1" />
                <path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12" />
              </svg>
              <span>Carrito</span>
              <Chip
                size="sm"
                color="accent"
                variant={activeView === 'cart' ? 'secondary' : 'soft'}
                className="ml-0.5"
              >
                <Chip.Label>{cartItemsCount}</Chip.Label>
              </Chip>
            </Button>

            <Button
              size="sm"
              variant={activeView === 'purchases' ? 'primary' : 'ghost'}
              onPress={() => onNavigate('purchases')}
              className={`w-full sm:w-auto inline-flex items-center gap-1.5 ${
                activeView === 'purchases'
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'text-slate-700 hover:bg-blue-50'
              }`}
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4 w-4 shrink-0"
              >
                <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z" />
                <path d="M3 6h18" />
                <path d="M16 10a4 4 0 0 1-8 0" />
              </svg>
              <span>Mis compras</span>
              <Chip size="sm" color="accent" variant="soft" className="ml-0.5">
                <Chip.Label>{purchasesCount}</Chip.Label>
              </Chip>
            </Button>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-3 py-4 sm:px-6 sm:py-6">
        {children}
      </main>
    </div>
  )
}
