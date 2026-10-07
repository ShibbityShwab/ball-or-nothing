"""Tests for the event stream.

This file exists because the event stream rotted silently through the 5x3 rewrite: it
imported a class that no longer existed, and nothing failed because no test imported it.
The event stream is the contract between the RGS and the frontend, so it gets its own
coverage rather than being checked incidentally.

The rules the frontend depends on:
  * one sequential index per simulation, starting at 0
  * a reveal first, a finalWin last
  * win positions that follow the payline the win was actually scored on
"""

from __future__ import annotations

import pytest

from typing import Tuple

from ball_or_nothing import config as cfg
from ball_or_nothing.events import (
    FINAL_WIN,
    FREESPIN_END,
    FREESPIN_UPDATE,
    FS_TRIGGER,
    REVEAL,
    SET_TOTAL_WIN,
    UPDATE_GLOBAL_MULT,
    WIN_INFO,
    WIN_LEVELS,
    build_book,
    build_events,
    win_level,
    win_positions,
)
from ball_or_nothing.spinner import BonusRound, LineWin, SpinOutcome, count_scatters, spin


def _a_bonus_round() -> Tuple[int, SpinOutcome, BonusRound]:
    for sim_id in range(6000):
        outcome = spin(sim_id)
        if outcome.bonus is not None:
            return sim_id, outcome, outcome.bonus
    pytest.fail("no bonus round found in 6000 sims")


def _a_base_win() -> Tuple[int, SpinOutcome]:
    for sim_id in range(6000):
        outcome = spin(sim_id)
        if outcome.is_win and outcome.bonus is None:
            return sim_id, outcome
    pytest.fail("no base win found in 6000 sims")


class TestEventSequence:
    def test_indices_are_sequential_from_zero(self) -> None:
        for sim_id in range(400):
            events = build_events(spin(sim_id))
            assert [e["index"] for e in events] == list(range(len(events))), sim_id

    def test_indices_stay_sequential_across_a_bonus_round(self) -> None:
        # A bonus round once restarted the counter at zero, which would make the frontend
        # play the events out of order.
        _sim, outcome, _bonus = _a_bonus_round()
        events = build_events(outcome)
        assert [e["index"] for e in events] == list(range(len(events)))

    def test_every_round_opens_with_a_reveal_and_closes_with_final_win(self) -> None:
        for sim_id in range(200):
            events = build_events(spin(sim_id))
            assert events[0]["type"] == REVEAL
            assert events[-1]["type"] == FINAL_WIN

    def test_final_win_matches_the_round_payout(self) -> None:
        for sim_id in range(200):
            outcome = spin(sim_id)
            assert build_events(outcome)[-1]["amount"] == pytest.approx(outcome.payout_multiplier)

    def test_total_win_always_precedes_final_win(self) -> None:
        for sim_id in range(200):
            events = build_events(spin(sim_id))
            assert events[-2]["type"] == SET_TOTAL_WIN
            assert events[-2]["amount"] == pytest.approx(events[-1]["amount"])

    def test_every_event_has_an_index_and_a_type(self) -> None:
        for sim_id in range(300):
            for event in build_events(spin(sim_id)):
                assert isinstance(event["index"], int)
                assert isinstance(event["type"], str) and event["type"]


class TestReveal:
    def test_board_shape_matches_the_game(self) -> None:
        event = build_events(spin(0))[0]
        board = event["board"]
        assert len(board) == cfg.NUM_REELS
        for reel in board:
            assert len(reel) == cfg.NUM_ROWS

    def test_every_position_carries_a_symbol_name(self) -> None:
        event = build_events(spin(0))[0]
        names = {cell["name"] for reel in event["board"] for cell in reel}
        assert names <= set(cfg.SYMBOLS)

    def test_game_type_is_labelled(self) -> None:
        assert build_events(spin(0))[0]["gameType"] == cfg.GAME_TYPE


class TestWinInfo:
    def test_a_base_win_reports_at_least_one_line(self) -> None:
        _sim, outcome = _a_base_win()
        info = [e for e in build_events(outcome) if e["type"] == WIN_INFO]
        assert info, "a winning round must emit winInfo"
        assert len(info[0]["wins"]) >= 1

    def test_win_total_matches_the_round(self) -> None:
        _sim, outcome = _a_base_win()
        info = [e for e in build_events(outcome) if e["type"] == WIN_INFO][0]
        assert info["totalWin"] == pytest.approx(outcome.base_payout)

    def test_positions_follow_the_payline_that_scored(self) -> None:
        # The frontend highlights exactly these coordinates, so a wrong row lights up a
        # symbol that did not pay.
        for sim_id in range(400):
            outcome = spin(sim_id)
            if not outcome.is_win or outcome.bonus:
                continue
            for win in outcome.wins:
                rows = cfg.PAYLINES[win.line_index]
                expected = [{"reel": r, "row": rows[r]} for r in range(win.kind)]
                assert win_positions(win) == expected
            return
        pytest.fail("no base win found in 400 sims")

    def test_positions_never_exceed_the_reel_count(self) -> None:
        for sim_id in range(400):
            outcome = spin(sim_id)
            for win in outcome.wins:
                assert len(win_positions(win)) <= cfg.NUM_REELS

    def test_losing_rounds_emit_no_win_info(self) -> None:
        for sim_id in range(400):
            outcome = spin(sim_id)
            if outcome.is_win or outcome.bonus:
                continue
            assert not [e for e in build_events(outcome) if e["type"] == WIN_INFO]
            return
        pytest.fail("no losing round found in 400 sims")


