export type SalesAgentClientEventDto =
  | { type: 'text'; text: string }
  | { type: 'audio'; data: string }
  | { type: 'close' }

export type SalesAgentServerEventDto =
  | {
      type: 'session'
      provider: string
      model: string
      tools: string[]
      input_sample_rate: number
      output_sample_rate: number
    }
  | { type: 'ready' }
  | { type: 'audio'; data: string; mime_type: string }
  | {
      type: 'transcript'
      speaker: 'user' | 'agent'
      id: string
      text: string
      final: boolean
    }
  | {
      type: 'tool'
      id: string
      name: string
      args: Record<string, unknown>
      phase: 'running' | 'done' | 'error' | 'cancelled'
      result?: unknown
    }
  | { type: 'interrupted' }
  | { type: 'turn_complete' }
  | { type: 'error'; message: string }
