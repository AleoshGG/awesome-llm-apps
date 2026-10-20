import type { SalesAgentServerEventDto } from '../../data/models/salesAgent.dto'

export type AgentEventListener = (event: SalesAgentServerEventDto) => void
export type AgentCloseListener = (expected: boolean) => void

export interface SalesAgentRepository {
  connect(): Promise<void>
  subscribe(listener: AgentEventListener, onClose: AgentCloseListener): () => void
  sendText(text: string): void
  sendAudioChunk(base64Pcm16: string): void
  sendImage(mimeType: 'image/jpeg' | 'image/png' | 'image/webp', base64: string): void
  pause(): void
  resume(): void
  disconnect(): void
}
