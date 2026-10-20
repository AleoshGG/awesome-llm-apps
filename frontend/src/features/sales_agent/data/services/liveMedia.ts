const MAX_IMAGE_BYTES = 4 * 1024 * 1024
const IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp'])

export function bytesToBase64(bytes: Uint8Array): string {
  let binary = ''
  for (let offset = 0; offset < bytes.length; offset += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000))
  }
  return btoa(binary)
}

export function base64ToBytes(value: string): Uint8Array {
  const binary = atob(value)
  return Uint8Array.from(binary, (character) => character.charCodeAt(0))
}

export function resamplePcm16(samples: Float32Array, sourceRate: number, targetRate = 16000): Int16Array {
  const length = Math.max(1, Math.round(samples.length * targetRate / sourceRate))
  const output = new Int16Array(length)
  const ratio = sourceRate / targetRate
  for (let index = 0; index < length; index += 1) {
    const position = index * ratio
    const left = Math.floor(position)
    const right = Math.min(left + 1, samples.length - 1)
    const sample = samples[left] * (1 - (position - left)) + samples[right] * (position - left)
    output[index] = Math.round(Math.max(-1, Math.min(1, sample)) * (sample < 0 ? 32768 : 32767))
  }
  return output
}

export function validateImage(file: Blob): asserts file is Blob & { type: 'image/jpeg' | 'image/png' | 'image/webp' } {
  if (!IMAGE_TYPES.has(file.type)) throw new Error('Usa una imagen JPEG, PNG o WebP.')
  if (file.size === 0 || file.size > MAX_IMAGE_BYTES) throw new Error('La imagen debe pesar menos de 4 MiB.')
}

export async function imageToBase64(file: Blob): Promise<string> {
  validateImage(file)
  return bytesToBase64(new Uint8Array(await file.arrayBuffer()))
}

export class MicrophoneCapture {
  private context: AudioContext | null = null
  private stream: MediaStream | null = null
  private node: AudioNode | null = null
  private source: MediaStreamAudioSourceNode | null = null

  async start(onChunk: (base64: string) => void): Promise<void> {
    if (this.stream) return
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
    })
    this.context = new AudioContext()
    this.source = this.context.createMediaStreamSource(this.stream)
    const handle = (samples: Float32Array) => {
      const pcm = resamplePcm16(samples, this.context?.sampleRate ?? 48000)
      onChunk(bytesToBase64(new Uint8Array(pcm.buffer)))
    }

    if (this.context.audioWorklet) {
      const source = `class P extends AudioWorkletProcessor{process(i){const c=i[0]?.[0];if(c)this.port.postMessage(c);return true}}registerProcessor('pcm-capture',P)`
      const url = URL.createObjectURL(new Blob([source], { type: 'text/javascript' }))
      try {
        await this.context.audioWorklet.addModule(url)
        const worklet = new AudioWorkletNode(this.context, 'pcm-capture')
        worklet.port.onmessage = (event: MessageEvent<Float32Array>) => handle(event.data)
        this.node = worklet
      } catch {
        this.node = null
      } finally {
        URL.revokeObjectURL(url)
      }
    }
    if (!this.node) {
      const fallback = this.context.createScriptProcessor(2048, 1, 1)
      fallback.onaudioprocess = (event) => handle(event.inputBuffer.getChannelData(0))
      this.node = fallback
    }
    this.source.connect(this.node)
    this.node.connect(this.context.destination)
  }

  stop(): void {
    this.node?.disconnect()
    this.source?.disconnect()
    this.stream?.getTracks().forEach((track) => track.stop())
    void this.context?.close()
    this.node = null
    this.source = null
    this.stream = null
    this.context = null
  }
}

export class PcmAudioQueue {
  private context: AudioContext | null = null
  private nextStart = 0
  private sources = new Set<AudioBufferSourceNode>()

  async enqueue(base64: string, sampleRate = 24000): Promise<void> {
    this.context ??= new AudioContext({ sampleRate })
    await this.context.resume()
    const bytes = base64ToBytes(base64)
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
    const buffer = this.context.createBuffer(1, Math.floor(bytes.byteLength / 2), sampleRate)
    const channel = buffer.getChannelData(0)
    for (let index = 0; index < channel.length; index += 1) channel[index] = view.getInt16(index * 2, true) / 32768
    const source = this.context.createBufferSource()
    source.buffer = buffer
    source.connect(this.context.destination)
    this.nextStart = Math.max(this.nextStart, this.context.currentTime)
    source.start(this.nextStart)
    this.nextStart += buffer.duration
    this.sources.add(source)
    source.onended = () => this.sources.delete(source)
  }

  stop(): void {
    this.sources.forEach((source) => source.stop())
    this.sources.clear()
    this.nextStart = 0
  }

  close(): void {
    this.stop()
    void this.context?.close()
    this.context = null
  }
}
