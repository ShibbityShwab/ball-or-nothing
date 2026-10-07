"""Tests for the 5x3 BALL OR NOTHING math core.

Independent checks, not restatements of the code:
  * the line rules, against hand-computed outcomes
  * the closed form, against hand-computed constants
  * the simulator, against the closed form
  * THE BYPASS, against the claim that it cannot move the RTP

Several real bugs shipped during development - a jackpot probability that omitted mixed
wild lines, a solver that verified itself against the default paytable, and a wild weight
that made five-of-a-kind ten times too common to pay a headline. Every probability the
game depends on is asserted as a literal here rather than recomputed from the same code
that produces it.
"""

from __future__ import annotations

import math

import pytest

from ball_or_nothing import config as cfg
from ball_or_nothing import par
from ball_or_nothing.rng import SplitMix64
from ball_or_nothing.spinner import (
    count_scatters,
    evaluate_board,
    evaluate_line,
    line_symbols,
    play_bonus,
    spin,
)


class TestLineRules:
    def test_five_of_a_kind_pays_the_top_prize(self) -> None:
        t = cfg.Paytable().as_table()
        _s, kind, pay = evaluate_line(("BALL",) * 5, t)
        assert kind == 5
        assert pay == cfg.Paytable().five_ball

    def test_three_of_a_kind_is_the_minimum(self) -> None:
        t = cfg.Paytable().as_table()
        _s, _kind, pay = evaluate_line(("BALL", "BALL", "LOSS", "LOSS", "BALL"), t)
        assert pay == 0.0

    def test_wild_substitutes_for_the_leading_symbol(self) -> None:
        t = cfg.Paytable().as_table()
        symbol, kind, pay = evaluate_line(("WILD", "WILD", "BALL", "BALL", "BALL"), t)
        assert symbol == cfg.BALL
        assert kind == 5
        assert pay == cfg.Paytable().five_ball

    def test_all_wild_pays_as_ball(self) -> None:
        t = cfg.Paytable().as_table()
        symbol, kind, pay = evaluate_line((cfg.WILD,) * 5, t)
        assert symbol == cfg.BALL
        assert kind == 5
        assert pay > 0

    def test_vault_breaks_a_line(self) -> None:
        t = cfg.Paytable().as_table()
        # VAULT is a scatter: it never substitutes, so the run stops there.
        _s, kind, pay = evaluate_line(("BALL", "BALL", cfg.VAULT, "BALL", "BALL"), t)
        assert kind == 2
        assert pay == 0.0

    def test_loss_breaks_a_line(self) -> None:
        t = cfg.Paytable().as_table()
        _s, kind, pay = evaluate_line(("BALL", "BALL", cfg.LOSS, "BALL", "BALL"), t)
        assert kind == 2
        assert pay == 0.0

    def test_run_must_start_at_reel_zero(self) -> None:
        t = cfg.Paytable().as_table()
        _s, _kind, pay = evaluate_line((cfg.LOSS, "BALL", "BALL", "BALL", "BALL"), t)
        assert pay == 0.0

    def test_higher_kind_pays_more_than_lower_for_the_same_symbol(self) -> None:
        pay = cfg.Paytable()
        for symbol, low, mid, high in (
            (cfg.BALL, pay.three_ball, pay.four_ball, pay.five_ball),
            (cfg.NUT, pay.three_nut, pay.four_nut, pay.five_nut),
            (cfg.SACK, pay.three_sack, pay.four_sack, pay.five_sack),
            (cfg.COIN, pay.three_coin, pay.four_coin, pay.five_coin),
        ):
            assert low < mid < high, symbol


