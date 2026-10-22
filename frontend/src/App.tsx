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
import {
  cartFromCommand,
  featuredProductForChat,
  navigationForCommand,
  productFromAgent,
  productsFromCommand,
  saleFromCommand,
} from './features/sales_agent/presentation/state/agentUi'
import type { AgentToolPhase } from './features/sales_agent/domain/entities/salesAgent.entity'
import type { ProductDetailEntity } from './features/products/domain/entities/productDetail.entity'

export function App() {
  const [activeView, setActiveView] = useState<AppView>('home')

  const cart = useCartPresentation()
  const purchases = usePurchasesPresentation()
  const salesAgent = useSalesAgentPresentation()
  const [agentProducts, setAgentProducts] = useState<ProductDetailEntity[] | null>(null)
  const [chatProducts, setChatProducts] = useState<ProductDetailEntity[] | null>(null)
  const [searchMessageIndex, setSearchMessageIndex] = useState<number>(0)
  const [isCrossSell, setIsCrossSell] = useState<boolean>(false)
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
      const crossSell = command.payload.cross_sell === true
      setIsCrossSell(crossSell)
      if (!crossSell) {
        setAgentSearchPhase(command.phase)
        setAgentProduct(null)
        if (command.phase === 'done') {
          const found = productsFromCommand(command)
          setAgentProducts(found)
          setChatProducts(found)
          setSearchMessageIndex(salesAgent.messages.length)
        }
      } else if (command.phase === 'done') {
        const found = productsFromCommand(command)
        if (found.length > 0) {
          setChatProducts((prev) => {
            const existing = prev ?? []
            const seen = new Set(existing.map((item) => item.id))
            return [...existing, ...found.filter((item) => !seen.has(item.id))]
          })
        }
        setSearchMessageIndex(salesAgent.messages.length)
      }
    }
    if (command.action === 'catalog_product' && command.phase === 'done') {
      setIsCrossSell(command.payload.cross_sell === true)
      setAgentProduct(productFromAgent(command.payload.product))
      setSearchMessageIndex(salesAgent.messages.length)
    }
    if (command.action === 'cart_update') {
      const operation = command.payload.operation
      setAgentCartOperation(operation === 'add' || operation === 'remove' || operation === 'view' ? operation : null)
      if (operation === 'add' && command.phase === 'running') {
        setAgentProduct(null)
        setChatProducts(null)
        setIsCrossSell(true)
      }
      const args = command.payload.arguments
      setAgentCartProductId(args && typeof args === 'object' && typeof (args as Record<string, unknown>).product_id === 'string'
        ? (args as Record<string, unknown>).product_id as string : null)
      setAgentCartStatus(command.phase === 'running' ? 'Actualizando tu carrito…'
        : command.phase === 'error' && typeof command.payload.message === 'string' ? command.payload.message
          : command.phase === 'done' && operation === 'remove' ? 'Producto retirado del carrito.'
            : command.phase === 'done' && operation === 'clear' ? 'Carrito vaciado.' : null)
      if (command.phase === 'done') {
        const syncedCart = cartFromCommand(command)
        if (syncedCart !== null) {
          cart.syncCart(syncedCart)
        } else {
          cart.refreshCart()
        }
      }
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
        cart.syncCart([])
        purchases.refreshSales()
      }
    }
  }, [salesAgent.uiCommand])
  // oxlint-enable react/set-state-in-effect react-hooks/exhaustive-deps

  const featuredProduct = featuredProductForChat(
    agentProduct,
    chatProducts ?? agentProducts,
    salesAgent.messages,
    searchMessageIndex,
    isCrossSell,
  )

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
            agentProduct={salesAgent.isOpen ? null : agentProduct}
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
        featuredProduct={featuredProduct}
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
