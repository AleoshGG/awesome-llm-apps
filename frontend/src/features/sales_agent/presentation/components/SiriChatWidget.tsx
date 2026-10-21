import { Button, ScrollShadow, Separator } from '@heroui/react'
import { useEffect, useRef, type ChangeEvent, type FormEvent } from 'react'
import { formatCentsToMXN } from '../../../../core/utils/formatters'
import type { ProductDetailEntity } from '../../../products/domain/entities/productDetail.entity'
import type { AgentConnectionPhase, AgentTranscriptMessageEntity } from '../../domain/entities/salesAgent.entity'

interface SiriChatWidgetProps {
  isOpen: boolean
  phase: AgentConnectionPhase
  isMicActive: boolean
  isCameraActive: boolean
  cameraStream: MediaStream | null
  visualSearchActive: boolean
  statusMessage: string | null
  draftText: string
  messages: AgentTranscriptMessageEntity[]
  featuredProduct: ProductDetailEntity | null
  onClose: () => void
  onEndSession: () => void
  onToggleMic: () => void
  onToggleCamera: () => void
  onCaptureCamera: (video: HTMLVideoElement) => void
  onSelectImage: (file: File) => void
  onRetryConnection: () => void
  onDraftChange: (value: string) => void
  onSendMessage: (customText?: string) => void
}

const QUICK_PROMPTS = ['Busco botas para lluvia', '¿Qué hay en mi carrito?', 'Quiero confirmar mi compra']
const STATUS: Record<AgentConnectionPhase, string> = {
  idle: 'Abre el asistente para comenzar', connecting: 'Preparando el asistente…',
  ready: 'En línea para ayudarte', listening: 'Escuchando tu voz…',
  speaking: 'Respondiendo…', paused: 'Sesión en pausa', error: 'Necesita reconectarse',
}

