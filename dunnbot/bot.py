"""DunnBot: posts "Pens defense is embarrassing" when Pittsburgh trails by 2.

Env vars:
  DISCORD_TOKEN       bot token (never commit it)
  DUNNBOT_CHANNEL_ID  channel to post in
  DUNNBOT_POLL_SECS   scoreboard poll interval, default 60 (floor 30)
"""

from __future__ import annotations

import logging
import os

import discord
import httpx
from discord.ext import tasks

from dunnbot.scores import MESSAGE, SCORE_URL, DeficitTracker

log = logging.getLogger("dunnbot")


class DunnBot(discord.Client):
    def __init__(self, channel_id: int, poll_secs: float) -> None:
        super().__init__(intents=discord.Intents.default())
        self.channel_id = channel_id
        self.tracker = DeficitTracker()
        self.http_client = httpx.AsyncClient(timeout=15)
        self.poll.change_interval(seconds=poll_secs)

    async def setup_hook(self) -> None:
        self.poll.start()

    async def on_ready(self) -> None:
        log.info("logged in as %s; posting to channel %s", self.user, self.channel_id)

    async def close(self) -> None:
        self.poll.cancel()
        await self.http_client.aclose()
        await super().close()

    @tasks.loop(seconds=60)
    async def poll(self) -> None:
        try:
            resp = await self.http_client.get(SCORE_URL, follow_redirects=True)
            resp.raise_for_status()
            scoreboard = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("scoreboard fetch failed: %s", exc)
            return
        for game_id in self.tracker.update(scoreboard):
            log.info("PIT down 2 in game %s", game_id)
            channel = self.get_channel(self.channel_id) or await self.fetch_channel(
                self.channel_id
            )
            await channel.send(MESSAGE)

    @poll.before_loop
    async def _wait_ready(self) -> None:
        await self.wait_until_ready()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    token = os.environ["DISCORD_TOKEN"]
    channel_id = int(os.environ["DUNNBOT_CHANNEL_ID"])
    poll_secs = max(30.0, float(os.environ.get("DUNNBOT_POLL_SECS", "60")))
    DunnBot(channel_id, poll_secs).run(token, log_handler=None)


if __name__ == "__main__":
    main()
