/**
 * Documentación y contratos del esquema GraphQL y WebSocket del Backend.
 *
 * Endpoint HTTP GraphQL: POST /graphql
 * Endpoint WebSocket: ws://<host>/ws/sales-agent
 */

export const API_ENDPOINTS = {
  graphql: '/graphql',
  salesAgentWs: '/ws/sales-agent',
} as const

const PRODUCT_DETAIL_FIELDS = /* GraphQL */ `
  id
  name
  description
  priceListCents
  category {
    id
    name
  }
  provider {
    id
    name
    address
    logoUrl
  }
  media {
    id
    url
    productId
    isMain
  }
`

export const GRAPHQL_OPERATIONS_DOC = {
  queries: {
    GET_PRODUCTS_COUNT: /* GraphQL */ `
      query GetProductsCount {
        productsCount
      }
    `,
    GET_PRODUCTS: /* GraphQL */ `
      query GetProducts($limit: Int, $offset: Int) {
        products(limit: $limit, offset: $offset) {
          ${PRODUCT_DETAIL_FIELDS}
        }
      }
    `,
    GET_PRODUCT_BY_ID: /* GraphQL */ `
      query GetProductById($productId: String!) {
        product(productId: $productId) {
          ${PRODUCT_DETAIL_FIELDS}
        }
      }
    `,
    SEARCH_PRODUCTS: /* GraphQL */ `
      query SearchProducts($query: ProductQueryInput) {
        searchProducts(query: $query) {
          ${PRODUCT_DETAIL_FIELDS}
        }
      }
    `,
    GET_CATEGORIES: /* GraphQL */ `
      query GetCategories {
        categories {
          id
          name
        }
      }
    `,
    GET_PROVIDERS: /* GraphQL */ `
      query GetProviders {
        providers {
          id
          name
          address
          logoUrl
        }
      }
    `,
    GET_CART: /* GraphQL */ `
      query GetCart {
        cart {
          quantity
          product {
            ${PRODUCT_DETAIL_FIELDS}
          }
        }
      }
    `,
    GET_SALES: /* GraphQL */ `
      query GetSales {
        sales {
          id
          createdAt
          items {
            quantity
            product {
              ${PRODUCT_DETAIL_FIELDS}
            }
          }
        }
      }
    `,
  },
  mutations: {
    ADD_PRODUCT_TO_CART: /* GraphQL */ `
      mutation AddProductToCart($productId: String!, $quantity: Int! = 1) {
        addProductToCart(productId: $productId, quantity: $quantity) {
          quantity
          product {
            ${PRODUCT_DETAIL_FIELDS}
          }
        }
      }
    `,
    REMOVE_PRODUCT_FROM_CART: /* GraphQL */ `
      mutation RemoveProductFromCart($productId: String!) {
        removeProductFromCart(productId: $productId) {
          quantity
          product {
            ${PRODUCT_DETAIL_FIELDS}
          }
        }
      }
    `,
    CLEAR_CART: /* GraphQL */ `
      mutation ClearCart {
        clearCart {
          quantity
          product {
            ${PRODUCT_DETAIL_FIELDS}
          }
        }
      }
    `,
    REGISTER_SALE: /* GraphQL */ `
      mutation RegisterSale {
        registerSale {
          id
          createdAt
          items {
            quantity
            product {
              ${PRODUCT_DETAIL_FIELDS}
            }
          }
        }
      }
    `,
  },
} as const
