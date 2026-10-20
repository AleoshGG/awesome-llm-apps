/**
 * Entidades de dominio para el asistente de ventas en vivo (Gemini Live WebSocket).
 */

export type AgentConnectionPhase =
  | 'idle'
  | 'connecting'
  | 'ready'
  | 'listening'
  | 'speaking'
  | 'paused'
  | 'error'

export type AgentToolPhase = 'running' | 'done' | 'error' | 'cancelled'

export interface AgentToolCallEntity {
  id: string
  name:
    | 'search_products'
    | 'get_product_details'
    | 'list_categories'
    | 'list_providers'
    | 'add_to_cart'
    | 'remove_from_cart'
    | 'get_cart'
    | 'checkout'
  argsSummary: string
  phase: AgentToolPhase
  resultSummary?: string
}

export interface AgentTranscriptMessageEntity {
  id: string
  speaker: 'user' | 'agent'
  text: string
  final: boolean
  timestamp: string
  toolCall?: AgentToolCallEntity
}

export interface AgentSessionMetaEntity {
  provider: string
  model: string
  voice: string
  inputSampleRate: number
  outputSampleRate: number
}
