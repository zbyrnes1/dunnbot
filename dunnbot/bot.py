"""DunnBot: posts "Pens defense is embarrassing" when Pittsburgh trails by 2.

Env vars:
  DISCORD_TOKEN       bot token (never commit it)
  DUNNBOT_CHANNEL_ID  channel to post in
  DUNNBOT_POLL_SECS   scoreboard poll interval, default 60 (floor 30)
  DUNNBOT_GAME_MODE   "1" = only run if PIT plays soon, exit at the final
                      horn (used by the GitHub Actions schedule)
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime

import discord
import httpx
from discord.ext import tasks

from dunnbot.scores import (
    MESSAGE,
    SCORE_URL,
    DeficitTracker,
    pens_game_over,
    should_run,
)

log = logging.getLogger("dunnbot")


class DunnBot(discord.Client):
    def __init__(self, channel_id: int, poll_secs: float, game_mode: bool = False) -> None:
        super().__init__(intents=discord.Intents.default())
        self.channel_id = channel_id
        self.game_mode = game_mode
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
        if self.game_mode and pens_game_over(scoreboard):
            log.info("PIT game over; exiting")
            # close() cancels this loop, so run it outside the loop's task.
            self._closer = asyncio.create_task(self.close())

    @poll.before_loop
    async def _wait_ready(self) -> None:
        await self.wait_until_ready()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    token = os.environ["DISCORD_TOKEN"]
    channel_id = int(os.environ["DUNNBOT_CHANNEL_ID"])
    poll_secs = max(30.0, float(os.environ.get("DUNNBOT_POLL_SECS", "60")))
    game_mode = os.environ.get("DUNNBOT_GAME_MODE") == "1"
    if game_mode:
        scoreboard = httpx.get(SCORE_URL, follow_redirects=True, timeout=15).json()
        if not should_run(scoreboard, datetime.now(UTC)):
            log.info("no PIT game live or starting soon; exiting")
            return
    DunnBot(channel_id, poll_secs, game_mode).run(token, log_handler=None)


if __name__ == "__main__":
    main()