class TestBonusEvents:
    def test_free_spin_lines_sum_to_the_reported_total(self) -> None:
        # These did NOT, once: `win` carried the raw unmultiplied line value while
        # `totalWin` carried the multiplied one, so a UI rendering the breakdown showed a
        # total that contradicted its own lines.
        for sim_id in range(8000):
            outcome = spin(sim_id)
            if outcome.bonus is None:
                continue
            for event in build_events(outcome):
                if event["type"] != WIN_INFO or not event["wins"]:
                    continue
                m = event["wins"][0]["meta"]["multiplier"]
                if m <= 1:
                    continue
                total = sum(w["win"] for w in event["wins"])
                assert total == pytest.approx(event["totalWin"]), (
                    f"sim {sim_id}: lines sum to {total}, totalWin says {event['totalWin']}"
                )
                for w in event["wins"]:
                    assert w["win"] == pytest.approx(w["meta"]["winWithoutMult"] * m)
                return
        pytest.fail("no multiplied free-spin winInfo found")

    def test_trigger_reports_the_scatter_count_and_award(self) -> None:
        _sim, outcome, bonus = _a_bonus_round()
        trigger = [e for e in build_events(outcome) if e["type"] == FS_TRIGGER][0]
        assert trigger["scatters"] == count_scatters(outcome.board)
        assert trigger["spins"] == bonus.start_spins

    def test_one_freespin_update_per_spin(self) -> None:
        _sim, outcome, bonus = _a_bonus_round()
        updates = [e for e in build_events(outcome) if e["type"] == FREESPIN_UPDATE]
        assert len(updates) == bonus.spin_count
        assert [u["currentSpin"] for u in updates] == list(range(1, len(updates) + 1))

    def test_bonus_is_closed_with_a_freespin_end(self) -> None:
        _sim, outcome, bonus = _a_bonus_round()
        end = [e for e in build_events(outcome) if e["type"] == FREESPIN_END][0]
        assert end["totalWin"] == pytest.approx(bonus.total)
        assert end["finalMultiplier"] == bonus.final_multiplier

    def test_multiplier_updates_only_ever_climb(self) -> None:
        for sim_id in range(4000):
            outcome = spin(sim_id)
            if outcome.bonus is None:
                continue
            seen = 1
            for event in build_events(outcome):
                if event["type"] == UPDATE_GLOBAL_MULT:
                    assert event["multiplier"] > seen
                    seen = event["multiplier"]
            return
        pytest.fail("no bonus round found")

    def test_free_reveals_are_labelled_as_freegame(self) -> None:
        _sim, outcome, _bonus = _a_bonus_round()
        reveals = [e for e in build_events(outcome) if e["type"] == REVEAL]
        assert reveals[0]["gameType"] == cfg.GAME_TYPE
        assert all(r["gameType"] == cfg.FREEGAME_TYPE for r in reveals[1:])

    def test_bonus_round_emits_one_reveal_per_spin_plus_the_trigger(self) -> None:
        _sim, outcome, bonus = _a_bonus_round()
        reveals = [e for e in build_events(outcome) if e["type"] == REVEAL]
        assert len(reveals) == bonus.spin_count + 1


class TestNoWagerInTheStream:
    """The wager is gone and its events must never reappear.

    A mid-round player decision cannot be settled by a pre-computed book, so any
    bypassOffer/bypassResult in the stream would be theatre the platform cannot honour.
    """

    def test_no_bypass_events_are_ever_emitted(self) -> None:
        for sim_id in range(4000):
            outcome = spin(sim_id)
            types = {e["type"] for e in build_events(outcome)}
            assert "bypassOffer" not in types
            assert "bypassResult" not in types
            if outcome.bonus:
                return
        pytest.fail("no bonus round found")


class TestBookEntry:
    def test_book_has_the_sdk_shape(self) -> None:
        book = build_book(spin(0))
        assert set(book) == {"id", "payoutMultiplier", "events", "criteria", "baseGameWins", "freeGameWins"}

    def test_book_id_matches_the_simulation(self) -> None:
        assert build_book(spin(77))["id"] == 77

    def test_book_splits_base_and_free_wins(self) -> None:
        _sim, outcome, bonus = _a_bonus_round()
        book = build_book(outcome)
        assert book["freeGameWins"] == pytest.approx(bonus.total)
        assert book["payoutMultiplier"] == pytest.approx(outcome.payout_multiplier)

    def test_book_payout_matches_the_final_win_event(self) -> None:
        for sim_id in range(200):
            book = build_book(spin(sim_id))
            assert book["payoutMultiplier"] == pytest.approx(book["events"][-1]["amount"])


class TestWinLevel:
    def test_levels_escalate_with_size(self) -> None:
        assert win_level(0) == 0
        assert win_level(1) < win_level(25)
        assert win_level(25) < win_level(200)
        assert win_level(200) < win_level(4000)

    def test_zero_is_the_lowest_tier(self) -> None:
        assert win_level(0) == 0
        assert win_level(0.5) == 0

    def test_a_top_prize_lands_in_the_highest_tier(self) -> None:
        # The ladder has to sit above the paytable's ceiling, or a five-of-a-kind gets the
        # second-best celebration.
        assert win_level(cfg.Paytable().five_ball) == max(tier for _threshold, tier in WIN_LEVELS)

    def test_the_ladder_climbs_monotonically(self) -> None:
        thresholds = [threshold for threshold, _tier in WIN_LEVELS]
        assert thresholds == sorted(thresholds)
        assert thresholds[0] == 0.0
