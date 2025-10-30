import asyncio
import logging
import signal
import sys
import time
from dataclasses import dataclass
from typing import Optional
import contextlib

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from app.settings import settings


# -------------------- logging --------------------
def setup_logging(level: int | str = logging.INFO) -> None:
    """Configure unified logging for the bot."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
    # aiogram is very verbose in DEBUG; keep INFO for production
    logging.getLogger("aiogram").setLevel(logging.INFO)


# -------------------- throttling --------------------
@dataclass
class RateLimit:
    """Rate limiter configuration."""
    window_sec: float = 2.0
    max_hits: int = 3


class SimpleRateLimiter:
    """
    Lightweight in-memory anti-flood limiter.
    Prevents handlers from being triggered more than N times per time window.
    For production scale-out, move to Redis or distributed cache.
    """
    def __init__(self, cfg: RateLimit):
        self.cfg = cfg
        self._hits: dict[tuple[int, str], list[float]] = {}

    def hit(self, user_id: int, key: str) -> bool:
        """Register a hit and return True if allowed."""
        now = time.monotonic()
        k = (user_id, key)
        arr = self._hits.get(k, [])
        # Keep only recent hits within the time window
        arr = [t for t in arr if now - t <= self.cfg.window_sec]
        arr.append(now)
        self._hits[k] = arr
        return len(arr) <= self.cfg.max_hits


rate_limiter = SimpleRateLimiter(RateLimit(window_sec=2.0, max_hits=3))


# -------------------- bot init --------------------
bot = Bot(token=settings.bot_token)
router = Router()
log = logging.getLogger("bot")


# -------------------- keyboards --------------------
def webapp_kb() -> InlineKeyboardMarkup:
    """Generate a keyboard button that opens the WebApp."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="Open Language Simplifier",
                web_app=WebAppInfo(url=f"{settings.public_base_url}/webapp"),
            )
        ]]
    )


# -------------------- handlers --------------------
@router.message(CommandStart())
async def on_start(m: Message) -> None:
    """Handle /start — greets the user and shows the WebApp button."""
    if not rate_limiter.hit(m.from_user.id, "start"):
        return
    await m.answer(
        (
            "Hi there! 👋\n"
            "Open the WebApp and start adapting your text to the desired language level."
        ),
        reply_markup=webapp_kb(),
    )


@router.message(Command("help"))
async def on_help(m: Message) -> None:
    """Handle /help — show available bot commands."""
    if not rate_limiter.hit(m.from_user.id, "help"):
        return
    await m.answer(
        "Available commands:\n"
        "/start — open the WebApp\n"
        "/help — show this help message\n"
        "/ping — check bot availability",
        reply_markup=webapp_kb(),
    )


@router.message(Command("ping"))
async def on_ping(m: Message) -> None:
    """Health check command."""
    if not rate_limiter.hit(m.from_user.id, "ping"):
        return
    try:
        await m.answer("pong ✅")
    except TelegramBadRequest:
        # Rare cases when replying to closed chats or old threads
        pass


# Fallback: reply to any text with WebApp prompt
@router.message(F.text)
async def on_any_text(m: Message) -> None:
    """Default reply for text messages — show the WebApp button."""
    if not rate_limiter.hit(m.from_user.id, "any"):
        return
    await m.answer(
        "Press the button below to open the WebApp inside Telegram:",
        reply_markup=webapp_kb(),
    )


# -------------------- errors --------------------
@router.errors()
async def on_error(event, exception) -> None:  # type: ignore[no-untyped-def]
    """Centralized error logger (can be extended with alerts to Sentry, Logtail, etc.)."""
    upd = getattr(event, "update", None)
    log.exception("Handler error: %s | update=%r", exception, upd)


# -------------------- commands registration --------------------
async def setup_commands(b: Bot) -> None:
    """Register visible bot commands."""
    await b.set_my_commands(
        commands=[
            BotCommand(command="start", description="Open WebApp"),
            BotCommand(command="help", description="Help & commands"),
            BotCommand(command="ping", description="Health check"),
        ]
    )


# -------------------- lifecycle --------------------
async def run_polling() -> None:
    """
    Production-grade polling runner:
    clean initialization, command registration, graceful shutdown.
    """
    dp = Dispatcher()
    dp.include_router(router)

    # Optional: restrict allowed update types (reduces noise)
    allowed_updates = dp.resolve_used_update_types()

    await setup_commands(bot)
    log.info("Starting polling... allowed_updates=%s", allowed_updates)
    try:
        await dp.start_polling(
            bot,
            allowed_updates=allowed_updates,
            handle_signals=False,  # handled manually
        )
    finally:
        log.info("Polling stopped.")


async def shutdown(loop: asyncio.AbstractEventLoop, task: Optional[asyncio.Task] = None) -> None:
    """Gracefully shut down the bot and cancel all pending tasks."""
    log.info("Shutting down bot...")
    try:
        await bot.session.close()
    finally:
        tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task(loop)]
        for t in tasks:
            t.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*tasks, return_exceptions=True)
    log.info("Shutdown complete.")


# -------------------- entrypoint --------------------
def _install_signal_handlers(loop: asyncio.AbstractEventLoop, stopper: asyncio.Event) -> None:
    """Attach OS signal handlers for graceful stop (SIGINT/SIGTERM)."""
    def _handler(signame: str):
        log.info("Got signal %s — stopping...", signame)
        stopper.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _handler, sig.name)


async def main() -> None:
    """Main entrypoint for the Telegram bot process."""
    setup_logging()
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    _install_signal_handlers(loop, stop_event)

    # Optional: health check, metrics, preflight configuration
    log.info("Bot username preflight...")
    me = await bot.get_me()
    log.info("Bot: @%s (%s)", me.username, me.full_name)

    # Start polling and wait for termination signal
    poller = asyncio.create_task(run_polling())
    await stop_event.wait()

    # Gracefully stop
    poller.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await poller

    await shutdown(loop)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
