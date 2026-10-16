import os
import sys
import random
import string
import ctypes
import threading
from datetime import datetime
from colorama import Fore, Style, init
from pystyle import Colors, Colorate

init(autoreset=True)

PRIMARY = Colors.red_to_yellow
SECONDARY = Colors.cyan_to_blue

BANNER = """
 ██████╗██╗   ██╗██████╗  ██████╗ ██████╗  ██████╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔═══██╗██╔══██╗██╔════╝
██║      ╚████╔╝ ██████╔╝██║   ██║██████╔╝██║  ███╗
██║       ╚██╔╝  ██╔══██╗██║   ██║██╔══██╗██║   ██║
╚██████╗   ██║   ██████╔╝╚██████╔╝██║  ██╗╚██████╔╝
 ╚═════╝   ╚═╝   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═════╝ """


def get_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def show_banner():
    clear()
    width = get_width()
    colored = Colorate.Horizontal(PRIMARY, BANNER.center(width))
    for line in colored.split("\n"):
        print(line.center(width))

    print(Colorate.Horizontal(SECONDARY, "-" * width))
    print(Colorate.Horizontal(PRIMARY, "CYBORG Discord Username Checker".center(width)))
    print(Colorate.Horizontal(SECONDARY, "-" * width))
    print()

def show_menu():
    width = get_width()
    print(Colorate.Horizontal(PRIMARY, "\n  +-----------------------------+"))
    print(Colorate.Horizontal(PRIMARY, "  |      SELECT AN OPTION       |"))
    print(Colorate.Horizontal(PRIMARY, "  +-----------------------------+\n"))
    print(Colorate.Horizontal(SECONDARY, "  [1] Start Username Checker"))
    print(Colorate.Horizontal(SECONDARY, "  [2] Configure Settings"))
    print(Colorate.Horizontal(SECONDARY, "  [3] Validate Tokens"))
    print(Colorate.Horizontal(SECONDARY, "  [4] Test Proxies"))
    print(Colorate.Horizontal(SECONDARY, "  [5] Pattern Builder"))
    print(Colorate.Horizontal(SECONDARY, "  [6] Exit\n"))


def inp(prompt, default=None):
    if default is not None:
        val = input(Colorate.Horizontal(PRIMARY, f" > {prompt} ({default}): ")).strip()
        return val if val else str(default)
    return input(Colorate.Horizontal(PRIMARY, f" > {prompt}: ")).strip()


def show_config_menu(config):
    print()
    print(Colorate.Horizontal(PRIMARY, "  +-----------------------------+"))
    print(Colorate.Horizontal(PRIMARY, "  |      CONFIGURATION          |"))
    print(Colorate.Horizontal(PRIMARY, "  +-----------------------------+\n"))


    config.mode = inp("Gen mode (random/pattern/wordlist)", config.mode)
    config.username_length = int(inp("Username length", config.username_length))
    config.username_count = int(inp("Username count", config.username_count))
    config.threads = int(inp("Concurrency level", config.threads))
    config.delay = float(inp("Delay between requests (s)", config.delay))
    config.charset = inp("Charset (letters/digits/letters+digits/all)", config.charset)

    if config.mode == "pattern":
        config.pattern = inp("Pattern (a=letter, 1=digit)", config.pattern)
    if config.mode == "wordlist":
        config.wordlist_file = inp("Wordlist file path", config.wordlist_file)

    use_px = inp("Use proxies? (y/n)", "y" if config.use_proxies else "n")
    config.use_proxies = use_px.lower() == "y"
    config.timeout = int(inp("Timeout (s)", config.timeout))
    config.webhook = inp("Webhook URL (leave blank to skip)", config.webhook)
    config.rps_limit = int(inp("RPS limit (0=unlimited)", config.rps_limit))
    config.resume = inp("Resume from checkpoint? (y/n)", "y" if config.resume else "n").lower() == "y"

    config.save()
    print(Colorate.Horizontal(SECONDARY, "\n  [+] Configuration saved!\n"))


def show_separator():
    width = get_width()
    print(Colorate.Horizontal(SECONDARY, "-" * width))


