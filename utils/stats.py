import time
import threading
import json
import os
import sys
from dataclasses import dataclass, field


def _get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_BASE = _get_base_dir()


@dataclass
class Stats:
    checked: int = 0
    available: int = 0
    taken: int = 0
    errors: int = 0
    retries: int = 0
    start_time: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _checkpoint_file: str = os.path.join(_BASE, "checkpoint.json")

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def speed(self) -> float:
        elapsed = self.elapsed
        if elapsed <= 0:
            return 0.0
        return self.checked / elapsed

    @property
    def rpm(self) -> float:
        return self.speed * 60

    def record_check(self, status: str):
        with self._lock:
            self.checked += 1
            if status == "available":
                self.available += 1
            elif status == "taken":
                self.taken += 1
            else:
                self.errors += 1

    def record_retry(self):
        with self._lock:
            self.retries += 1

    def to_dict(self) -> dict:
        return {
            "checked": self.checked,
            "available": self.available,
            "taken": self.taken,
            "errors": self.errors,
            "retries": self.retries,
            "speed": round(self.speed, 1),
            "rpm": round(self.rpm, 0),
            "elapsed": round(self.elapsed, 1),
        }

    def save_checkpoint(self, remaining: list):
        data = {
            "stats": self.to_dict(),
            "remaining": remaining,
        }
        with open(self._checkpoint_file, "w") as f:
            json.dump(data, f)

    @classmethod
    def load_checkpoint(cls, path: str = None):
        if path is None:
            path = os.path.join(_BASE, "checkpoint.json")
        if not os.path.exists(path):
            return None, []
        with open(path, "r") as f:
            data = json.load(f)
        stats = cls()
        for k, v in data.get("stats", {}).items():
            if hasattr(stats, k) and k not in ("speed", "rpm", "elapsed"):
                setattr(stats, k, v)
        return stats, data.get("remaining", [])
