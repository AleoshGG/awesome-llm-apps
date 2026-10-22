import { CategoryRepositoryImpl } from '../../features/products/data/repositories/category.repository.impl'
import { ProductRepositoryImpl } from '../../features/products/data/repositories/product.repository.impl'
import { CategoryFindAllUseCase } from '../../features/products/domain/usecases/categoryFindAll.usecase'
import { ProductCountUseCase } from '../../features/products/domain/usecases/productCount.usecase'
import { ProductFindAllUseCase } from '../../features/products/domain/usecases/productFindAll.usecase'
import { ProductFindByIdUseCase } from '../../features/products/domain/usecases/productFindById.usecase'
import { ProductFindByQueryUseCase } from '../../features/products/domain/usecases/productFindByQuery.usecase'
import { ProviderRepositoryImpl } from '../../features/providers/data/repositories/provider.repository.impl'
import { ProviderFindAllUseCase } from '../../features/providers/domain/usecases/providerFindAll.usecase'
import { CartRepositoryImpl } from '../../features/sales/data/repositories/cart.repository.impl'
import { SaleRepositoryImpl } from '../../features/sales/data/repositories/sale.repository.impl'
import { AddProductToCartUseCase } from '../../features/sales/domain/usecases/addProductToCart.usecase'
import { ClearCartUseCase } from '../../features/sales/domain/usecases/clearCart.usecase'
import { GetCartUseCase } from '../../features/sales/domain/usecases/getCart.usecase'
import { GetSalesUseCase } from '../../features/sales/domain/usecases/getSales.usecase'
import { RegisterSaleUseCase } from '../../features/sales/domain/usecases/registerSale.usecase'
import { RemoveProductFromCartUseCase } from '../../features/sales/domain/usecases/removeProductFromCart.usecase'

const productRepository = new ProductRepositoryImpl()
const categoryRepository = new CategoryRepositoryImpl()
const providerRepository = new ProviderRepositoryImpl()
const cartRepository = new CartRepositoryImpl()
const saleRepository = new SaleRepositoryImpl()

export const useCases = {
  products: {
    findAll: new ProductFindAllUseCase(productRepository),
    findById: new ProductFindByIdUseCase(productRepository),
    findByQuery: new ProductFindByQueryUseCase(productRepository),
    findAllCategories: new CategoryFindAllUseCase(categoryRepository),
    count: new ProductCountUseCase(productRepository),
  },
  providers: {
    findAll: new ProviderFindAllUseCase(providerRepository),
  },
  sales: {
    getCart: new GetCartUseCase(cartRepository),
    addProductToCart: new AddProductToCartUseCase(cartRepository),
    removeProductFromCart: new RemoveProductFromCartUseCase(cartRepository),
    clearCart: new ClearCartUseCase(cartRepository),
    registerSale: new RegisterSaleUseCase(saleRepository),
    getSales: new GetSalesUseCase(saleRepository),
  },
} as const