def show_stats_block(stats_dict, total):
    progress = 0
    if total > 0:
        progress = round((stats_dict["checked"] / total) * 100, 1)

    width = get_width()
    print(Colorate.Horizontal(SECONDARY, "-" * width))
    print(Colorate.Horizontal(PRIMARY, "  CYBORG Dashboard".center(width)))
    print(Colorate.Horizontal(SECONDARY, "-" * width))

    lines = [
        f"  Checked   : {stats_dict['checked']:<12} Available : {stats_dict['available']}",
        f"  Taken     : {stats_dict['taken']:<12} Errors    : {stats_dict['errors']}",
        f"  Speed     : {stats_dict['speed']} req/s{'':<5} RPM       : {int(stats_dict['rpm'])}",
        f"  Retries   : {stats_dict.get('retries', 0):<12} Progress  : {progress}%",
    ]
    for line in lines:
        print(Colorate.Horizontal(SECONDARY, line))

    print(Colorate.Horizontal(SECONDARY, "-" * width))
    print()


def show_summary(stats_dict, total):
    width = get_width()
    print()
    print(Colorate.Horizontal(SECONDARY, "-" * width))
    print(Colorate.Horizontal(PRIMARY, "  SESSION SUMMARY".center(width)))
    print(Colorate.Horizontal(SECONDARY, "-" * width))

    lines = [
        f"  Total Checked  : {stats_dict['checked']}",
        f"  Available      : {stats_dict['available']}",
        f"  Taken          : {stats_dict['taken']}",
        f"  Errors         : {stats_dict['errors']}",
        f"  Retries        : {stats_dict.get('retries', 0)}",
        f"  Avg Speed      : {stats_dict['speed']} req/s",
        f"  Duration       : {stats_dict['elapsed']}s",
    ]
    for line in lines:
        print(Colorate.Horizontal(SECONDARY, line))

    print(Colorate.Horizontal(SECONDARY, "-" * width))
    print()


def show_pattern_builder():
    print()
    print(Colorate.Horizontal(PRIMARY, "  +-----------------------------+"))
    print(Colorate.Horizontal(PRIMARY, "  |      PATTERN BUILDER        |"))
    print(Colorate.Horizontal(PRIMARY, "  +-----------------------------+\n"))
    print(Colorate.Horizontal(SECONDARY, "  Legend:"))
    print(Colorate.Horizontal(SECONDARY, "    a = random lowercase letter"))
    print(Colorate.Horizontal(SECONDARY, "    1 = random digit"))
    print(Colorate.Horizontal(SECONDARY, "    _ = underscore"))
    print(Colorate.Horizontal(SECONDARY, "    any other char = literal"))
    print()
    print(Colorate.Horizontal(SECONDARY, "  Examples:"))

    examples = ["a1a1", "aa11", "1a1a", "aaa1", "a_a1", "1111"]
    for ex in examples:
        preview = _preview_pattern(ex)
        print(Colorate.Horizontal(SECONDARY, f"    {ex} -> {preview}"))
    print()

    custom = inp("Enter your pattern")
    if custom:
        for _ in range(5):
            print(Colorate.Horizontal(SECONDARY, f"    {_preview_pattern(custom)}"))
    print()


def _preview_pattern(pattern: str) -> str:
    result = []
    for ch in pattern:
        if ch == "a":
            result.append(random.choice(string.ascii_lowercase))
        elif ch == "1":
            result.append(random.choice(string.digits))
        else:
            result.append(ch)
    return "".join(result)


class TitleUpdater:
    def __init__(self, stats_ref):
        self._stats = stats_ref
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        import time
        while self._running:
            try:
                s = self._stats.to_dict()
                ts = datetime.now().strftime("%H:%M:%S")
                title = (
                    f"CYBORG | "
                    f"C {s['checked']} | "
                    f"A {s['available']} | "
                    f"T {s['taken']} | "
                    f"E {s['errors']} | "
                    f"{s['speed']} req/s | "
                    f"{ts}"
                )

                if os.name == "nt":
                    ctypes.windll.kernel32.SetConsoleTitleW(title)
                else:
                    print(f"\033]0;{title}\007", end="", flush=True)

                time.sleep(1)
            except Exception:
                pass
