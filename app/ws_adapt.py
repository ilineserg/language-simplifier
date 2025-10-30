import json
from typing import AsyncIterator

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from .security import verify_init_data
from .settings import settings
from .providers import openai_adapt_stream, ProviderError


async def ws_adapt_handler(ws: WebSocket) -> None:
    """Main WebSocket handler: verifies Telegram init data, adapts text via OpenAI, and streams tokens."""
    await ws.accept()

    async def send(event_type: str, data: str | None = None, seq: int | None = None) -> None:
        """Safely send structured messages to the WebSocket client."""
        if ws.application_state == WebSocketState.CONNECTED:
            await ws.send_text(json.dumps({"type": event_type, "data": data, "seq": seq}))

    try:
        # Receive and parse the initial JSON message from the client
        raw = await ws.receive_text()
        init = json.loads(raw)

        init_data = init.get("init_data", "")
        if not verify_init_data(init_data, bot_token=settings.bot_token):
            await send("error", "invalid init_data")
            await ws.close(code=1008)
            return

        # Validate input payload
        source_type = init.get("source_type", "text")
        payload = init.get("payload", "")
        level = init.get("level", "B1")

        if source_type != "text" or not payload:
            await send("error", "only source_type=text with non-empty payload supported")
            await ws.close(code=1003)
            return

        if not settings.openai_api_key:
            await send("error", "OpenAI API key not configured")
            await ws.close(code=1011)
            return

    except Exception as e:
        await send("error", f"bad init message: {e}")
        await ws.close(code=1003)
        return

    # --- text adaptation stream ---
    await send("start", "stream-begin")
    seq = 0

    try:
        # Initialize asynchronous OpenAI token stream
        agen: AsyncIterator[str] = openai_adapt_stream(
            text=payload,
            level=level,
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            mode="simplify",
            batch_interval_ms=settings.token_delay_ms,
        )

        # Stream tokens to the client
        async for token in agen:
            await send("token", token, seq)
            seq += 1

        await send("end", "stream-end", seq)

    except WebSocketDisconnect:
        # Client closed the connection
        pass
    except ProviderError as e:
        await send("error", f"provider error: {e}")
    except Exception as e:
        await send("error", f"internal error: {e}")
    finally:
        if ws.application_state == WebSocketState.CONNECTED:
            await ws.close()
