import logging
import queue
import threading
import time

from config import (
    ARCHIVIST_ENABLED,
    ARCHIVIST_IDLE_DELAY,
    ARCHIVIST_QUEUE_SIZE,
)


log = logging.getLogger(__name__)


class PostTurnArchivist:
    """Consolida aprendizaje despues de responder, fuera del turno visible."""

    def __init__(self, cortex, llm, events):
        self.cortex = cortex
        self.llm = llm
        self.events = events
        self.enabled = ARCHIVIST_ENABLED
        self._queue = queue.Queue(maxsize=max(1, ARCHIVIST_QUEUE_SIZE))
        self._thread = None
        self._lock = threading.Lock()
        self.processed = 0
        self.failed = 0
        self.last_error = ""

    def _ensure_worker(self):
        if not self.enabled:
            return
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(
                target=self._run,
                name="eva-archivist",
                daemon=True,
            )
            self._thread.start()

    def submit(
        self,
        user_message,
        assistant_message,
        source_message_id=None,
    ):
        if not self.enabled:
            return False

        self._ensure_worker()

        payload = {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "source_message_id": source_message_id,
        }

        try:
            self._queue.put_nowait(payload)
            return True
        except queue.Full:
            self.failed += 1
            self.last_error = "Cola del Archivist llena."
            return False

    def _run(self):
        while True:
            payload = self._queue.get()
            try:
                if ARCHIVIST_IDLE_DELAY > 0:
                    time.sleep(ARCHIVIST_IDLE_DELAY)

                archive = self.llm.archive_turn(
                    payload["user_message"],
                    payload["assistant_message"],
                )
                counters = self.cortex.apply_archive(
                    archive,
                    payload.get("source_message_id"),
                )
                self.processed += 1
                self.last_error = ""
                self.events.publish(
                    "post_turn_archived",
                    {"counters": counters},
                )
            except Exception as exc:
                self.failed += 1
                self.last_error = str(exc)
                log.exception("Archivist no pudo consolidar el turno")
                try:
                    self.cortex.store.log_internal_event(
                        "archivist_error",
                        str(exc)[:500],
                        0.4,
                    )
                except Exception:
                    log.exception("No se pudo registrar archivist_error")
            finally:
                self._queue.task_done()

    def status(self):
        return {
            "enabled": self.enabled,
            "queued": self._queue.qsize(),
            "processed": self.processed,
            "failed": self.failed,
            "last_error": self.last_error,
            "worker_alive": bool(
                self._thread and self._thread.is_alive()
            ),
        }
