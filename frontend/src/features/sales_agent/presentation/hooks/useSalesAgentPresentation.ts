import { useState } from 'react'
import { INITIAL_AGENT_MESSAGES } from '../../../../core/mocks/mockStoreData'
import type {
  AgentConnectionPhase,
  AgentTranscriptMessageEntity,
} from '../../domain/entities/salesAgent.entity'

export interface UseSalesAgentPresentationReturn {
  isOpen: boolean
  phase: AgentConnectionPhase
  isMicActive: boolean
  isCameraActive: boolean
  draftText: string
  messages: AgentTranscriptMessageEntity[]
  openWidget: () => void
  closeWidget: () => void
  toggleWidget: () => void
  toggleMic: () => void
  toggleCamera: () => void
  setDraftText: (value: string) => void
  sendUserMessage: (customText?: string) => void
}

/**
 * Hook de gestión de estado de presentación para el botón flotante estilo Siri
 * y el panel lateral izquierdo de conversación.
 */
export function useSalesAgentPresentation(): UseSalesAgentPresentationReturn {
  const [isOpen, setIsOpen] = useState<boolean>(false)
  const [phase, setPhase] = useState<AgentConnectionPhase>('ready')
  const [isMicActive, setIsMicActive] = useState<boolean>(false)
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false)
  const [draftText, setDraftText] = useState<string>('')
  const [messages, setMessages] = useState<AgentTranscriptMessageEntity[]>(
    INITIAL_AGENT_MESSAGES,
  )

  const openWidget = () => setIsOpen(true)
  const closeWidget = () => setIsOpen(false)
  const toggleWidget = () => setIsOpen((prev) => !prev)

  const toggleMic = () => {
    setIsMicActive((prev) => {
      const next = !prev
      setPhase(next ? 'listening' : 'ready')
      return next
    })
  }

  const toggleCamera = () => {
    setIsCameraActive((prev) => !prev)
  }

  const sendUserMessage = (customText?: string) => {
    const content = (customText ?? draftText).trim()
    if (!content) return

    const nowLabel = new Date().toLocaleTimeString('es-MX', {
      hour: '2-digit',
      minute: '2-digit',
    })

    const userMsg: AgentTranscriptMessageEntity = {
      id: `usr-${Date.now()}`,
      speaker: 'user',
      text: content,
      final: true,
      timestamp: nowLabel,
    }

    const simulatedReply: AgentTranscriptMessageEntity = {
      id: `agt-${Date.now() + 1}`,
      speaker: 'agent',
      text: `Con gusto te ayudo con "${content}". Enseguida reviso las opciones disponibles en la tienda.`,
      final: true,
      timestamp: nowLabel,
    }

    setMessages((current) => [...current, userMsg, simulatedReply])
    if (!customText) {
      setDraftText('')
    }
  }

  return {
    isOpen,
    phase,
    isMicActive,
    isCameraActive,
    draftText,
    messages,
    openWidget,
    closeWidget,
    toggleWidget,
    toggleMic,
    toggleCamera,
    setDraftText,
    sendUserMessage,
  }
}
