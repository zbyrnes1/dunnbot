from datetime import UTC, datetime

from dunnbot.scores import DeficitTracker, pens_deficit, pens_game_over, should_run


def game(gid=1, state="LIVE", home="PIT", away="PHI", hs=0, as_=0, start="2026-10-18T23:00:00Z"):
    return {
        "id": gid,
        "gameState": state,
        "startTimeUTC": start,
        "homeTeam": {"abbrev": home, "score": hs},
        "awayTeam": {"abbrev": away, "score": as_},
    }


def board(*games):
    return {"games": list(games)}


def test_deficit_home_and_away():
    assert pens_deficit(game(hs=1, as_=3)) == 2
    assert pens_deficit(game(home="NYR", away="PIT", hs=4, as_=2)) == 2
    assert pens_deficit(game(hs=3, as_=1)) == -2


def test_ignores_unstarted_and_other_teams():
    assert pens_deficit(game(state="FUT")) is None
    assert pens_deficit(game(home="NYR", away="BOS", hs=0, as_=2)) is None
    assert pens_deficit(game(state="CRIT", hs=0, as_=2)) == 2


def test_fires_when_opponent_makes_it_two_down():
    t = DeficitTracker()
    assert t.update(board(game(hs=1, as_=2))) == []  # down 1
    assert t.update(board(game(hs=1, as_=3))) == [1]  # 3-1: fires
    assert t.update(board(game(hs=1, as_=3))) == []  # still down 2: no repeat
    assert t.update(board(game(hs=1, as_=4))) == []  # down 3


def test_pens_goal_cutting_deficit_to_two_does_not_fire():
    t = DeficitTracker()
    t.update(board(game(hs=1, as_=3)))
    t.update(board(game(hs=1, as_=4)))
    assert t.update(board(game(hs=2, as_=4))) == []  # 4-1 -> 4-2: no fire
    assert t.update(board(game(hs=3, as_=4))) == []  # down 1
    assert t.update(board(game(hs=3, as_=5))) == [1]  # opponent makes it 5-3


def test_fires_when_first_seen_already_down_two():
    assert DeficitTracker().update(board(game(hs=1, as_=3))) == [1]


def test_tracks_games_independently():
    t = DeficitTracker()
    assert t.update(board(game(gid=1, as_=2), game(gid=2, home="NYR", away="BOS", as_=2))) == [1]


def at(hhmm):
    h, m = map(int, hhmm.split(":"))
    return datetime(2026, 10, 18, h, m, tzinfo=UTC)


def test_should_run_window():
    pre = board(game(state="FUT"))  # puck drop 23:00 UTC
    assert not should_run(pre, at("21:19"))  # 101 min out
    assert should_run(pre, at("21:20"))  # 100 min out
    assert should_run(board(game(state="PRE")), at("22:50"))
    assert should_run(board(game(state="LIVE")), at("23:30"))


def test_should_not_run_without_live_pens_game():
    assert not should_run(board(), at("22:00"))
    assert not should_run(board(game(home="NYR", away="BOS", state="FUT")), at("22:30"))
    assert not should_run(board(game(state="FINAL")), at("22:30"))
    assert not should_run(board(game(state="OFF")), at("22:30"))


def test_game_over():
    assert not pens_game_over(board(game(state="LIVE")))
    assert not pens_game_over(board(game(state="FUT")))
    assert pens_game_over(board(game(state="FINAL")))
    assert pens_game_over(board())


def test_late_goal_seen_only_at_final_fires():
    t = DeficitTracker()
    assert t.update(board(game(state="CRIT", hs=1, as_=2))) == []
    assert t.update(board(game(state="FINAL", hs=1, as_=3))) == [1]  # empty-netter
    assert t.update(board(game(state="OFF", hs=1, as_=3))) == []


def test_finished_game_never_seen_live_is_ignored():
    assert DeficitTracker().update(board(game(state="FINAL", hs=1, as_=3))) == []
