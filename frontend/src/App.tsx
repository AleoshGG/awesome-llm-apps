import { useEffect, useState } from 'react'
import { AppShell, type AppView } from './core/layout/AppShell'
import { HomePage } from './features/products/presentation/pages/HomePage'
import { useCartPresentation } from './features/sales/presentation/hooks/useCartPresentation'
import { usePurchasesPresentation } from './features/sales/presentation/hooks/usePurchasesPresentation'
import { CartPage } from './features/sales/presentation/pages/CartPage'
import { PurchasesPage } from './features/sales/presentation/pages/PurchasesPage'
import { SiriChatWidget } from './features/sales_agent/presentation/components/SiriChatWidget'
import { SiriFloatingButton } from './features/sales_agent/presentation/components/SiriFloatingButton'
import { useSalesAgentPresentation } from './features/sales_agent/presentation/hooks/useSalesAgentPresentation'
import { navigationForCommand, productFromAgent, productsFromCommand, saleFromCommand } from './features/sales_agent/presentation/state/agentUi'
import type { AgentToolPhase } from './features/sales_agent/domain/entities/salesAgent.entity'
import type { ProductDetailEntity } from './features/products/domain/entities/productDetail.entity'

export function App() {
  const [activeView, setActiveView] = useState<AppView>('home')

  const cart = useCartPresentation()
  const purchases = usePurchasesPresentation()
  const salesAgent = useSalesAgentPresentation()
  const [agentProducts, setAgentProducts] = useState<ProductDetailEntity[] | null>(null)
  const [agentSearchPhase, setAgentSearchPhase] = useState<AgentToolPhase | null>(null)
  const [agentProduct, setAgentProduct] = useState<ProductDetailEntity | null>(null)
  const [agentCartOperation, setAgentCartOperation] = useState<'add' | 'remove' | 'view' | null>(null)
  const [agentCartProductId, setAgentCartProductId] = useState<string | null>(null)
  const [agentCartStatus, setAgentCartStatus] = useState<string | null>(null)
  const [highlightedSaleId, setHighlightedSaleId] = useState<string | null>(null)

  // WebSocket commands deliberately synchronize independent page-level stores.
  // oxlint-disable react/set-state-in-effect react-hooks/exhaustive-deps
  useEffect(() => {
    const command = salesAgent.uiCommand
    if (!command) return
    const view = navigationForCommand(command)
    if (view) setActiveView(view)
    if (command.action === 'catalog_search') {
      setAgentSearchPhase(command.phase)
      setAgentProduct(null)
      if (command.phase === 'done') setAgentProducts(productsFromCommand(command))
    }
    if (command.action === 'catalog_product' && command.phase === 'done') {
      setAgentProduct(productFromAgent(command.payload.product))
    }
    if (command.action === 'cart_update') {
      const operation = command.payload.operation
      setAgentCartOperation(operation === 'add' || operation === 'remove' || operation === 'view' ? operation : null)
      const args = command.payload.arguments
      setAgentCartProductId(args && typeof args === 'object' && typeof (args as Record<string, unknown>).product_id === 'string'
        ? (args as Record<string, unknown>).product_id as string : null)
      setAgentCartStatus(command.phase === 'running' ? 'Actualizando tu carrito…'
        : command.phase === 'error' && typeof command.payload.message === 'string' ? command.payload.message
          : command.phase === 'done' && operation === 'remove' ? 'Producto retirado del carrito.' : null)
      if (command.phase === 'done') cart.refreshCart()
    }
    if (command.action === 'checkout') {
      setAgentCartStatus(command.phase === 'running' ? 'Confirmando tu compra…'
        : command.phase === 'error' && typeof command.payload.message === 'string' ? command.payload.message : null)
      if (command.phase === 'done') {
        const sale = saleFromCommand(command)
        if (sale) {
          purchases.prependNewSale(sale)
          setHighlightedSaleId(sale.id)
        }
        cart.refreshCart()
        purchases.refreshSales()
      }
    }
  }, [salesAgent.uiCommand])
  // oxlint-enable react/set-state-in-effect react-hooks/exhaustive-deps

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
            agentProducts={agentProducts}
            agentSearchPhase={agentSearchPhase}
            agentProduct={agentProduct}
            onDismissAgentProduct={() => setAgentProduct(null)}
            onClearAgentResults={() => {
              setAgentProducts(null)
              setAgentSearchPhase(null)
            }}
          />
        )}

        {activeView === 'cart' && (
          <CartPage
            items={cart.items}
            isLoading={cart.isLoading}
            isSubmitting={cart.isSubmitting || salesAgent.uiCommand?.action === 'checkout' && salesAgent.uiCommand.phase === 'running'}
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
            agentOperation={agentCartOperation}
            agentProductId={agentCartProductId}
            agentStatus={agentCartStatus}
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
            highlightedSaleId={highlightedSaleId}
          />
        )}
      </AppShell>

      <SiriChatWidget
        isOpen={salesAgent.isOpen}
        phase={salesAgent.phase}
        isMicActive={salesAgent.isMicActive}
        isCameraActive={salesAgent.isCameraActive}
        cameraStream={salesAgent.cameraStream}
        visualSearchActive={salesAgent.visualSearchActive}
        statusMessage={salesAgent.statusMessage}
        draftText={salesAgent.draftText}
        messages={salesAgent.messages}
        featuredProduct={agentProduct ?? agentProducts?.[0] ?? null}
        onClose={salesAgent.closeWidget}
        onEndSession={salesAgent.endSession}
        onToggleMic={salesAgent.toggleMic}
        onToggleCamera={salesAgent.toggleCamera}
        onCaptureCamera={salesAgent.captureCamera}
        onSelectImage={salesAgent.selectImage}
        onRetryConnection={salesAgent.retryConnection}
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
