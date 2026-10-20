import { Button, Card, Chip, Separator } from '@heroui/react'
import { useEffect, useState } from 'react'

type ServiceStatus = 'checking' | 'online' | 'offline'

const STATUS_CONFIG: Record<
  ServiceStatus,
  { label: string; color: 'warning' | 'success' | 'danger' }
> = {
  checking: { label: 'Verificando...', color: 'warning' },
  online: { label: 'Operativo', color: 'success' },
  offline: { label: 'Sin conexión', color: 'danger' },
}

async function pingGraphQL(): Promise<boolean> {
  try {
    const response = await fetch('/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: '{ __typename }' }),
    })
    return response.ok
  } catch {
    return false
  }
}

export function App() {
  const [backendStatus, setBackendStatus] = useState<ServiceStatus>('checking')
  const [lastChecked, setLastChecked] = useState<string>('-')
  const [refreshCount, setRefreshCount] = useState(0)

  useEffect(() => {
    let active = true

    void pingGraphQL().then((isOnline) => {
      if (!active) return
      setBackendStatus(isOnline ? 'online' : 'offline')
      setLastChecked(new Date().toLocaleTimeString('es-MX'))
    })

    return () => {
      active = false
    }
  }, [refreshCount])

  const handleRefresh = () => {
    setBackendStatus('checking')
    setRefreshCount((prev) => prev + 1)
  }

  const statusInfo = STATUS_CONFIG[backendStatus]

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-4">
        <Card className="w-full">
          <Card.Header className="flex flex-col items-start gap-1">
            <div className="flex w-full items-center justify-between gap-2">
              <Card.Title className="text-lg font-semibold">
                Live AI Sales Assistant
              </Card.Title>
              <Chip color="success" size="sm" variant="soft">
                <Chip.Label>Frontend Activo</Chip.Label>
              </Chip>
            </div>
            <Card.Description>
              Estado general de la aplicación demo (React + Vite + HeroUI)
            </Card.Description>
          </Card.Header>

          <Separator />

          <Card.Content className="space-y-3 py-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted">Cliente Web (React + Vite)</span>
              <Chip color="success" size="sm" variant="soft">
                <Chip.Label>Operativo</Chip.Label>
              </Chip>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted">UI Kit (HeroUI v3)</span>
              <Chip color="accent" size="sm" variant="soft">
                <Chip.Label>Instalado</Chip.Label>
              </Chip>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted">Backend GraphQL (/graphql)</span>
              <Chip color={statusInfo.color} size="sm" variant="soft">
                <Chip.Label>{statusInfo.label}</Chip.Label>
              </Chip>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted">Endpoint Gemini Live</span>
              <code className="text-xs px-2 py-0.5 rounded bg-surface-secondary">
                /ws/sales-agent
              </code>
            </div>
          </Card.Content>

          <Separator />

          <Card.Footer className="flex items-center justify-between pt-3">
            <span className="text-xs text-muted">
              Última comprobación: {lastChecked}
            </span>
            <Button
              size="sm"
              variant="secondary"
              isDisabled={backendStatus === 'checking'}
              onPress={handleRefresh}
            >
              Verificar estado
            </Button>
          </Card.Footer>
        </Card>
      </div>
    </main>
  )
}

export default App
