export type AgentToolPhaseDto = 'running' | 'done' | 'error' | 'cancelled'
export type AgentUiActionDto = 'catalog_search' | 'catalog_product' | 'cart_update' | 'checkout'

export type SalesAgentClientEventDto =
  | { type: 'text'; text: string }
  | { type: 'audio'; data: string }
  | { type: 'image'; mime_type: 'image/jpeg' | 'image/png' | 'image/webp'; data: string }
  | { type: 'pause' }
  | { type: 'resume' }
  | { type: 'close' }

export type SalesAgentServerEventDto =
  | { type: 'session'; provider: string; model: string; tools: string[]; input_sample_rate: number; output_sample_rate: number }
  | { type: 'ready' }
  | { type: 'paused' }
  | { type: 'resume_error'; message: string }
  | { type: 'audio'; data: string; mime_type: string }
  | { type: 'transcript'; speaker: 'user' | 'agent'; id: string; text: string; final: boolean }
  | { type: 'tool'; id: string; name: string; args: Record<string, unknown>; phase: AgentToolPhaseDto; result?: unknown }
  | { type: 'ui'; id: string; action: AgentUiActionDto; phase: AgentToolPhaseDto; payload: Record<string, unknown> }
  | { type: 'interrupted' }
  | { type: 'turn_complete' }
  | { type: 'error'; message: string }

const phases = new Set(['running', 'done', 'error', 'cancelled'])
const actions = new Set(['catalog_search', 'catalog_product', 'cart_update', 'checkout'])

export function parseServerEvent(raw: unknown): SalesAgentServerEventDto | null {
  if (!raw || typeof raw !== 'object') return null
  const value = raw as Record<string, unknown>
  if (typeof value.type !== 'string') return null
  if (value.type === 'ready' || value.type === 'paused' || value.type === 'interrupted' || value.type === 'turn_complete') {
    return { type: value.type }
  }
  if ((value.type === 'error' || value.type === 'resume_error') && typeof value.message === 'string') {
    return { type: value.type, message: value.message }
  }
  if (value.type === 'audio' && typeof value.data === 'string' && typeof value.mime_type === 'string') return value as SalesAgentServerEventDto
  if (value.type === 'transcript' && typeof value.id === 'string' && typeof value.text === 'string' &&
      (value.speaker === 'user' || value.speaker === 'agent') && typeof value.final === 'boolean') return value as SalesAgentServerEventDto
  if (value.type === 'ui' && typeof value.id === 'string' && typeof value.action === 'string' && actions.has(value.action) &&
      typeof value.phase === 'string' && phases.has(value.phase) && value.payload !== null && typeof value.payload === 'object') return value as SalesAgentServerEventDto
  if (value.type === 'tool' && typeof value.id === 'string' && typeof value.name === 'string' && typeof value.phase === 'string' &&
      phases.has(value.phase) && value.args !== null && typeof value.args === 'object') return value as SalesAgentServerEventDto
  if (value.type === 'session' && typeof value.provider === 'string' && typeof value.model === 'string' && Array.isArray(value.tools) &&
      typeof value.input_sample_rate === 'number' && typeof value.output_sample_rate === 'number') return value as SalesAgentServerEventDto
  return null
}
