import logging
from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from src.features.sales_agent.domain.entities.agent_event_entity import AgentError
from src.features.sales_agent.domain.exceptions import ProviderConnectionError
from src.features.sales_agent.domain.usecases.sales_agent_run_session_usecase import SalesAgentRunSessionUseCase
from src.features.sales_agent.presentation.sales_agent_dependencies import get_sales_agent
from src.features.sales_agent.presentation.websocket_client_channel_adapter import (
    InvalidClientMessageError, WebSocketClientChannelAdapter,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/sales-agent")
async def sales_agent_socket(
    websocket: WebSocket,
    usecase: Annotated[SalesAgentRunSessionUseCase, Depends(get_sales_agent)],
) -> None:
    # Same-origin browsers and non-browser clients are sufficient for this demo.
    origin = websocket.headers.get("origin")
    expected_origin = f"{'https' if websocket.url.scheme == 'wss' else 'http'}://{websocket.headers.get('host')}"
    if origin is not None and origin != expected_origin:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    channel = WebSocketClientChannelAdapter(websocket)
    code = 1000
    error = None
    try:
        await usecase.execute(channel)
    except WebSocketDisconnect:
        return
    except InvalidClientMessageError as exc:
        code, error = 1008, str(exc)
    except ProviderConnectionError as exc:
        code, error = 1011, str(exc)
    except TimeoutError:
        code, error = 1000, "La sesión alcanzó su límite de 20 minutos. Inicia otra conexión."
    except Exception:
        logger.exception("Sales agent session failed")
        code, error = 1011, "La sesión no pudo continuar. No se reintentaron operaciones automáticamente."
    finally:
        with suppress(WebSocketDisconnect, RuntimeError, OSError):
            if error:
                await channel.send(AgentError(error))
            await websocket.close(code=code)
