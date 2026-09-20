import threading
import time

from config import (
    AUTONOMY_ENABLED,
    HEARTBEAT_ENABLED,
    HEARTBEAT_INTERVAL,
)


class HeartbeatEngine:
    """
    Pulso cognitivo controlado.

    En v0.4 no ejecuta acciones externas. Solo publica estado para preparar
    la autonomia posterior. Esta desactivado por defecto.
    """

    def __init__(self, cortex, events):
        self.cortex = cortex
        self.events = events
        self.enabled = HEARTBEAT_ENABLED
        self.autonomy_enabled = AUTONOMY_ENABLED
        self.interval = max(15, HEARTBEAT_INTERVAL)
        self._thread = None
        self._stop = threading.Event()
        self.cycles = 0
        self.last_cycle_at = None

    def start(self):
        if not self.enabled:
            return False
        if self._thread and self._thread.is_alive():
            return True

        self._thread = threading.Thread(
            target=self._run,
            name="eva-heartbeat",
            daemon=True,
        )
        self._thread.start()
        return True

    def _run(self):
        while not self._stop.wait(self.interval):
            self.cycles += 1
            self.last_cycle_at = time.time()
            payload = {
                "cycle": self.cycles,
                "goals": len(self.cortex.store.get_active_goals(20)),
                "tasks": len(self.cortex.get_tasks(20)),
                "autonomy_enabled": self.autonomy_enabled,
                "action": "NO_OP",
            }
            self.events.publish("heartbeat", payload)

    def stop(self):
        self._stop.set()

    def status(self):
        return {
            "enabled": self.enabled,
            "autonomy_enabled": self.autonomy_enabled,
            "interval_seconds": self.interval,
            "cycles": self.cycles,
            "last_cycle_at": self.last_cycle_at,
            "running": bool(
                self._thread and self._thread.is_alive()
            ),
        }
