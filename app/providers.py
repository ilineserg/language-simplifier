import asyncio
from collections.abc import AsyncIterator

from .prompting import build_system_prompt, build_user_prompt


class ProviderError(Exception):
    """Errors raised by LLM providers."""


def _coalesce(source: AsyncIterator[str], interval_ms: int = 120) -> AsyncIterator[str]:
    """
    Coalesce small token strings into ~interval_ms chunks to reduce WS chatter.
    NOTE: generator is async-iterable wrapper around `source`.
    """
    async def _run() -> AsyncIterator[str]:
        buf: list[str] = []
        loop = asyncio.get_running_loop()
        last = loop.time()
        interval = interval_ms / 1000.0

        def flush() -> str | None:
            nonlocal buf
            if not buf:
                return None
            out = "".join(buf)
            buf.clear()
            return out

        async for tok in source:
            buf.append(tok)
            now = loop.time()
            if (now - last) >= interval:
                chunk = flush()
                if chunk:
                    yield chunk
                last = now

        # final flush
        chunk = flush()
        if chunk:
            yield chunk

    # expose as async generator without extra stack frame in call site
    return _run()


def _extract_delta(event) -> str | None:
    """
    Be tolerant to SDK variations:
    - event.choices[0].delta may be dict or an object with .content
    """
    try:
        choice0 = event.choices[0]
        d = getattr(choice0, "delta", None)
        if isinstance(d, dict):
            return d.get("content")
        return getattr(d, "content", None)
    except Exception:
        return None


async def openai_adapt_stream(
    text: str,
    level: str,
    model: str,
    api_key: str,
    mode: str = "simplify",
    batch_interval_ms: int | None = None,  # None → no batching
) -> AsyncIterator[str]:
    """
    Yield adapted text fragments from OpenAI chat.completions (streaming).
    Keeps behavior identical to the previous version, but with cleaner structure.
    """
    try:
        from openai import AsyncOpenAI
    except Exception as e:
        raise ProviderError(f"openai client not available: {e}") from e

    client = AsyncOpenAI(api_key=api_key)

    system = build_system_prompt(level=level, mode=mode)
    user = build_user_prompt(text=text)  # оставляем прежнюю логику

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0.5,
            stream=True,
        )
    except Exception as e:
        raise ProviderError(str(e)) from e

    async def _tokens() -> AsyncIterator[str]:
        try:
            async for event in stream:  # ChatCompletionChunk
                delta = _extract_delta(event)
                if delta:
                    yield delta
        except asyncio.CancelledError:
            # graceful cancellation (client closed WS)
            raise
        except Exception as e:
            # propagate as provider error to the caller
            raise ProviderError(f"stream error: {e}") from e

    src: AsyncIterator[str] = _tokens()
    if batch_interval_ms and batch_interval_ms > 0:
        src = _coalesce(src, interval_ms=batch_interval_ms)

    async for chunk in src:
        yield chunk
