import asyncio
import logging
from datetime import datetime, timezone
import os
import signal

from app.gmail.sync import sync_gmail

logger = logging.getLogger(__name__)

# Configurable interval from environment (seconds)
SYNC_INTERVAL_SECONDS = int(os.getenv("GMAIL_SYNC_INTERVAL", "60"))

# Global event to signal shutdown
_stop_event = asyncio.Event()


def _signal_handler(*args):
    logger.info("Received shutdown signal, stopping Gmail worker...")
    _stop_event.set()


async def gmail_worker():
    """
    Continuous Gmail sync worker.
    Runs in background, periodically triggers sync_gmail().
    Stops gracefully when _stop_event is set.
    """
    logger.info("Starting continuous Gmail worker with interval=%s seconds", SYNC_INTERVAL_SECONDS)

    # Register signal handlers once
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    while not _stop_event.is_set():
        start_time = datetime.now(timezone.utc)
        try:
            await sync_gmail()
        except Exception as e:
            logger.exception("Gmail sync encountered an error: %s", e)

        # Sleep until next iteration or until shutdown
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        sleep_time = max(0, SYNC_INTERVAL_SECONDS - elapsed)
        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=sleep_time)
        except asyncio.TimeoutError:
            continue  # timeout expired, run next iteration

    logger.info("Gmail worker stopped gracefully")
