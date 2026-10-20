import type { AgentCloseListener, AgentEventListener, SalesAgentRepository } from '../../domain/repositories/salesAgent.repository'
import type { SalesAgentClientEventDto } from '../models/salesAgent.dto'
import { parseServerEvent } from '../models/salesAgent.dto'

function defaultUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/sales-agent`
}

export class SalesAgentRepositoryImpl implements SalesAgentRepository {
  private readonly url: string
  private socket: WebSocket | null = null
  private expectedClose = false
  private listener: AgentEventListener = () => undefined
  private closeListener: AgentCloseListener = () => undefined

  constructor(url = defaultUrl()) { this.url = url }

  subscribe(listener: AgentEventListener, onClose: AgentCloseListener): () => void {
    this.listener = listener
    this.closeListener = onClose
    return () => {
      this.listener = () => undefined
      this.closeListener = () => undefined
    }
  }

  connect(): Promise<void> {
    if (this.socket?.readyState === WebSocket.OPEN) return Promise.resolve()
    this.expectedClose = false
    return new Promise((resolve, reject) => {
      const socket = new WebSocket(this.url)
      this.socket = socket
      socket.addEventListener('open', () => resolve(), { once: true })
      socket.addEventListener('error', () => reject(new Error('No pudimos conectar con el asistente.')), { once: true })
      socket.addEventListener('message', (message) => {
        try {
          const parsed = parseServerEvent(JSON.parse(String(message.data)))
          if (parsed) this.listener(parsed)
        } catch {
          // Ignore malformed server frames and keep the recoverable session alive.
        }
      })
      socket.addEventListener('close', () => {
        this.closeListener(this.expectedClose)
        if (this.socket === socket) this.socket = null
      })
    })
  }

  private send(message: SalesAgentClientEventDto): void {
    if (this.socket?.readyState === WebSocket.OPEN) this.socket.send(JSON.stringify(message))
  }

  sendText(text: string): void { this.send({ type: 'text', text }) }
  sendAudioChunk(data: string): void { this.send({ type: 'audio', data }) }
  sendImage(mime_type: 'image/jpeg' | 'image/png' | 'image/webp', data: string): void { this.send({ type: 'image', mime_type, data }) }
  pause(): void { this.send({ type: 'pause' }) }
  resume(): void { this.send({ type: 'resume' }) }
  disconnect(): void {
    this.expectedClose = true
    this.send({ type: 'close' })
    this.socket?.close(1000)
    this.socket = null
  }
}
