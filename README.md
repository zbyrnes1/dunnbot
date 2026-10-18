# DunnBot

Discord bot that posts **"Pens defense is embarrassing"** whenever the Pittsburgh
Penguins fall behind by exactly 2 goals in a live game.


## How it works
- Polls the public NHL scoreboard (`https://api-web.nhle.com/v1/score/now`) every 60s.
- Fires when the opponent scores to put PIT down exactly 2 (e.g. 2-1 → 3-1).
  A Pens goal that cuts a bigger deficit to 2 (4-1 → 4-2) does **not** fire.
  Staying down 2 doesn't repeat.
- State is in memory, so a restart mid-game while already down 2 will post once more.

## Setup
1. Discord Developer Portal → New Application → name it **DunnBot** → Bot → Reset Token.
2. OAuth2 → URL Generator: scope `bot`, permission `Send Messages`. Open the URL to invite it.
3. In Discord, enable Developer Mode, right-click the target channel → Copy Channel ID.
4. Run:
   ```sh
   uv sync            # or: pip install -e .
   export DISCORD_TOKEN=...          # never commit this
   export DUNNBOT_CHANNEL_ID=123456789012345678
   uv run dunnbot
   ```
   Optional: `DUNNBOT_POLL_SECS` (default 60, minimum 30).

## Deploy on Railway (works from a phone)
1. railway.com → sign in with GitHub → New Project → Deploy from GitHub repo → `dunnbot`.
2. Service → Variables: add `DISCORD_TOKEN` and `DUNNBOT_CHANNEL_ID`.
3. It redeploys automatically; check Deployments → logs for `logged in as`.
   `railway.json` sets the start command and restarts it if it ever crashes.

## Tests
```sh
uv run pytest
```
