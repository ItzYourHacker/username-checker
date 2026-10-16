import random
import string
import os
from typing import List


class UsernameGenerator:
    CHARSETS = {
        "letters": string.ascii_lowercase,
        "digits": string.digits,
        "letters+digits": string.ascii_lowercase + string.digits,
        "letters+digits+underscore": string.ascii_lowercase + string.digits + "_",
        "letters+digits+dot": string.ascii_lowercase + string.digits + ".",
        "all": string.ascii_lowercase + string.digits + "_.",
    }

    def __init__(self, length: int = 4, charset: str = "letters+digits",
                 mode: str = "random", pattern: str = "a1a1",
                 wordlist_file: str = "wordlist.txt", custom_chars: str = ""):
        self.length = length
        self.charset_key = charset
        self.mode = mode
        self.pattern = pattern
        self.wordlist_file = wordlist_file
        self.chars = self.CHARSETS.get(charset, charset)
        if custom_chars:
            self.chars += custom_chars

    @staticmethod
    def _is_valid(name: str) -> bool:
        if not name or len(name) < 2:
            return False
        if name.startswith(".") or name.endswith("."):
            return False
        if ".." in name:
            return False
        allowed = set(string.ascii_lowercase + string.digits + "_.")
        return all(c in allowed for c in name)

    def generate(self, count: int) -> List[str]:
        if self.mode == "random":
            return self._random(count)
        elif self.mode == "pattern":
            return self._pattern(count)
        elif self.mode == "wordlist":
            return self._wordlist(count)
        return self._random(count)

    def _random(self, count: int) -> List[str]:
        seen = set()
        results = []
        while len(results) < count:
            name = "".join(random.choices(self.chars, k=self.length))
            if name not in seen and self._is_valid(name):
                seen.add(name)
                results.append(name)
        return results

    def _pattern(self, count: int) -> List[str]:
        seen = set()
        results = []
        while len(results) < count:
            name = self._apply_pattern()
            if name not in seen and self._is_valid(name):
                seen.add(name)
                results.append(name)
        return results

    def _apply_pattern(self) -> str:
        result = []
        for ch in self.pattern:
            if ch == "a":
                result.append(random.choice(string.ascii_lowercase))
            elif ch == "1":
                result.append(random.choice(string.digits))
            elif ch == "_":
                result.append("_")
            elif ch == ".":
                result.append(".")
            else:
                result.append(ch)
        return "".join(result)

    def _wordlist(self, count: int) -> List[str]:
        if not os.path.exists(self.wordlist_file):
            return []
        with open(self.wordlist_file, "r") as f:
            words = [line.strip() for line in f if line.strip()]
        if len(words) > count:
            return random.sample(words, count)
        return words
