import { useState } from 'react'
import { AppShell, type AppView } from './core/layout/AppShell'
import { HomePage } from './features/products/presentation/pages/HomePage'
import { useCartPresentation } from './features/sales/presentation/hooks/useCartPresentation'
import { usePurchasesPresentation } from './features/sales/presentation/hooks/usePurchasesPresentation'
import { CartPage } from './features/sales/presentation/pages/CartPage'
import { PurchasesPage } from './features/sales/presentation/pages/PurchasesPage'
import { SiriChatWidget } from './features/sales_agent/presentation/components/SiriChatWidget'
import { SiriFloatingButton } from './features/sales_agent/presentation/components/SiriFloatingButton'
import { useSalesAgentPresentation } from './features/sales_agent/presentation/hooks/useSalesAgentPresentation'

export function App() {
  const [activeView, setActiveView] = useState<AppView>('home')

  const cart = useCartPresentation()
  const purchases = usePurchasesPresentation()
  const salesAgent = useSalesAgentPresentation()

  return (
    <>
      <AppShell
        activeView={activeView}
        cartItemsCount={cart.totalItemsCount}
        purchasesCount={purchases.totalOrdersCount}
        onNavigate={setActiveView}
      >
        {activeView === 'home' && (
          <HomePage
            getProductQuantityInCart={cart.getProductQuantity}
            onAddToCart={cart.addItem}
          />
        )}

        {activeView === 'cart' && (
          <CartPage
            items={cart.items}
            isLoading={cart.isLoading}
            isSubmitting={cart.isSubmitting}
            error={cart.error}
            totalItemsCount={cart.totalItemsCount}
            subtotalCents={cart.subtotalCents}
            shippingCents={cart.shippingCents}
            totalCents={cart.totalCents}
            checkoutStep={cart.checkoutStep}
            lastCompletedSale={cart.lastCompletedSale}
            onIncrementItem={(product) => cart.addItem(product, 1)}
            onDecrementItem={cart.decrementItem}
            onRemoveItem={cart.removeItem}
            onClearCart={cart.clearCart}
            onSetCheckoutStep={cart.setCheckoutStep}
            onConfirmPurchase={() =>
              cart.completePurchase((newSale) => {
                purchases.prependNewSale(newSale)
              })
            }
            onRefreshCart={cart.refreshCart}
            onNavigateToStore={() => setActiveView('home')}
            onNavigateToPurchases={() => setActiveView('purchases')}
          />
        )}

        {activeView === 'purchases' && (
          <PurchasesPage
            sales={purchases.filteredSales}
            isLoading={purchases.isLoading}
            error={purchases.error}
            searchFolio={purchases.searchFolio}
            expandedSaleId={purchases.expandedSaleId}
            totalOrdersCount={purchases.totalOrdersCount}
            totalSpentCents={purchases.totalSpentCents}
            onSearchFolioChange={purchases.setSearchFolio}
            onToggleExpandSale={purchases.toggleExpandedSale}
            onReorderProduct={(product, quantity) => {
              cart.addItem(product, quantity)
              setActiveView('cart')
            }}
            onRefreshSales={purchases.refreshSales}
            onNavigateToStore={() => setActiveView('home')}
          />
        )}
      </AppShell>

      <SiriChatWidget
        isOpen={salesAgent.isOpen}
        phase={salesAgent.phase}
        isMicActive={salesAgent.isMicActive}
        isCameraActive={salesAgent.isCameraActive}
        draftText={salesAgent.draftText}
        messages={salesAgent.messages}
        onClose={salesAgent.closeWidget}
        onToggleMic={salesAgent.toggleMic}
        onToggleCamera={salesAgent.toggleCamera}
        onDraftChange={salesAgent.setDraftText}
        onSendMessage={salesAgent.sendUserMessage}
      />

      <SiriFloatingButton
        isOpen={salesAgent.isOpen}
        phase={salesAgent.phase}
        isMicActive={salesAgent.isMicActive}
        onToggle={salesAgent.toggleWidget}
      />
    </>
  )
}

export default App
