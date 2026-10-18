"""Penguins deficit tracking against the public NHL scoreboard.

Pure logic lives here (no Discord import) so it can be tested offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SCORE_URL = "https://api-web.nhle.com/v1/score/now"
TEAM = "PIT"
TRIGGER_DEFICIT = 2
MESSAGE = "Pens defense is embarrassing"

# api-web gameState values while the puck is (or recently was) in play.
# CRIT = final minutes / OT of a live game.
LIVE_STATES = {"LIVE", "CRIT"}


def pens_deficit(game: dict) -> int | None:
    """Goals PIT trails by in a live game (negative if leading), else None."""
    if game.get("gameState") not in LIVE_STATES:
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
            # prev None = first sighting (e.g. bot restart); fire, since we can't
            # tell how the deficit got there.
            if deficit == TRIGGER_DEFICIT and (prev is None or prev < TRIGGER_DEFICIT):
                fired.append(game_id)
            self.last[game_id] = deficit
        return fired
