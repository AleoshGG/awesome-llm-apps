export interface SalesAgentRepository {
  connect(): Promise<void>
  sendText(text: string): void
  sendAudioChunk(base64Pcm16: string): void
  disconnect(): void
}
