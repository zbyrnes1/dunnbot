from dunnbot.scores import DeficitTracker, pens_deficit


def game(gid=1, state="LIVE", home="PIT", away="PHI", hs=0, as_=0):
    return {
        "id": gid,
        "gameState": state,
        "homeTeam": {"abbrev": home, "score": hs},
        "awayTeam": {"abbrev": away, "score": as_},
    }


def board(*games):
    return {"games": list(games)}


def test_deficit_home_and_away():
    assert pens_deficit(game(hs=1, as_=3)) == 2
    assert pens_deficit(game(home="NYR", away="PIT", hs=4, as_=2)) == 2
    assert pens_deficit(game(hs=3, as_=1)) == -2


def test_ignores_non_live_and_other_teams():
    assert pens_deficit(game(state="FINAL", hs=0, as_=2)) is None
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
