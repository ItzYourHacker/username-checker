import aiohttp
import asyncio
import itertools
import random
import json
import os
from typing import List, Optional
from utils.stats import Stats
from utils.config import INPUT_DIR, BASE_DIR


class TokenPool:
    def __init__(self, tokens: List[str]):
        self._tokens = tokens
        self._cycle = itertools.cycle(tokens) if tokens else None
        self._lock = asyncio.Lock()

    async def next(self) -> Optional[str]:
        if not self._cycle:
            return None
        async with self._lock:
            return next(self._cycle)

    @property
    def valid_count(self) -> int:
        return len(self._tokens)


class ProxyPool:
    def __init__(self, proxies: List[str], enabled: bool = True):
        self._proxies = list(proxies)
        self._enabled = enabled and bool(proxies)
        self._cycle = itertools.cycle(proxies) if proxies else None
        self._lock = asyncio.Lock()
        self._failed = set()

    async def next(self) -> Optional[str]:
        if not self._enabled or not self._cycle:
            return None
        async with self._lock:
            for _ in range(len(self._proxies)):
                proxy = next(self._cycle)
                if proxy not in self._failed:
                    return self._format(proxy)
        return None

    def remove(self, proxy: str):
        raw = proxy.replace("http://", "").replace("https://", "").replace("socks5://", "")
        self._failed.add(raw)

    @staticmethod
    def _format(proxy: str) -> str:
        if proxy.startswith(("http://", "https://", "socks5://")):
            return proxy
        try:
            if "@" in proxy:
                auth_part, host_part = proxy.rsplit("@", 1)
                host, port = host_part.rsplit(":", 1)
            else:
                parts = proxy.split(":")
                if len(parts) == 4:
                    host = parts[0]
                    port = parts[1]
                    user = parts[2]
                    password = parts[3]
                    auth_part = f"{user}:{password}"
                elif len(parts) == 2:
                    host, port = parts
                    auth_part = None
                else:
                    return f"http://{proxy}"

            protocol = "socks5" if port == "1080" else "http"

            if auth_part:
                return f"{protocol}://{auth_part}@{host}:{port}"
            else:
                return f"{protocol}://{host}:{port}"
        except Exception:
            return f"http://{proxy}"

    @property
    def active_count(self) -> int:
        return len(self._proxies) - len(self._failed)


