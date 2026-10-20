import type { SalesAgentServerEventDto } from '../../data/models/salesAgent.dto'
import type { AgentConnectionPhase, AgentTranscriptMessageEntity } from '../../domain/entities/salesAgent.entity'

export type UiCommand = Extract<SalesAgentServerEventDto, { type: 'ui' }>

export interface SalesAgentState {
  phase: AgentConnectionPhase
  messages: AgentTranscriptMessageEntity[]
  uiCommand: UiCommand | null
  visualSearchActive: boolean
  statusMessage: string | null
}

export const initialSalesAgentState: SalesAgentState = {
  phase: 'idle',
  messages: [],
  uiCommand: null,
  visualSearchActive: false,
  statusMessage: null,
}

function timeLabel(): string {
  return new Date().toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' })
}

export function upsertTranscript(messages: AgentTranscriptMessageEntity[], event: Extract<SalesAgentServerEventDto, { type: 'transcript' }>): AgentTranscriptMessageEntity[] {
  const existing = messages.findIndex((message) => message.id === event.id)
  const next = { id: event.id, speaker: event.speaker, text: event.text, final: event.final,
    timestamp: existing >= 0 ? messages[existing].timestamp : timeLabel() }
  if (existing < 0) return [...messages, next]
  const updated = [...messages]
  updated[existing] = next
  return updated
}

export type SalesAgentStateEvent = SalesAgentServerEventDto | { type: 'local_phase'; phase: AgentConnectionPhase } | { type: 'reset' }

export function salesAgentReducer(state: SalesAgentState, event: SalesAgentStateEvent): SalesAgentState {
  switch (event.type) {
    case 'local_phase': return { ...state, phase: event.phase }
    case 'reset': return initialSalesAgentState
    case 'ready': return { ...state, phase: 'ready', statusMessage: null }
    case 'paused': return { ...state, phase: 'paused', visualSearchActive: false }
    case 'resume_error': return { ...state, phase: 'error', statusMessage: event.message }
    case 'error': return { ...state, phase: 'error', statusMessage: event.message }
    case 'transcript': return { ...state, messages: upsertTranscript(state.messages, event) }
    case 'audio': return { ...state, phase: 'speaking' }
    case 'interrupted': return { ...state, phase: 'ready' }
    case 'turn_complete': return { ...state, phase: 'ready' }
    case 'tool':
      return event.name === 'visual_product_search'
        ? { ...state, visualSearchActive: event.phase === 'running' }
        : state
    case 'ui':
      if (state.uiCommand?.id === event.id && state.uiCommand.phase === event.phase) return state
      return { ...state, uiCommand: event,
        visualSearchActive: event.action === 'catalog_search' && event.payload.source === 'visual'
          ? event.phase === 'running' : state.visualSearchActive,
        statusMessage: event.phase === 'error' && typeof event.payload.message === 'string'
          ? event.payload.message : event.phase === 'done' ? null : state.statusMessage }
    default: return state
  }
}
