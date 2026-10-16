import json
import os
import sys
from dataclasses import dataclass, field
from typing import List


def _get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = _get_base_dir()
INPUT_DIR = os.path.join(BASE_DIR, "input")


@dataclass
class Config:
    threads: int = 120
    delay: float = 0.1
    webhook: str = ""
    use_proxies: bool = False
    timeout: int = 10
    username_length: int = 4
    username_count: int = 1000
    charset: str = "letters+digits"
    mode: str = "random"
    pattern: str = "a1a1"
    wordlist_file: str = "wordlist.txt"
    rps_limit: int = 0
    auto_save_interval: int = 30
    resume: bool = False

    _tokens: List[str] = field(default_factory=list, repr=False)
    _proxies: List[str] = field(default_factory=list, repr=False)
    _valid_tokens: List[str] = field(default_factory=list, repr=False)

    @classmethod
    def _ensure_input_dir(cls):
        os.makedirs(INPUT_DIR, exist_ok=True)
        config_path = os.path.join(INPUT_DIR, "config.json")
        if not os.path.exists(config_path):
            defaults = cls()
            defaults.save()
        for name in ("tokens.txt", "proxies.txt"):
            p = os.path.join(INPUT_DIR, name)
            if not os.path.exists(p):
                open(p, "w").close()

    @classmethod
    def load(cls) -> "Config":
        cls._ensure_input_dir()
        cfg = cls()
        config_path = os.path.join(INPUT_DIR, "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
        cfg._tokens = cls._load_lines(os.path.join(INPUT_DIR, "tokens.txt"))
        cfg._proxies = cls._load_lines(os.path.join(INPUT_DIR, "proxies.txt"))
        return cfg

    def save(self):
        config_path = os.path.join(INPUT_DIR, "config.json")
        data = {
            "threads": self.threads,
            "delay": self.delay,
            "webhook": self.webhook,
            "use_proxies": self.use_proxies,
            "timeout": self.timeout,
            "username_length": self.username_length,
            "username_count": self.username_count,
            "charset": self.charset,
            "mode": self.mode,
            "pattern": self.pattern,
            "wordlist_file": self.wordlist_file,
            "rps_limit": self.rps_limit,
            "auto_save_interval": self.auto_save_interval,
            "resume": self.resume,
        }
        os.makedirs(INPUT_DIR, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def _load_lines(path: str) -> List[str]:
        if not os.path.exists(path):
            return []
        with open(path, "r") as f:
            return [line.strip() for line in f if line.strip()]

    @property
    def tokens(self) -> List[str]:
        return self._valid_tokens if self._valid_tokens else self._tokens

    @tokens.setter
    def tokens(self, value: List[str]):
        self._valid_tokens = value

    @property
    def proxies(self) -> List[str]:
        return self._proxies

    @proxies.setter
    def proxies(self, value: List[str]):
        self._proxies = value