HEADERS_BASE = {
    "authority":       "discord.com",
    "accept":          "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type":    "application/json",
    "origin":          "https://discord.com",
    "referer":         "https://discord.com/channels/@me",
    "user-agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


INVALID_USERNAME_CODES = {
    "BASE_TYPE_BAD_LENGTH",
    "USERNAME_INVALID_CHARACTERS",
    "USERNAME_TOO_MANY_USERS",
    "BASE_TYPE_CHOICES",
    "BASE_TYPE_REQUIRED",
    "USERNAME_INVALID",
}


def _parse_result(status_code: int, body: dict):
    if status_code == 400:
        msg = body.get("message", "")
        if msg == "Invalid Form Body":
            errors = body.get("errors", {})
            username_errs = errors.get("username", {})
            err_list = username_errs.get("_errors", [])
            for e in err_list:
                if isinstance(e, dict):
                    code = e.get("code", "")
                    if code == "USERNAME_ALREADY_TAKEN":
                        return "taken", ""
                    if code in INVALID_USERNAME_CODES:
                        return "invalid", code
            errors_str = json.dumps(errors)
            if "USERNAME_ALREADY_TAKEN" in errors_str:
                return "taken", ""
            if any(c in errors_str for c in INVALID_USERNAME_CODES):
                return "invalid", "bad_format"
            return "error", f"unhandled_400: {errors_str[:120]}"

    if status_code == 200:
        taken = body.get("taken")
        if taken is True:
            return "taken", ""
        if taken is False:
            return "available", ""

    if status_code == 429:
        return "rate_limited", str(body.get("retry_after", "1"))

    if status_code == 401:
        return "unauthorized", ""

    if status_code == 403:
        return "forbidden", ""

    return "error", f"status_{status_code}"



class UsernameChecker:
    URL = "https://discord.com/api/v9/users/@me/pomelo-attempt"

    def __init__(self, config):
        self.config = config
        self.stats = Stats()
        self.token_pool = TokenPool(config.tokens)
        self.proxy_pool = ProxyPool(config.proxies, config.use_proxies)
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._results = []
        self._available_lock = asyncio.Lock()
        self._on_result = None
        self._stop_event = asyncio.Event()

    async def start(self):
        connector = aiohttp.TCPConnector(
            limit=self.config.threads * 2,
            limit_per_host=0,
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
            force_close=False,
        )
        self._session = aiohttp.ClientSession(connector=connector)
        self._semaphore = asyncio.Semaphore(self.config.threads)

    async def stop(self):
        if self._session:
            await self._session.close()

    def on_result(self, callback):
        self._on_result = callback

    async def check_batch(self, usernames: List[str]) -> List[dict]:
        tasks = [self._check_worker(u) for u in usernames]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict)]

    async def _check_worker(self, username: str) -> dict:
        if self._stop_event.is_set():
            return {"username": username, "status": "skipped"}

        async with self._semaphore:
            if self.config.delay > 0:
                await asyncio.sleep(self.config.delay * random.uniform(0.8, 1.2))

            result = await self._check_single(username)

            if self._on_result:
                await self._on_result(result)

            return result

    async def _check_single(self, username: str, retries: int = 15) -> dict:
        last_reason = ""

        for attempt in range(retries):
            token = await self.token_pool.next()
            if not token:
                await asyncio.sleep(1)
                self.stats.record_check("error")
                return {"username": username, "status": "error", "detail": "no_valid_token"}

            proxy = await self.proxy_pool.next()
            headers = dict(HEADERS_BASE)
            headers["authorization"] = token

            try:
                request_kwargs = dict(
                    headers=headers,
                    json={"username": username},
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                )
                if proxy:
                    request_kwargs["proxy"] = proxy

                async with self._session.request("POST", self.URL, **request_kwargs) as resp:
                    try:
                        body = await resp.json(content_type=None)
                    except Exception:
                        body = {}

                    result = _parse_result(resp.status, body)
                    if isinstance(result, tuple):
                        parsed, detail = result
                    else:
                        parsed, detail = result, ""

                    if parsed == "available":
                        self.stats.record_check("available")
                        return {"username": username, "status": "available"}

                    if parsed == "taken":
                        self.stats.record_check("taken")
                        return {"username": username, "status": "taken"}

                    if parsed == "invalid":
                        self.stats.record_check("error")
                        return {"username": username, "status": "invalid", "detail": detail}

                    if parsed == "rate_limited":
                        self.stats.record_retry()
                        last_reason = "rate_limited"
                        try:
                            retry_after = float(detail) if detail else body.get("retry_after", 1.0)
                        except Exception:
                            retry_after = 1.0
                        await asyncio.sleep(retry_after + 0.5)
                        continue

                    if parsed == "unauthorized":
                        self.stats.record_retry()
                        last_reason = "unauthorized"
                        await asyncio.sleep(1)
                        continue

                    if parsed == "forbidden":
                        self.stats.record_retry()
                        last_reason = "forbidden"
                        await asyncio.sleep(1)
                        continue

                    self.stats.record_check("error")
                    return {"username": username, "status": "error", "code": resp.status, "detail": detail}

            except aiohttp.ClientProxyConnectionError:
                if proxy:
                    self.proxy_pool.remove(proxy)
                self.stats.record_retry()
                last_reason = "proxy_failed"
                continue
            except (aiohttp.ClientError, asyncio.TimeoutError):
                self.stats.record_retry()
                last_reason = "timeout"
                if attempt < retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                continue
            except Exception:
                self.stats.record_retry()
                last_reason = "exception"
                continue

        self.stats.record_check("error")
        return {"username": username, "status": "error", "detail": last_reason}

    async def validate_tokens(self) -> List[str]:
        valid = []
        for token in self.config._tokens:
            try:
                headers = dict(HEADERS_BASE)
                headers["authorization"] = token
                async with self._session.request(
                    "POST", self.URL,
                    json={"username": ""},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    try:
                        body = await resp.json(content_type=None)
                    except Exception:
                        body = {}
                    body_str = json.dumps(body)
                    if resp.status == 401:
                        continue
                    if "retry_after" in body:
                        valid.append(token)
                        continue
                    if any(k in body_str for k in ("USERNAME_ALREADY_TAKEN", "BASE_TYPE_BAD_LENGTH", "PASSWORD_DOES_NOT_MATCH", "taken")):
                        valid.append(token)
            except Exception:
                continue
        return valid

    async def test_proxies(self) -> List[str]:
        working = []
        for proxy in self.config._proxies:
            formatted = ProxyPool._format(proxy)
            try:
                async with self._session.get(
                    "https://discord.com/api/v9/gateway",
                    proxy=formatted,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        working.append(proxy)
            except Exception:
                continue
        return working

    def request_stop(self):
        self._stop_event.set()

    async def save_available(self, username: str):
        async with self._available_lock:
            with open(os.path.join(BASE_DIR, "available.txt"), "a") as f:
                f.write(f"{username}\n")
