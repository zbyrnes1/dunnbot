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

## Free hosting: GitHub Actions (default)
`.github/workflows/dunnbot.yml` runs hourly from about 10am to 10pm ET. Each run
checks the scoreboard and exits within seconds unless the Pens are live or face
off within ~100 minutes; then it stays connected until the final horn. Free
because the repo is public; the token lives in encrypted repo secrets.

Setup (phone works): repo **Settings → Secrets and variables → Actions → New
repository secret**, add `DISCORD_TOKEN` and `DUNNBOT_CHANNEL_ID`. Test any time
from **Actions → dunnbot → Run workflow** (exits quickly if there's no game).

Caveats: GitHub can start scheduled runs 5-15 min late, and it pauses schedules
in a repo with no commits for 60 days (it emails you first; re-enable from the
Actions tab). If a run dies mid-game, the next hourly run resumes it and may
repost if the Pens are down 2 at that moment.

## Paid alternative: Railway
1. railway.com → sign in with GitHub → New Project → Deploy from GitHub repo → `dunnbot`.
2. Service → Variables: add `DISCORD_TOKEN` and `DUNNBOT_CHANNEL_ID`.
3. It redeploys automatically; check Deployments → logs for `logged in as`.
   `railway.json` sets the start command and restarts it if it ever crashes.

## Tests
```sh
uv run pytest
```