export function SiriChatWidget(props: SiriChatWidgetProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const conversationRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (videoRef.current) videoRef.current.srcObject = props.cameraStream
  }, [props.cameraStream])

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      const conversation = conversationRef.current
      if (props.isOpen && conversation) conversation.scrollTop = conversation.scrollHeight
    })
    return () => window.cancelAnimationFrame(frame)
  }, [props.featuredProduct, props.isOpen, props.messages])

  if (!props.isOpen) return null

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    props.onSendMessage()
  }
  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) props.onSelectImage(file)
    event.target.value = ''
  }

  return (
    <aside aria-label="Conversación de ayuda en compras" className="fixed inset-x-0 bottom-0 z-50 flex h-[92dvh] max-h-[760px] w-full flex-col overflow-hidden rounded-t-[28px] border border-blue-200/90 bg-white/98 shadow-2xl backdrop-blur-xl sm:inset-x-auto sm:bottom-22 sm:left-5 sm:h-auto sm:max-h-[calc(100dvh-7rem)] sm:w-[370px] sm:rounded-3xl">
      <div className="shrink-0 bg-blue-950 px-4 py-3.5 text-white">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-7 w-7 shrink-0 items-center justify-center"><span className="siri-orb-core h-6 w-6 rounded-full" /><span className="siri-orb-glow absolute inset-0.5 rounded-full" /></span>
            <div><h2 className="font-display text-xs font-bold text-white">Asistente de compras</h2><p className="text-[11px] text-blue-200">{STATUS[props.phase]}</p></div>
          </div>
          <button type="button" onClick={props.onClose} aria-label="Minimizar chat" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-blue-200 hover:bg-white/10 hover:text-white cursor-pointer">✕</button>
        </div>

        <div className="mt-3 grid grid-cols-2 gap-2 sm:flex sm:items-center">
          <Button size="sm" variant={props.isMicActive ? 'primary' : 'secondary'} onPress={props.onToggleMic} isDisabled={props.phase === 'connecting' || props.phase === 'error'} className="flex-1">
            {props.isMicActive ? 'Silenciar voz' : 'Hablar'}
          </Button>
          <Button size="sm" variant={props.isCameraActive ? 'primary' : 'secondary'} onPress={props.onToggleCamera} isDisabled={props.visualSearchActive} className="flex-1">
            {props.isCameraActive ? 'Cerrar cámara' : 'Usar cámara'}
          </Button>
          <label className={`col-span-2 cursor-pointer rounded-lg px-2.5 py-2 text-center text-xs font-semibold sm:col-span-1 sm:py-1.5 ${props.visualSearchActive ? 'pointer-events-none opacity-50' : 'bg-white/12 text-blue-100 hover:bg-white/20'}`}>
            Elegir imagen
            <input className="sr-only" type="file" accept="image/jpeg,image/png,image/webp" disabled={props.visualSearchActive} onChange={handleFile} />
          </label>
        </div>

        {props.isCameraActive && (
          <div className="mt-2.5 overflow-hidden rounded-xl border border-blue-400/40 bg-blue-900/70">
            <video ref={videoRef} autoPlay muted playsInline className="aspect-video w-full object-cover" />
            <Button fullWidth size="sm" variant="secondary" isDisabled={props.visualSearchActive} onPress={() => { if (videoRef.current) props.onCaptureCamera(videoRef.current) }}>
              {props.visualSearchActive ? 'Analizando imagen…' : 'Buscar con esta foto'}
            </Button>
          </div>
        )}
      </div>

      {props.statusMessage && (
        <div className="flex items-center justify-between gap-2 border-b border-blue-100 bg-blue-50 px-3 py-2 text-[11px] text-blue-950">
          <span>{props.statusMessage}</span>
          {props.phase === 'error' && <Button size="sm" variant="secondary" onPress={props.onRetryConnection}>Reintentar</Button>}
        </div>
      )}

      <ScrollShadow ref={conversationRef} hideScrollBar className="min-h-0 flex-1 space-y-3 overflow-y-auto bg-blue-50/30 p-3.5 sm:min-h-[220px] sm:max-h-[300px]">
        {props.messages.length === 0 && <p className="mx-auto max-w-56 pt-14 text-center text-xs leading-relaxed text-slate-500">Pregunta por un producto, revisa tu carrito o usa una foto para buscar algo parecido.</p>}
        {props.messages.map((message) => {
          const user = message.speaker === 'user'
          return <div key={message.id} className={`flex flex-col ${user ? 'items-end' : 'items-start'} space-y-1`}>
            <div className={`max-w-[86%] rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed ${user ? 'rounded-br-xs bg-blue-600 text-white' : 'rounded-bl-xs border border-blue-100 bg-white text-slate-800 shadow-2xs'}`}><p>{message.text}</p></div>
            <span className="px-1 text-[10px] text-slate-400">{user ? 'Tú' : 'Asistente'} · {message.timestamp}</span>
          </div>
        })}
        {props.featuredProduct && (() => {
          const product = props.featuredProduct
          const image = product.media.find((item) => item.isMain)?.url ?? product.media[0]?.url
          return (
            <article className="ml-0 max-w-[94%] overflow-hidden rounded-2xl border border-blue-200 bg-white shadow-2xs" aria-label={`Producto encontrado: ${product.name}`}>
              <div className="flex items-center gap-3 p-2.5">
                <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-slate-100 bg-white p-1.5">
                  {image ? <img src={image} alt="" className="max-h-full max-w-full object-contain object-center" /> : <span className="flex h-full items-center justify-center text-[10px] text-slate-400">Sin imagen</span>}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] text-slate-500">Encontré esta opción</p>
                  <p className="text-[10px] font-medium text-blue-700">{product.provider.name}</p>
                  <h3 className="line-clamp-2 text-xs font-bold leading-snug text-slate-900">{product.name}</h3>
                  <p className="mt-1 text-sm font-extrabold text-blue-700 tabular-price">{formatCentsToMXN(product.priceListCents)}</p>
                </div>
              </div>
            </article>
          )
        })()}
      </ScrollShadow>
      <Separator />

      <div className="flex gap-1.5 overflow-x-auto bg-white px-3 pt-2.5 pb-1">
        {QUICK_PROMPTS.map((prompt) => <button key={prompt} type="button" onClick={() => props.onSendMessage(prompt)} className="shrink-0 rounded-full border border-blue-100 bg-blue-50/50 px-2.5 py-1 text-[11px] font-medium text-blue-800 hover:border-blue-400 cursor-pointer">{prompt}</button>)}
      </div>
      <form onSubmit={handleSubmit} className="flex shrink-0 items-center gap-2 bg-white p-3">
        <input type="text" value={props.draftText} onChange={(event) => props.onDraftChange(event.target.value)} placeholder="Escribe tu mensaje…" aria-label="Escribe tu mensaje" className="min-w-0 flex-1 rounded-xl border border-blue-100 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 focus:border-blue-600 focus:bg-white focus:outline-none sm:py-2 sm:text-xs" />
        <Button type="submit" size="sm" variant="primary" isDisabled={!props.draftText.trim() || props.phase === 'connecting' || props.phase === 'error'}>Enviar</Button>
      </form>
      <button type="button" onClick={props.onEndSession} className="shrink-0 border-t border-slate-100 bg-white pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] text-[11px] font-medium text-slate-500 hover:text-blue-700 cursor-pointer">Terminar sesión</button>
    </aside>
  )
}
