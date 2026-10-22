import { describe, expect, it, vi } from 'vitest'
import { SalesAgentRepositoryImpl } from './data/repositories/salesAgent.repository.impl'
import { bytesToBase64, PcmAudioQueue, resamplePcm16, validateImage } from './data/services/liveMedia'
import { parseServerEvent } from './data/models/salesAgent.dto'
import { initialSalesAgentState, salesAgentReducer } from './presentation/state/salesAgentState'
import { cartFromCommand, featuredProductForChat, navigationForCommand, productFromAgent } from './presentation/state/agentUi'

class FakeWebSocket {
  static OPEN = 1
  readyState = 0
  sent: string[] = []
  listeners = new Map<string, Array<(event: { data?: string }) => void>>()
  readonly url: string
  constructor(url: string) { this.url = url }
  addEventListener(type: string, listener: (event: { data?: string }) => void): void {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener])
  }
  emit(type: string, event: { data?: string } = {}): void {
    if (type === 'open') this.readyState = 1
    this.listeners.get(type)?.forEach((listener) => listener(event))
  }
  send(value: string): void { this.sent.push(value) }
  close(): void { this.emit('close') }
}

describe('sales agent contract', () => {
  it('validates events and upserts transcript chunks by id', () => {
    expect(parseServerEvent({ type: 'ui', id: '1', action: 'unknown', phase: 'done', payload: {} })).toBeNull()
    const partial = { type: 'transcript', id: 'a', speaker: 'agent', text: 'Hola', final: false } as const
    const done = { ...partial, text: 'Hola cliente', final: true }
    const first = salesAgentReducer(initialSalesAgentState, partial)
    const second = salesAgentReducer(first, done)
    expect(second.messages).toHaveLength(1)
    expect(second.messages[0].text).toBe('Hola cliente')
  })

  it('deduplicates UI phases and maps navigation and snake-case products', () => {
    const command = { type: 'ui', id: 'x', action: 'catalog_search', phase: 'done', payload: {} } as const
    const crossSellCommand = { type: 'ui', id: 'x2', action: 'catalog_search', phase: 'done', payload: { cross_sell: true } } as const
    const first = salesAgentReducer(initialSalesAgentState, command)
    expect(salesAgentReducer(first, command)).toBe(first)
    expect(navigationForCommand(command)).toBe('home')
    expect(navigationForCommand(crossSellCommand)).toBeNull()
    const p1 = productFromAgent({ id: 'p1', name: 'Bota Industrial Negra', description: 'Fresco', price_list_cents: 100,
      category: { id: 'c', name: 'Calzado' }, provider: { id: 'v', name: 'Casa' }, media: [] })!
    const p2 = productFromAgent({ id: 'p2', name: 'Bota Impermeable Amarilla', description: 'Lluvia', price_list_cents: 200,
      category: { id: 'c', name: 'Calzado' }, provider: { id: 'v', name: 'Casa' }, media: [] })!
    expect(p1.priceListCents).toBe(100)
    expect(featuredProductForChat(null, [p1, p2], [
      { id: 'm1', speaker: 'agent', text: 'Tengo la Bota Industrial Negra y la Bota Impermeable Amarilla.', final: true, timestamp: '10:00' },
    ], 0)?.id).toBe('p1')
    expect(featuredProductForChat(null, [p1, p2], [
      { id: 'm1', speaker: 'agent', text: 'Tengo la Bota Industrial Negra y la Bota Impermeable Amarilla.', final: true, timestamp: '10:00' },
      { id: 'm2', speaker: 'user', text: 'Háblame de la otra opción', final: true, timestamp: '10:01' },
    ], 0)?.id).toBe('p2')
    expect(cartFromCommand({ type: 'ui', id: 'c1', action: 'cart_update', phase: 'done', payload: { cart: [] } })).toEqual([])
  })

  it('connects, pauses, resumes, interrupts and closes through one socket', async () => {
    const sockets: FakeWebSocket[] = []
    vi.stubGlobal('WebSocket', class extends FakeWebSocket {
      static OPEN = 1
      constructor(url: string) { super(url); sockets.push(this) }
    })
    const repository = new SalesAgentRepositoryImpl('ws://test/ws/sales-agent')
    const events: string[] = []
    repository.subscribe((event) => events.push(event.type), () => undefined)
    const connecting = repository.connect()
    sockets[0].emit('open')
    await connecting
    sockets[0].emit('message', { data: JSON.stringify({ type: 'interrupted' }) })
    repository.pause()
    repository.resume()
    repository.disconnect()
    expect(events).toEqual(['interrupted'])
    expect(sockets[0].sent.map((value) => JSON.parse(value).type)).toEqual(['pause', 'resume', 'close'])
    vi.unstubAllGlobals()
  })
})

describe('media boundaries', () => {
  it('resamples and clamps PCM to 16 kHz', () => {
    const output = resamplePcm16(new Float32Array([2, 1, 0, -1, -2, 0]), 48000, 16000)
    expect(output).toHaveLength(2)
    expect(output[0]).toBe(32767)
    expect(output[1]).toBe(-32768)
  })

  it('accepts supported small images and rejects type and size violations', () => {
    expect(() => validateImage(new Blob(['ok'], { type: 'image/jpeg' }))).not.toThrow()
    expect(() => validateImage(new Blob(['bad'], { type: 'image/gif' }))).toThrow(/JPEG/)
    expect(() => validateImage(new Blob([new Uint8Array(4 * 1024 * 1024 + 1)], { type: 'image/png' }))).toThrow(/4 MiB/)
  })

  it('queues PCM playback and interruption stops pending sources', async () => {
    const stopped = vi.fn()
    class FakeContext {
      currentTime = 0
      destination = {}
      resume = vi.fn()
      close = vi.fn()
      createBuffer() { return { duration: 1 / 24000, getChannelData: () => new Float32Array(1) } }
      createBufferSource() { return { buffer: null, connect: vi.fn(), start: vi.fn(), stop: stopped, onended: null } }
    }
    vi.stubGlobal('AudioContext', FakeContext)
    const queue = new PcmAudioQueue()
    await queue.enqueue(bytesToBase64(new Uint8Array([0, 0])))
    queue.stop()
    expect(stopped).toHaveBeenCalledOnce()
    vi.unstubAllGlobals()
  })
})
