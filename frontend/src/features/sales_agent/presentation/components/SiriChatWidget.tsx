import { Button, ScrollShadow, Separator } from '@heroui/react'
import type { FormEvent } from 'react'
import type {
  AgentConnectionPhase,
  AgentTranscriptMessageEntity,
} from '../../domain/entities/salesAgent.entity'

interface SiriChatWidgetProps {
  isOpen: boolean
  phase: AgentConnectionPhase
  isMicActive: boolean
  isCameraActive: boolean
  draftText: string
  messages: AgentTranscriptMessageEntity[]
  onClose: () => void
  onToggleMic: () => void
  onToggleCamera: () => void
  onDraftChange: (value: string) => void
  onSendMessage: (customText?: string) => void
}

const QUICK_PROMPTS = [
  'Busco botas para lluvia',
  '¿Qué hay en mi carrito?',
  'Quiero confirmar mi compra',
]

export function SiriChatWidget({
  isOpen,
  phase,
  isMicActive,
  isCameraActive,
  draftText,
  messages,
  onClose,
  onToggleMic,
  onToggleCamera,
  onDraftChange,
  onSendMessage,
}: SiriChatWidgetProps) {
  if (!isOpen) {
    return null
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSendMessage()
  }

  return (
    <aside
      aria-label="Conversación de ayuda en compras"
      className="fixed bottom-22 left-5 z-50 flex w-[calc(100vw-2.5rem)] max-w-[350px] flex-col overflow-hidden rounded-3xl border border-blue-200/90 bg-white/98 shadow-2xl backdrop-blur-xl"
    >
      {/* Cabecera en tonos azules */}
      <div className="bg-blue-950 px-4 py-3.5 text-white">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-7 w-7 shrink-0 items-center justify-center">
              <span className="siri-orb-core h-6 w-6 rounded-full" />
              <span className="siri-orb-glow absolute inset-0.5 rounded-full" />
            </span>
            <div>
              <h2 className="font-display text-xs font-bold tracking-tight text-white">
                Asistente de compras
              </h2>
              <p className="text-[11px] text-blue-200">
                {isMicActive
                  ? 'Escuchando tu voz...'
                  : phase === 'ready'
                    ? 'En línea para ayudarte'
                    : 'Conectando...'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Minimizar chat"
            className="rounded-full p-1 text-blue-200 hover:bg-white/10 hover:text-white cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Controles de Voz y Cámara */}
        <div className="mt-3 flex items-center gap-2">
          <button
            type="button"
            onClick={onToggleMic}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-xl px-2.5 py-1.5 text-xs font-semibold transition-colors cursor-pointer ${
              isMicActive
                ? 'bg-blue-500 text-white'
                : 'bg-white/12 text-blue-100 hover:bg-white/20'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isMicActive ? 'bg-white animate-ping' : 'bg-sky-300'
              }`}
            />
            {isMicActive ? 'Silenciar voz' : 'Hablar'}
          </button>

          <button
            type="button"
            onClick={onToggleCamera}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-xl px-2.5 py-1.5 text-xs font-semibold transition-colors cursor-pointer ${
              isCameraActive
                ? 'bg-blue-600 text-white'
                : 'bg-white/12 text-blue-100 hover:bg-white/20'
            }`}
          >
            <span>📷</span>
            {isCameraActive ? 'Cámara activa' : 'Mostrar cámara'}
          </button>
        </div>

        {isCameraActive && (
          <div className="mt-2.5 flex items-center justify-between rounded-xl border border-blue-400/40 bg-blue-900/70 px-3 py-2 text-[11px] text-blue-100">
            <span>Apunta al producto que deseas buscar</span>
            <span className="h-2 w-2 rounded-full bg-sky-300 animate-pulse" />
          </div>
        )}
      </div>

      {/* Historial de conversación */}
      <ScrollShadow className="max-h-[300px] min-h-[230px] space-y-3 overflow-y-auto bg-blue-50/30 p-3.5">
        {messages.map((msg) => {
          const isUser = msg.speaker === 'user'

          return (
            <div
              key={msg.id}
              className={`flex flex-col ${
                isUser ? 'items-end' : 'items-start'
              } space-y-1`}
            >
              <div
                className={`max-w-[86%] rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed ${
                  isUser
                    ? 'rounded-br-xs bg-blue-600 text-white'
                    : 'rounded-bl-xs border border-blue-100 bg-white text-slate-800 shadow-2xs'
                }`}
              >
                <p>{msg.text}</p>
              </div>

              <span className="px-1 text-[10px] text-slate-400">
                {isUser ? 'Tú' : 'Asistente'} · {msg.timestamp}
              </span>
            </div>
          )
        })}
      </ScrollShadow>

      <Separator />

      {/* Sugerencias rápidas */}
      <div className="flex gap-1.5 overflow-x-auto bg-white px-3 pt-2.5 pb-1">
        {QUICK_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onSendMessage(prompt)}
            className="shrink-0 rounded-full border border-blue-100 bg-blue-50/50 px-2.5 py-1 text-[11px] font-medium text-blue-800 hover:border-blue-400 hover:bg-blue-50 cursor-pointer"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Entrada de texto */}
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2 bg-white p-3"
      >
        <input
          type="text"
          value={draftText}
          onChange={(event) => onDraftChange(event.target.value)}
          placeholder="Escribe tu mensaje..."
          aria-label="Escribe tu mensaje"
          className="flex-1 rounded-xl border border-blue-100 bg-slate-50 px-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:bg-white focus:outline-none"
        />
        <Button
          type="submit"
          size="sm"
          variant="primary"
          isDisabled={draftText.trim().length === 0}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          Enviar
        </Button>
      </form>
    </aside>
  )
}
