"""Windows asyncio compatibility helpers for AI Video Assistant."""
import asyncio
import sys

def configure_windows_asyncio():
    """Use SelectorEventLoop on Windows to avoid Proactor socket cleanup noise."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