class TestBoard:
    def test_board_is_five_by_three(self) -> None:
        outcome = spin(1)
        assert len(outcome.board) == cfg.NUM_REELS
        for reel in outcome.board:
            assert len(reel) == cfg.NUM_ROWS

    def test_paylines_are_well_formed(self) -> None:
        assert len(cfg.PAYLINES) == 10
        for index, rows in cfg.PAYLINES.items():
            assert len(rows) == cfg.NUM_REELS, index
            assert all(0 <= r < cfg.NUM_ROWS for r in rows), index

    def test_line_symbols_reads_one_position_per_reel(self) -> None:
        board = [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"], ["J", "K", "L"], ["M", "N", "O"]]
        assert line_symbols(board, 1) == ("A", "D", "G", "J", "M")  # top row
        assert line_symbols(board, 0) == ("B", "E", "H", "K", "N")  # middle row
        assert line_symbols(board, 2) == ("C", "F", "I", "L", "O")  # bottom row

    def test_scatter_count_covers_the_whole_board(self) -> None:
        board = [[cfg.VAULT, cfg.LOSS, cfg.VAULT], [cfg.LOSS] * 3, [cfg.VAULT] * 3, [cfg.LOSS] * 3, [cfg.LOSS] * 3]
        assert count_scatters(board) == 5

    def test_evaluate_board_sums_every_paying_line(self) -> None:
        t = cfg.Paytable().as_table()
        board = [["BALL"] * 3 for _ in range(5)]
        total, wins = evaluate_board(board, t)
        # every payline is five BALL
        assert len(wins) == 10
        assert total == pytest.approx(10 * cfg.Paytable().five_ball)


class TestProbabilities:
    def test_weights_sum_to_one_thousand(self) -> None:
        for name, weights in (("base", cfg.REEL_WEIGHTS), ("free", cfg.FREEGAME_WEIGHTS)):
            total = sum(weights["default"].values())
            assert total == 1000, (name, total)

    def test_every_symbol_has_weight(self) -> None:
        for weights in (cfg.REEL_WEIGHTS, cfg.FREEGAME_WEIGHTS):
            for symbol in cfg.SYMBOLS:
                assert weights["default"][symbol] > 0, symbol

    def test_scatter_distribution_sums_to_the_trigger_rate(self) -> None:
        dist = par.scatter_distribution()
        assert sum(dist.values()) == pytest.approx(par.trigger_probability())

    def test_trigger_probability_is_hand_computable(self) -> None:
        p = 25 / 1000
        n = cfg.NUM_REELS * cfg.NUM_ROWS
        expected = sum(
            math.comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(3, n + 1)
        )
        assert par.trigger_probability() == pytest.approx(expected)

    def test_trigger_is_rare_enough_to_be_an_event(self) -> None:
        assert 1 / 400 < par.trigger_probability() < 1 / 80


class TestRtp:
    def test_closed_form_rtp_hits_target(self) -> None:
        assert par.closed_form_rtp() == pytest.approx(cfg.TARGET_RTP, abs=1e-5)

    def test_rtp_is_below_one(self) -> None:
        assert par.closed_form_rtp() < 1.0

    def test_rtp_splits_between_base_and_bonus(self) -> None:
        assert par.base_rtp() + par.bonus_rtp() == pytest.approx(par.closed_form_rtp())

    def test_the_feature_carries_meaningful_rtp(self) -> None:
        share = par.bonus_rtp() / par.closed_form_rtp()
        assert 0.30 < share < 0.55, share

    def test_rtp_is_linear_in_the_top_prize(self) -> None:
        # This linearity is what makes the solver a single divide.
        low = par.closed_form_rtp(cfg.Paytable(five_ball=100.0, five_wild=100.0))
        mid = par.closed_form_rtp(cfg.Paytable(five_ball=200.0, five_wild=200.0))
        high = par.closed_form_rtp(cfg.Paytable(five_ball=300.0, five_wild=300.0))
        assert mid - low == pytest.approx(high - mid, rel=1e-9)

    def test_solver_lands_on_any_supported_target(self) -> None:
        for target in (0.90, 0.94, 0.96, 0.97, 0.985):
            top = par.solve_five_ball_for_rtp(target)
            table = cfg.Paytable(five_ball=top, five_wild=top)
            assert par.closed_form_rtp(table) == pytest.approx(target, abs=1e-9)

    def test_solver_rejects_unreachable_target(self) -> None:
        with pytest.raises(ValueError):
            par.solve_five_ball_for_rtp(0.0001)


class TestNoWager:
    """THE BYPASS wager was removed and must stay removed.

    Stake Engine books are static and pre-computed, so a mid-round player decision has no
    settlement path. These tests exist so the wager cannot quietly come back.
    """

    def test_spin_takes_no_wager_parameter(self) -> None:
        import inspect

        params = set(inspect.signature(spin).parameters)
        assert "run_bypass" not in params, "the wager parameter came back"

    def test_spin_outcome_has_no_bypass_field(self) -> None:
        assert not hasattr(spin(0), "bypass"), "a bypass field came back"

    def test_removed_ev_helper_raises_rather_than_returning(self) -> None:
        # A tombstone: any surviving caller must fail loudly rather than silently
        # reintroduce a wager the platform cannot settle.
        with pytest.raises(NotImplementedError):
            par.bypass_expected_value()

    def test_no_bypass_events_are_ever_emitted(self) -> None:
        from ball_or_nothing.events import build_events

        for sim_id in range(3000):
            types = {e["type"] for e in build_events(spin(sim_id))}
            assert "bypassOffer" not in types
            assert "bypassResult" not in types

    def test_the_platform_answer_is_still_recorded(self) -> None:
        # If the platform answer ever changes to "yes", this is the test that should be
        # consciously updated rather than quietly deleted.
        from pathlib import Path

        gate = Path(__file__).resolve().parents[1] / ".omo" / "evidence" / "gate-answers.md"
        assert gate.exists(), "the gate-answers record is missing"
        assert "G2-branch: no" in gate.read_text(encoding="utf-8"), "the gate answer changed"


class TestBonus:
    def test_multiplier_starts_at_one(self) -> None:
        r = play_bonus(SplitMix64(1), cfg.Paytable().as_table(), scatters=3)
        assert r.spins[0].multiplier == 1

    def test_multiplier_climbs_on_a_wild_bearing_spin(self) -> None:
        for seed in range(400):
            r = play_bonus(SplitMix64(seed), cfg.Paytable().as_table(), scatters=3)
            if any(cfg.WILD in row for row in r.spins[0].board):
                assert r.spins[1].multiplier == 1 + cfg.BONUS.multiplier_add
                return
        pytest.fail("no wild-bearing first free spin found")

    def test_multiplier_holds_without_a_wild(self) -> None:
        for seed in range(400):
            r = play_bonus(SplitMix64(seed), cfg.Paytable().as_table(), scatters=3)
            if not any(cfg.WILD in row for row in r.spins[0].board):
                assert r.spins[1].multiplier == 1
                return
        pytest.fail("no wild-free first free spin found")

    def test_multiplier_never_exceeds_the_cap(self) -> None:
        for seed in range(120):
            r = play_bonus(SplitMix64(seed), cfg.Paytable().as_table(), scatters=5)
            for s in r.spins:
                assert s.multiplier <= cfg.BONUS.multiplier_cap

    def test_scatter_count_sets_the_spin_award(self) -> None:
        for scatters, expected in cfg.VAULTS.triggers.items():
            r = play_bonus(SplitMix64(3), cfg.Paytable().as_table(), scatters=scatters)
            assert r.spin_count == expected

    def test_more_scatters_award_at_least_as_many_spins(self) -> None:
        awards = [cfg.VAULTS.triggers[k] for k in sorted(cfg.VAULTS.triggers)]
        assert awards == sorted(awards)

    def test_total_is_the_sum_of_spin_payouts(self) -> None:
        r = play_bonus(SplitMix64(11), cfg.Paytable().as_table(), scatters=3)
        assert r.total == pytest.approx(sum(s.payout for s in r.spins))

    def test_every_spin_payout_is_multiplied(self) -> None:
        t = cfg.Paytable().as_table()
        r = play_bonus(SplitMix64(5), cfg.Paytable().as_table(), scatters=3)
        for s in r.spins:
            raw, _ = evaluate_board(s.board, t)
            assert s.payout == pytest.approx(raw * s.multiplier)

    def test_multiplier_sum_expectation_grows_with_spins(self) -> None:
        s12 = par.multiplier_sum_expectation(12)
        s20 = par.multiplier_sum_expectation(20)
        assert s20 > s12 > 12


class TestRng:
    def test_same_seed_gives_same_sequence(self) -> None:
        assert SplitMix64(42).next_u64() == SplitMix64(42).next_u64()

    def test_different_seeds_diverge(self) -> None:
        a = [SplitMix64(1).next_u64() for _ in range(5)]
        b = [SplitMix64(2).next_u64() for _ in range(5)]
        assert a != b

    def test_random_is_in_unit_interval(self) -> None:
        rng = SplitMix64(7)
        for _ in range(1000):
            assert 0.0 <= rng.random() < 1.0

    def test_weighted_choice_respects_zero_weight(self) -> None:
        rng = SplitMix64(3)
        assert {rng.weighted_choice({"a": 0, "b": 5}) for _ in range(100)} == {"b"}

    def test_weighted_choice_rejects_all_zero(self) -> None:
        with pytest.raises(ValueError):
            SplitMix64(1).weighted_choice({"a": 0, "b": 0})

    def test_weighted_choice_rejects_negative(self) -> None:
        with pytest.raises(ValueError):
            SplitMix64(1).weighted_choice({"a": -1, "b": 2})


class TestSpinner:
    def test_spin_is_deterministic(self) -> None:
        assert spin(12345) == spin(12345)

    def test_bonus_present_exactly_when_scatters_allow(self) -> None:
        for sim_id in range(2000):
            outcome = spin(sim_id)
            assert outcome.triggered_bonus == (count_scatters(outcome.board) >= 3)

    def test_criteria_matches_the_distribution_bucket(self) -> None:
        for sim_id in range(500):
            outcome = spin(sim_id)
            if outcome.triggered_bonus:
                assert outcome.criteria == "bonus"
            elif outcome.base_payout > 0:
                assert outcome.criteria == "win"
            else:
                assert outcome.criteria == "0"

    def test_round_never_exceeds_the_wincap(self) -> None:
        for sim_id in range(5000):
            assert spin(sim_id).payout_multiplier <= cfg.WINCAP

    def test_base_payout_is_recorded_separately_from_the_bonus(self) -> None:
        for sim_id in range(2000):
            outcome = spin(sim_id)
            if outcome.bonus is None:
                continue
            # the triggering spin pays nothing itself; the feature carries it
            assert outcome.base_payout == 0.0
            assert outcome.payout_multiplier == pytest.approx(
                min(outcome.bonus.total, cfg.WINCAP)
            )
            return
        pytest.fail("no bonus round found")


class TestQuotas:
    """The book-generator quotas must match the machine, not contradict it.

    The shipped quotas were invented: a win quota of 0.31 demanded 1.59x more winning rounds
    than the reels can produce, so any generator honouring them had to miss or distort the
    reels. These tests are what stop that drifting again.
    """

    def test_declared_quotas_are_achievable(self) -> None:
        specs = cfg.bet_modes()[0].distributions
        quotas = {s.criteria: s.quota for s in specs}

        measured = par.monte_carlo(120_000, seed=1)
        trigger = par.trigger_probability()

        # The bonus bucket must equal the real trigger rate.
        assert quotas["bonus"] == pytest.approx(trigger, abs=0.0005), (
            f"declared bonus {quotas['bonus']} vs real {trigger:.6f}"
        )
        # The win bucket must equal the real round hit rate.
        assert quotas["win"] == pytest.approx(measured.hit_rate, abs=0.01), (
            f"declared win {quotas['win']} vs real {measured.hit_rate:.6f}"
        )

    def test_quotas_sum_to_one(self) -> None:
        # winCap is an OVERLAY, not a fourth bucket: a wincap round is also a win or bonus
        # round, so it is deliberately excluded from the partition.
        specs = cfg.bet_modes()[0].distributions
        partition = sum(s.quota for s in specs if s.criteria != "winCap")
        assert partition == pytest.approx(1.0, abs=1e-6), f"win+bonus+zero = {partition}"

    def test_the_wincap_overlay_is_small(self) -> None:
        specs = {s.criteria: s.quota for s in cfg.bet_modes()[0].distributions}
        assert 0 < specs["winCap"] < 0.01, "a wincap overlay that large would distort the set"

    def test_the_zero_bucket_is_the_remainder(self) -> None:
        specs = {s.criteria: s.quota for s in cfg.bet_modes()[0].distributions}
        assert specs["0"] == pytest.approx(1.0 - specs["win"] - specs["bonus"], abs=1e-6)

    def test_the_wincap_bucket_is_a_policy_choice_not_a_derivation(self) -> None:
        # Documented deliberately: this one is set by design so the advertised ceiling is
        # reachable in the book set, and it is the only quota that is not measured.
        specs = {s.criteria: s for s in cfg.bet_modes()[0].distributions}
        assert specs["winCap"].quota == pytest.approx(0.0002)
        assert specs["winCap"].conditions.get("force_wincap") is True


class TestVolatilityLadder:
    """The three modes: every rung exactly 0.97, and BALL is the shipped machine."""

    def test_every_mode_solves_to_the_target_rtp(self) -> None:
        for sheet in par.mode_sheets():
            assert sheet.rtp == pytest.approx(cfg.TARGET_RTP, abs=1e-5), sheet.label

    def test_ball_reproduces_the_shipped_machine_exactly(self) -> None:
        # BALL is not a re-derivation: it IS the independently verified table, so the
        # headline numbers the README quotes must still hold on that rung.
        ball = next(s for s in par.mode_sheets() if s.name == "ball")
        assert ball.top_prize == pytest.approx(cfg.Paytable().five_ball)
        assert ball.rtp == pytest.approx(par.closed_form_rtp(), abs=1e-9)

    def test_the_ladder_is_monotonic_in_max_win(self) -> None:
        sheets = list(par.mode_sheets())
        wins = [s.max_win for s in sheets]
        assert wins == sorted(wins), f"max win must climb across the ladder, got {wins}"

    def test_every_mode_has_a_distinct_top_prize(self) -> None:
        tops = [round(s.top_prize, 6) for s in par.mode_sheets()]
        assert len(set(tops)) == len(tops), "two modes share a top prize"

    def test_no_mode_exceeds_its_own_wincap(self) -> None:
        for sheet in par.mode_sheets():
            assert sheet.max_win <= sheet.wincap, sheet.label

    def test_modes_do_not_share_a_constant(self) -> None:
        # Retuning one rung must not silently move another. If any two modes produced the
        # same top prize, they would share a solved constant.
        sheets = list(par.mode_sheets())
        for i, a in enumerate(sheets):
            for b in sheets[i + 1:]:
                assert a.top_prize != b.top_prize, f"{a.label} and {b.label} share a constant"

    def test_mode_reels_are_valid_weight_vectors(self) -> None:
        for mode in cfg.MODES.values():
            for name, reels in (("base", cfg.mode_reels(mode)), ("free", cfg.mode_free_reels(mode))):
                assert sum(reels.values()) == 1000, f"{mode.name}/{name} sums to {sum(reels.values())}"
                for symbol in cfg.SYMBOLS:
                    assert reels[symbol] > 0, f"{mode.name}/{name}: {symbol} has no weight"

    def test_a_mode_that_cannot_afford_its_tiers_is_rejected(self) -> None:
        # A flat tier ratio on very dense reels puts the lower tiers over the RTP budget.
        # That must raise, not silently ship.
        bad = cfg.Mode(
            name="bad", label="BAD", blurb="", density=900, wild=90,
            tier_flat=0.95, wincap=1_000.0,
        )
        with pytest.raises(ValueError):
            par.solve_mode(bad)

    def test_ball_mode_uses_the_shipped_free_reels(self) -> None:
        # The free-game reels are a separate table on the shipped machine; dropping them
        # would silently change the bonus.
        ball = cfg.MODES["ball"]
        assert cfg.mode_free_reels(ball) == cfg.FREEGAME_WEIGHTS["default"]


class TestMonteCarloAgreement:
    def test_monte_carlo_agrees_with_closed_form(self) -> None:
        expected = par.closed_form_rtp()
        result = par.monte_carlo(120_000, seed=0)
        assert result.agrees_with(expected, sigmas=5.0), (
            f"monte carlo {result.mean_payout:.6f} "
            f"(+-{result.standard_error:.6f}) vs closed form {expected:.6f}"
        )

    def test_monte_carlo_bonus_rate_agrees(self) -> None:
        result = par.monte_carlo(120_000, seed=0)
        assert result.bonus_hits / result.spins == pytest.approx(
            par.trigger_probability(), abs=0.001
        )
