import type { AgentConnectionPhase } from '../../domain/entities/salesAgent.entity'

interface SiriFloatingButtonProps {
  isOpen: boolean
  phase: AgentConnectionPhase
  isMicActive: boolean
  onToggle: () => void
}

const PHASE_LABELS: Record<AgentConnectionPhase, string> = {
  idle: 'En espera',
  connecting: 'Conectando...',
  ready: '¿Necesitas ayuda?',
  listening: 'Escuchando...',
  speaking: 'Respondiendo...',
  paused: 'Sesión en pausa',
  error: 'Sin conexión',
}

export function SiriFloatingButton({
  isOpen,
  phase,
  isMicActive,
  onToggle,
}: SiriFloatingButtonProps) {
  const isAnimated = isMicActive || phase === 'listening' || phase === 'speaking'

  return (
    <div className={`fixed bottom-20 left-4 z-50 items-center gap-2.5 sm:bottom-5 sm:left-5 ${isOpen ? 'hidden sm:flex' : 'flex'}`}>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-label={
          isOpen
            ? 'Cerrar ventana de conversación'
            : 'Abrir asistente de compras'
        }
        className="group relative flex items-center gap-3 rounded-full border border-blue-900/20 bg-blue-950/95 py-2 pl-2 pr-4 text-white shadow-xl backdrop-blur-md transition-transform duration-200 hover:scale-103 active:scale-98 cursor-pointer"
      >
        {/* Blue Iridescent Siri Orb */}
        <span className="relative flex h-11 w-11 items-center justify-center rounded-full">
          <span
            aria-hidden="true"
            className="siri-orb-halo absolute inset-0 rounded-full"
          />
          <span
            aria-hidden="true"
            className={`siri-orb-core relative h-9 w-9 rounded-full shadow-inner ${
              isAnimated ? 'siri-orb-core--active' : ''
            }`}
          />
          <span
            aria-hidden="true"
            className="siri-orb-glow pointer-events-none absolute inset-1 rounded-full"
          />
          <span
            aria-hidden="true"
            className="relative z-10 h-2.5 w-2.5 rounded-full bg-white/95 shadow-xs"
          />
        </span>

        <span className="flex flex-col text-left pr-0.5">
          <span className="flex items-center gap-1.5 text-xs font-bold tracking-tight text-white">
            Asistente
            <span
              className={`h-2 w-2 rounded-full ${
                isMicActive ? 'bg-sky-300 animate-ping' : 'bg-blue-400'
              }`}
            />
          </span>
          <span className="text-[11px] font-medium text-blue-200">
            {isOpen ? 'Ocultar chat' : PHASE_LABELS[phase]}
          </span>
        </span>
      </button>
    </div>
  )
}
