import aiohttp
import asyncio
from datetime import datetime


class WebhookSender:
    def __init__(self, webhook_url: str):
        self.url = webhook_url
        self._session = None
        self._queue = asyncio.Queue()
        self._running = False

    async def start(self):
        if not self.url:
            return
        self._session = aiohttp.ClientSession()
        self._running = True
        asyncio.create_task(self._worker())

    async def stop(self):
        self._running = False
        if self._session:
            await self._session.close()

    async def send(self, username: str):
        if not self.url:
            return
        await self._queue.put(username)

    async def _worker(self):
        while self._running:
            try:
                username = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            payload = {
                "embeds": [{
                    "title": "CYBORG Username Found",
                    "color": 0x00FF88,
                    "fields": [
                        {"name": "Username", "value": f"`{username}`", "inline": True},
                        {"name": "Timestamp", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), "inline": True},
                        {"name": "Tool", "value": "CYBORG Username Checker", "inline": False},
                    ],
                    "footer": {"text": "Powered By CyborG"},
                }]
            }

            for attempt in range(3):
                try:
                    async with self._session.post(self.url, json=payload) as resp:
                        if resp.status == 204:
                            break
                        if resp.status == 429:
                            retry_after = (await resp.json()).get("retry_after", 1)
                            await asyncio.sleep(retry_after)
                        else:
                            break
                except Exception:
                    await asyncio.sleep(1)

    async def send_summary(self, stats_dict: dict):
        if not self.url or not self._session:
            return

        payload = {
            "embeds": [{
                "title": "CYBORG Session Summary",
                "color": 0x5865F2,
                "fields": [
                    {"name": "Checked", "value": str(stats_dict["checked"]), "inline": True},
                    {"name": "Available", "value": str(stats_dict["available"]), "inline": True},
                    {"name": "Taken", "value": str(stats_dict["taken"]), "inline": True},
                    {"name": "Errors", "value": str(stats_dict["errors"]), "inline": True},
                    {"name": "Speed", "value": f"{stats_dict['speed']} req/s", "inline": True},
                    {"name": "Duration", "value": f"{stats_dict['elapsed']}s", "inline": True},
                ],
                "footer": {"text": "CYBORG v1.0 - Session Complete"},
            }]
        }

        try:
            async with self._session.post(self.url, json=payload) as resp:
                pass
        except Exception:
            pass
