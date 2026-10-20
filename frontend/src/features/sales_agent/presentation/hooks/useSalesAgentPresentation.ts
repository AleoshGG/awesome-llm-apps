import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { SalesAgentRepositoryImpl } from '../../data/repositories/salesAgent.repository.impl'
import { imageToBase64, MicrophoneCapture, PcmAudioQueue, validateImage } from '../../data/services/liveMedia'
import type { AgentConnectionPhase, AgentTranscriptMessageEntity } from '../../domain/entities/salesAgent.entity'
import { initialSalesAgentState, salesAgentReducer, type UiCommand } from '../state/salesAgentState'

type ImageType = 'image/jpeg' | 'image/png' | 'image/webp'

export interface UseSalesAgentPresentationReturn {
  isOpen: boolean
  phase: AgentConnectionPhase
  isMicActive: boolean
  isCameraActive: boolean
  cameraStream: MediaStream | null
  visualSearchActive: boolean
  statusMessage: string | null
  draftText: string
  messages: AgentTranscriptMessageEntity[]
  uiCommand: UiCommand | null
  toggleWidget: () => void
  closeWidget: () => void
  endSession: () => void
  toggleMic: () => void
  toggleCamera: () => void
  captureCamera: (video: HTMLVideoElement) => void
  selectImage: (file: File) => void
  retryConnection: () => void
  setDraftText: (value: string) => void
  sendUserMessage: (customText?: string) => void
}

export function useSalesAgentPresentation(): UseSalesAgentPresentationReturn {
  const [isOpen, setIsOpen] = useState(false)
  const [isMicActive, setIsMicActive] = useState(false)
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null)
  const [draftText, setDraftText] = useState('')
  const [state, dispatch] = useReducer(salesAgentReducer, initialSalesAgentState)
  const repository = useRef(new SalesAgentRepositoryImpl())
  const microphone = useRef(new MicrophoneCapture())
  const player = useRef(new PcmAudioQueue())
  const camera = useRef<MediaStream | null>(null)
  const connected = useRef(false)

  const stopMedia = useCallback(() => {
    microphone.current.stop()
    player.current.stop()
    camera.current?.getTracks().forEach((track) => track.stop())
    camera.current = null
    setCameraStream(null)
    setIsMicActive(false)
  }, [])

  useEffect(() => repository.current.subscribe((event) => {
    if (event.type === 'audio') void player.current.enqueue(event.data)
    if (event.type === 'interrupted') player.current.stop()
    dispatch(event)
  }, (expected) => {
    connected.current = false
    if (!expected) {
      stopMedia()
      dispatch({ type: 'error', message: 'La conexión se cerró. Puedes volver a intentarlo.' })
    }
  }), [stopMedia])

  useEffect(() => {
    const currentRepository = repository.current
    const currentPlayer = player.current
    const handlePageHide = () => {
      stopMedia()
      currentRepository.disconnect()
    }
    window.addEventListener('pagehide', handlePageHide)
    return () => {
      window.removeEventListener('pagehide', handlePageHide)
      stopMedia()
      currentPlayer.close()
      currentRepository.disconnect()
    }
  }, [stopMedia])

  const connect = useCallback(() => {
    dispatch({ type: 'local_phase', phase: 'connecting' })
    if (connected.current) {
      repository.current.resume()
      return
    }
    void repository.current.connect().then(() => {
      connected.current = true
    }).catch((error: unknown) => {
      dispatch({ type: 'error', message: error instanceof Error ? error.message : 'No pudimos conectar.' })
    })
  }, [])

  const closeWidget = useCallback(() => {
    setIsOpen(false)
    stopMedia()
    if (connected.current) repository.current.pause()
  }, [stopMedia])

  const toggleWidget = () => {
    if (isOpen) closeWidget()
    else {
      setIsOpen(true)
      connect()
    }
  }

  const endSession = () => {
    stopMedia()
    repository.current.disconnect()
    connected.current = false
    setIsOpen(false)
    setDraftText('')
    dispatch({ type: 'reset' })
  }

  const toggleMic = () => {
    if (isMicActive) {
      microphone.current.stop()
      setIsMicActive(false)
      dispatch({ type: 'local_phase', phase: 'ready' })
      return
    }
    void microphone.current.start((chunk) => repository.current.sendAudioChunk(chunk)).then(() => {
      setIsMicActive(true)
      dispatch({ type: 'local_phase', phase: 'listening' })
    }).catch(() => dispatch({ type: 'error', message: 'Activa el permiso del micrófono para hablar.' }))
  }

  const toggleCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop())
      camera.current = null
      setCameraStream(null)
      return
    }
    void navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } } }).then((stream) => {
      camera.current = stream
      setCameraStream(stream)
    })
      .catch(() => dispatch({ type: 'error', message: 'Activa el permiso de cámara para tomar una foto.' }))
  }

  const sendImage = (blob: Blob) => {
    if (state.visualSearchActive) return
    try { validateImage(blob) } catch (error) {
      dispatch({ type: 'error', message: error instanceof Error ? error.message : 'Imagen inválida.' })
      return
    }
    void imageToBase64(blob).then((base64) => repository.current.sendImage(blob.type as ImageType, base64))
  }

  const captureCamera = (video: HTMLVideoElement) => {
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d')?.drawImage(video, 0, 0)
    canvas.toBlob((blob) => { if (blob) sendImage(blob) }, 'image/jpeg', 0.88)
  }

  const sendUserMessage = (customText?: string) => {
    const content = (customText ?? draftText).trim()
    if (!content || state.phase === 'connecting' || state.phase === 'paused') return
    repository.current.sendText(content)
    if (!customText) setDraftText('')
  }

  return {
    isOpen, phase: state.phase, isMicActive, isCameraActive: cameraStream !== null,
    cameraStream, visualSearchActive: state.visualSearchActive, statusMessage: state.statusMessage,
    draftText, messages: state.messages, uiCommand: state.uiCommand, toggleWidget, closeWidget,
    endSession, toggleMic, toggleCamera, captureCamera, selectImage: sendImage,
    retryConnection: connect, setDraftText, sendUserMessage,
  }
}
