# horace/watcher.py

import asyncio
from pathlib import Path
from typing import NamedTuple, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from joshua_logger import Logger

from horace.catalog import CatalogManager

logger = Logger()

class Event(NamedTuple):
    """Represents a filesystem event to be processed."""
    event_type: str
    src_path: Path
    dest_path: Optional[Path] = None


class CatalogEventHandler(FileSystemEventHandler):
    """
    Handles filesystem events from watchdog and puts them onto an async queue.
    """
    def __init__(self, queue: asyncio.Queue, base_path: Path):
        self.queue = queue
        self.base_path = base_path

    def _should_ignore(self, path_str: str) -> bool:
        """Determines if an event for a given path should be ignored."""
        # Ignore events within Horace's own metadata directory
        if '.horace' in path_str:
            return True
        # Ignore temporary files from common applications
        if path_str.endswith('~') or path_str.endswith('.tmp'):
            return True
        return False

    def on_moved(self, event: FileSystemEvent):
        if event.is_directory or self._should_ignore(event.dest_path):
            return
        # Note: Synchronous handler - logging happens in async processor
        self.queue.put_nowait(Event('moved', Path(event.src_path), Path(event.dest_path)))

    def on_created(self, event: FileSystemEvent):
        # We prefer MOVED_TO/CLOSE_WRITE, but this can be a fallback.
        if event.is_directory or self._should_ignore(event.src_path):
            return
        # Note: Synchronous handler - logging happens in async processor
        self.queue.put_nowait(Event('created', Path(event.src_path)))

    def on_modified(self, event: FileSystemEvent):
        # This event is the closest watchdog gives us to CLOSE_WRITE.
        # It's the primary trigger for updates.
        if event.is_directory or self._should_ignore(event.src_path):
            return
        # Note: Synchronous handler - logging happens in async processor
        self.queue.put_nowait(Event('modified', Path(event.src_path)))

    def on_deleted(self, event: FileSystemEvent):
        if event.is_directory or self._should_ignore(event.src_path):
            return
        # Note: Synchronous handler - logging happens in async processor
        self.queue.put_nowait(Event('deleted', Path(event.src_path)))


class WatcherService:
    """
    The main service that watches the filesystem and processes events.
    """
    def __init__(self, catalog_manager: CatalogManager, watch_path: Path):
        self.catalog = catalog_manager
        self.watch_path = watch_path
        self.queue = asyncio.Queue()

    async def run(self):
        """Starts the watcher and the event processing loop."""
        # Start watchdog observer in a separate thread
        event_handler = CatalogEventHandler(self.queue, self.watch_path)
        observer = Observer()
        observer.schedule(event_handler, str(self.watch_path), recursive=True)
        observer.start()
        await logger.log("INFO", f"File watcher started on '{self.watch_path}'", "horace-watcher")

        try:
            await self._process_events()
        except asyncio.CancelledError:
            await logger.log("INFO", "Watcher service shutting down.", "horace-watcher")
        finally:
            observer.stop()
            observer.join()

    async def _process_events(self):
        """The main async loop that consumes events from the queue."""
        while True:
            try:
                event: Event = await self.queue.get()
                await logger.log("INFO", f"Processing event: {event.event_type} on {event.src_path}", "horace-watcher")

                if event.event_type in ('created', 'modified'):
                    await self.catalog.handle_upsert(event.src_path)
                elif event.event_type == 'deleted':
                    await self.catalog.handle_delete(event.src_path)
                elif event.event_type == 'moved' and event.dest_path:
                    await self.catalog.handle_move(event.src_path, event.dest_path)

                self.queue.task_done()
            except Exception as e:
                await logger.log("ERROR", f"Error processing event {event}: {e}", "horace-watcher", data={"exc_info": True})
