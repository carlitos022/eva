import logging
import threading
from collections import defaultdict


log = logging.getLogger(__name__)


class EventBus:
    """Bus de eventos local, ligero y seguro entre hilos."""

    def __init__(self):
        self._lock = threading.RLock()
        self._subscribers = defaultdict(list)

    def subscribe(self, event_name, callback):
        if not event_name or not callable(callback):
            return
        with self._lock:
            self._subscribers[event_name].append(callback)

    def publish(self, event_name, payload=None):
        with self._lock:
            callbacks = list(self._subscribers.get(event_name, []))

        for callback in callbacks:
            try:
                callback(payload or {})
            except Exception:
                log.exception("Error en suscriptor de evento %s", event_name)
