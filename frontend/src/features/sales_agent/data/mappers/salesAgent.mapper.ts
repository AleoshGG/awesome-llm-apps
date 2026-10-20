import type { AgentTranscriptMessageEntity } from '../../domain/entities/salesAgent.entity'
import type { SalesAgentServerEventDto } from '../models/salesAgent.dto'

export const SalesAgentMapper = {
  transcriptToDomain(
    dto: Extract<SalesAgentServerEventDto, { type: 'transcript' }>,
    timestamp: string,
  ): AgentTranscriptMessageEntity {
    return {
      id: dto.id,
      speaker: dto.speaker,
      text: dto.text,
      final: dto.final,
      timestamp,
    }
  },
}
