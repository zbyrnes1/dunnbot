"""Penguins deficit tracking against the public NHL scoreboard.

Pure logic lives here (no Discord import) so it can be tested offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

SCORE_URL = "https://api-web.nhle.com/v1/score/now"
TEAM = "PIT"
TRIGGER_DEFICIT = 2
MESSAGE = "Pens defense is embarrassing"

# api-web gameState values while the puck is (or recently was) in play.
# CRIT = final minutes / OT of a live game.
LIVE_STATES = {"LIVE", "CRIT"}
DONE_STATES = {"FINAL", "OFF"}

# Game mode (GitHub Actions): an hourly job only stays up if PIT's game is
# live or starts within this window. 100 min covers an hourly cron that
# fires late, while wait + a long OT game stays under the 6h job limit.
START_WINDOW = timedelta(minutes=100)


def pens_game(scoreboard: dict) -> dict | None:
    """Today's PIT game on the scoreboard, if any."""
    for game in scoreboard.get("games", []):
        if TEAM in (game.get("homeTeam", {}).get("abbrev"), game.get("awayTeam", {}).get("abbrev")):
            return game
    return None


def should_run(scoreboard: dict, now: datetime) -> bool:
    """Game mode: is there a PIT game live or starting soon?"""
    game = pens_game(scoreboard)
    if game is None or game.get("gameState") in DONE_STATES:
        return False
    if game.get("gameState") in LIVE_STATES:
        return True
    start = datetime.fromisoformat(game["startTimeUTC"])
    return start - now <= START_WINDOW


def pens_game_over(scoreboard: dict) -> bool:
    game = pens_game(scoreboard)
    return game is None or game.get("gameState") in DONE_STATES


def pens_deficit(game: dict) -> int | None:
    """Goals PIT trails by in a live or finished game (negative if leading)."""
    if game.get("gameState") not in LIVE_STATES | DONE_STATES:
        return None
    home, away = game.get("homeTeam", {}), game.get("awayTeam", {})
    if home.get("abbrev") == TEAM:
        pens, opp = home, away
    elif away.get("abbrev") == TEAM:
        pens, opp = away, home
    else:
        return None
    return opp.get("score", 0) - pens.get("score", 0)


@dataclass
class DeficitTracker:
    """Fires when the opponent scores to put PIT down exactly 2.

    Down 1 -> down 2 (e.g. 2-1 -> 3-1) fires. A Pens goal that cuts a bigger
    deficit to 2 (4-1 -> 4-2) does not. Staying down 2 doesn't repeat.
    """

    last: dict[int, int] = field(default_factory=dict)

    def update(self, scoreboard: dict) -> list[int]:
        fired = []
        for game in scoreboard.get("games", []):
            deficit = pens_deficit(game)
            if deficit is None:
                continue
            game_id = game["id"]
            prev = self.last.get(game_id)
            if prev is None and game.get("gameState") in DONE_STATES:
                continue  # finished before we ever saw it live
            # prev None = first sighting of a live game (e.g. bot restart); fire,
            # since we can't tell how the deficit got there. A finished game
            # still counts if we saw it live: catches a late empty-netter that
            # lands between the last live poll and the final horn.
            if deficit == TRIGGER_DEFICIT and (prev is None or prev < TRIGGER_DEFICIT):
                fired.append(game_id)
            self.last[game_id] = deficit
        return fired
