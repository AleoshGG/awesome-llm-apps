import type { SalesAgentRepository } from '../../domain/repositories/salesAgent.repository'

export class SalesAgentRepositoryImpl implements SalesAgentRepository {
  async connect(): Promise<void> {
    // Pendiente de conectar con WebSocket `/ws/sales-agent` en la fase de lógica de negocio
    return Promise.resolve()
  }

  sendText(_text: string): void {
    // Pendiente de envío por WebSocket
  }

  sendAudioChunk(_base64Pcm16: string): void {
    // Pendiente de envío de PCM16 a 16kHz por WebSocket
  }

  disconnect(): void {
    // Pendiente de cierre de sesión WebSocket
  }
}
