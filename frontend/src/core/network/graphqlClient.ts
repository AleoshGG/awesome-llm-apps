import { API_ENDPOINTS } from '../config/graphqlSchema.doc'

export interface GraphQLErrorItem {
  message: string
  path?: Array<string | number>
}

export interface GraphQLResponsePayload<TData> {
  data?: TData
  errors?: GraphQLErrorItem[]
}

export class GraphQLClientError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'GraphQLClientError'
  }
}

export async function graphqlRequest<
  TData,
  TVariables extends Record<string, unknown> = Record<string, unknown>,
>(
  query: string,
  variables?: TVariables,
  signal?: AbortSignal,
): Promise<TData> {
  const response = await fetch(API_ENDPOINTS.graphql, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      variables,
    }),
    signal,
  })

  if (!response.ok) {
    throw new GraphQLClientError(
      `No se pudo comunicar con el servidor (${response.status})`,
    )
  }

  const payload = (await response.json()) as GraphQLResponsePayload<TData>

  if (payload.errors && payload.errors.length > 0) {
    throw new GraphQLClientError(
      payload.errors.map((err) => err.message).join(', '),
    )
  }

  if (payload.data === undefined) {
    throw new GraphQLClientError('El servidor devolvió una respuesta vacía')
  }

  return payload.data
}
