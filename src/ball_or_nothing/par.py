"""RTP solver, verifier, and PAR sheet for the 5x3 board.

Three exact pieces, no simulation required for any of them:

  base    E[spin] = 10 * E[single line]. Expectation is linear, so the ten paylines being
          correlated does not matter - only the marginal of one line does.
  line    E[single line] = sum over all 7^5 symbol sequences, weighted by the product of
          per-position probabilities. 16,807 terms, exact.
  bonus   The multiplier doubles for every free spin containing a wild, so at spin i it is
          step^K with K ~ Binomial(i-1, p_wild). Its expectation is closed form from the
          binomial moment generating function. Spin count varies with the scatter count,
          so the bonus is averaged over the scatter distribution.

monte_carlo() independently plays real rounds and must agree. The test suite asserts it,
which is the evidence the decomposition is right rather than merely self-consistent.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb
from typing import Dict, List, Tuple

from . import config as cfg
from .spinner import (
    all_lines,
    evaluate_board,
    line_symbols,
    play_bonus,
    spin,
    wild_spin_probability,
)


def _probabilities(weights: Dict[str, Dict[str, int]] | None = None) -> Dict[str, float]:
    reel = (weights or cfg.REEL_WEIGHTS)["default"]
    total = sum(reel.values())
    return {s: w / total for s, w in reel.items()}


def expected_line_payout(
    table: Dict[Tuple[int, str], float],
    weights: Dict[str, Dict[str, int]] | None = None,
) -> float:
    """Expected payout of ONE payline, summed exactly over all 7^5 sequences."""
    probs = _probabilities(weights)
    total = 0.0
    for symbols, (_sym, _kind, payout) in all_lines(table):
        if payout == 0.0:
            continue
        p = 1.0
        for s in symbols:
            p *= probs[s]
        total += p * payout
    return total


def expected_spin_payout(
    table: Dict[Tuple[int, str], float],
    weights: Dict[str, Dict[str, int]] | None = None,
) -> float:
    """Expected payout of a base spin: every payline evaluated on the same board."""
    return len(cfg.PAYLINES) * expected_line_payout(table, weights)


def scatter_distribution(weights: Dict[str, Dict[str, int]] | None = None) -> Dict[int, float]:
    """Probability of each scatter bucket (3, 4, 5+) across the 15 board positions."""
    p = _probabilities(weights)[cfg.VAULT]
    n = cfg.NUM_REELS * cfg.NUM_ROWS
    out: Dict[int, float] = {}
    for k in (3, 4):
        out[k] = comb(n, k) * (p**k) * ((1 - p) ** (n - k))
    out[5] = sum(
        comb(n, k) * (p**k) * ((1 - p) ** (n - k)) for k in range(5, n + 1)
    )
    return out


def trigger_probability(weights: Dict[str, Dict[str, int]] | None = None) -> float:
    return sum(scatter_distribution(weights).values())


def multiplier_sum_expectation(
    spins: int,
    weights: Dict[str, Dict[str, int]] | None = None,
    bonus: cfg.Bonus | None = None,
) -> float:
    """S = sum over free spins of E[multiplier at that spin].

    The multiplier after n wild-bearing spins is a + n capped, with a ~ Binomial(n,
    p_spin), so the expectation is closed form.
    """
    bonus = bonus or cfg.BONUS
    p_spin = wild_spin_probability(weights)

    total = 0.0
    for i in range(spins):
        expectation = 0.0
        for k in range(i + 1):
            weight = comb(i, k) * (p_spin**k) * ((1 - p_spin) ** (i - k))
            expectation += weight * min(
                bonus.multiplier_add * k + 1, bonus.multiplier_cap
            )
        total += expectation
    return total


def bonus_expected_multiple(
    weights: Dict[str, Dict[str, int]] | None = None,
    bonus: cfg.Bonus | None = None,
    scatter_weights: Dict[str, Dict[str, int]] | None = None,
) -> float:
    """Expected payout of one BALLGAME, expressed as a multiple of one free spin's EV.

    `weights` are the FREE-game reels (where the multiplier ladder advances);
    `scatter_weights` are the BASE reels the trigger is rolled on. They are separate
    parameters because a mode changes both, and using the wrong one for either silently
    mis-states the bonus.
    """
    weights = weights or cfg.FREEGAME_WEIGHTS
    bonus = bonus or cfg.BONUS
    dist = scatter_distribution(scatter_weights)
    total = 0.0
    for scatters, prob in dist.items():
        spins = cfg.VAULTS.triggers.get(scatters, 0)
        if spins <= 0:
            continue
        total += prob * multiplier_sum_expectation(spins, weights, bonus)
    return total


def closed_form_rtp(
    paytable: cfg.Paytable | None = None,
    bonus: cfg.Bonus | None = None,
    reels: Dict[str, Dict[str, int]] | None = None,
    free_reels: Dict[str, Dict[str, int]] | None = None,
) -> float:
    """Exact RTP for the whole game, base spins and BALLGAME rounds.

    `reels` and `free_reels` default to the shipped table; a volatility mode passes its own
    so each mode is solved without mutating any global.
    """
    paytable = paytable or cfg.Paytable()
    table = paytable.as_table()
    reels = reels or cfg.REEL_WEIGHTS
    free_reels = free_reels or cfg.FREEGAME_WEIGHTS

    e_base = expected_spin_payout(table, reels)
    e_free = expected_spin_payout(table, free_reels)
    p_trigger = trigger_probability(reels)
    bonus_multiple = bonus_expected_multiple(free_reels, bonus, scatter_weights=reels)

    return (1 - p_trigger) * e_base + bonus_multiple * e_free


def base_rtp(paytable: cfg.Paytable | None = None) -> float:
    paytable = paytable or cfg.Paytable()
    return (1 - trigger_probability()) * expected_spin_payout(paytable.as_table(), cfg.REEL_WEIGHTS)


def bonus_rtp(paytable: cfg.Paytable | None = None, bonus: cfg.Bonus | None = None) -> float:
    paytable = paytable or cfg.Paytable()
    return bonus_expected_multiple(cfg.FREEGAME_WEIGHTS, bonus) * expected_spin_payout(
        paytable.as_table(), cfg.FREEGAME_WEIGHTS
    )


def hit_rate(table: Dict[Tuple[int, str], float] | None = None) -> float:
    """Probability a base spin pays at least one line.

    Exact by inclusion over the board is infeasible (7^15), so this is the one figure
    measured by simulation. Kept separate from the RTP, which is exact.
    """
    table = table if table is not None else cfg.Paytable().as_table()
    from .rng import SplitMix64

    hits = 0
    n = 200_000
    for i in range(n):
        rng = SplitMix64(i)
        board = [[rng.weighted_choice(cfg.REEL_WEIGHTS["default"]) for _ in range(cfg.NUM_ROWS)] for _ in range(cfg.NUM_REELS)]
        total, _ = evaluate_board(board, table)
        if total > 0:
            hits += 1
    return hits / n


def max_win(paytable: cfg.Paytable | None = None, bonus: cfg.Bonus | None = None) -> float:
    """The largest payout the machine can produce.

    The final free spin carries the biggest multiplier available and the best line is
    five BALL on one payline; every payline could in principle hit, so the board ceiling
    is that win times the payline count. Capped by the wincap.
    """
    paytable = paytable or cfg.Paytable()
    bonus = bonus or cfg.BONUS
    spins = max(cfg.VAULTS.triggers.values())
    multiplier = min(bonus.multiplier_add * (spins - 1) + 1, bonus.multiplier_cap)
    per_line = paytable.five_ball
    return min(per_line * len(cfg.PAYLINES) * multiplier, cfg.WINCAP)


@dataclass(frozen=True)
class ParSheet:
    rtp: float
    base_rtp: float
    bonus_rtp: float
    trigger_rate: float
    volatility: float
    max_win: float
    max_multiplier: int


def par_sheet(paytable: cfg.Paytable | None = None, bonus: cfg.Bonus | None = None) -> ParSheet:
    paytable = paytable or cfg.Paytable()
    bonus = bonus or cfg.BONUS
    spins = max(cfg.VAULTS.triggers.values())
    return ParSheet(
        rtp=closed_form_rtp(paytable, bonus),
        base_rtp=base_rtp(paytable),
        bonus_rtp=bonus_rtp(paytable, bonus),
        trigger_rate=trigger_probability(),
        volatility=0.0,
        max_win=max_win(paytable, bonus),
        max_multiplier=min(bonus.multiplier_add * (spins - 1) + 1, bonus.multiplier_cap),
    )


def bypass_expected_value(bonus: cfg.Bonus | None = None) -> float:
    """REMOVED. THE BYPASS was deleted - see `.omo/evidence/gate-answers.md`.

    Stake Engine books are static and pre-computed, so a mid-round player decision has no
    settlement path. The function is kept only as a tombstone so that any surviving caller
    fails loudly rather than silently reintroducing a wager the platform cannot settle.
    """
    raise NotImplementedError(
        "THE BYPASS was removed: Stake books are pre-computed and cannot branch on a "
        "mid-round player decision. See .omo/evidence/gate-answers.md (G2-branch: no)."
    )


@dataclass(frozen=True)
class MonteCarloResult:
    spins: int
    mean_payout: float
    standard_error: float
    hit_rate: float
    bonus_hits: int
    max_seen: float

    def agrees_with(self, expected: float, sigmas: float = 4.0) -> bool:
        if self.standard_error == 0:
            return abs(self.mean_payout - expected) < 1e-12
        return abs(self.mean_payout - expected) <= sigmas * self.standard_error


def monte_carlo(
    n: int,
    seed: int = 0,
    paytable: cfg.Paytable | None = None,
    bonus: cfg.Bonus | None = None,
) -> MonteCarloResult:
    """Play `n` real rounds and measure them, as an independent check on the closed form."""
    if n <= 0:
        raise ValueError("n must be positive")

    total = 0.0
    total_sq = 0.0
    hits = 0
    bonus_hits = 0
    max_seen = 0.0

    for i in range(n):
        outcome = spin(seed + i, paytable, bonus)
        payout = outcome.payout_multiplier

        total += payout
        total_sq += payout * payout
        if payout > 0:
            hits += 1
        if outcome.triggered_bonus:
            bonus_hits += 1
        if payout > max_seen:
            max_seen = payout

    mean = total / n
    variance = max(total_sq / n - mean * mean, 0.0)

    return MonteCarloResult(
        spins=n,
        mean_payout=mean,
        standard_error=(variance / n) ** 0.5,
        hit_rate=hits / n,
        bonus_hits=bonus_hits,
        max_seen=max_seen,
    )


def solve_five_ball_for_rtp(
    target_rtp: float,
    paytable: cfg.Paytable | None = None,
    bonus: cfg.Bonus | None = None,
    tolerance: float = 1e-9,
) -> float:
    """Solve for the five-of-a-kind BALL payout that lands total RTP on target.

    RTP is affine in that one payout, so evaluate the game twice (paying nothing, then
    paying one) and interpolate. Using the top prize as the knob keeps every other
    number in the paytable round.
    """
    bonus = bonus or cfg.BONUS

    def rtp_at(five_ball: float) -> float:
        table = cfg.Paytable(**{**cfg.Paytable().__dict__, "five_ball": five_ball})
        return closed_form_rtp(table, bonus)

    b = rtp_at(0.0)
    a = rtp_at(1.0) - b

    if a <= 0:
        raise ValueError("five-of-a-kind BALL pays nothing; nothing to solve")

    solved = (target_rtp - b) / a
    if solved <= 0:
        raise ValueError(
            f"target RTP {target_rtp} is below the seeded return ({b:.6f}); "
            "lower the fixed payouts or raise the target"
        )

    achieved = rtp_at(solved)
    if abs(achieved - target_rtp) > tolerance:
        raise AssertionError(f"solve drifted: wanted {target_rtp}, produced {achieved}")
    return solved


def solve_scale_for_rtp(
    target_rtp: float,
    paytable: cfg.Paytable | None = None,
    bonus: cfg.Bonus | None = None,
    tolerance: float = 1e-9,
) -> float:
    """Solve for the multiplier that scales the whole paytable onto the target RTP.

    RTP is linear in the paytable, so this is one divide rather than a search:

        RTP(1) = A, so RTP(s) = s * A  ->  s = target / A
    """
    paytable = paytable or cfg.Paytable()
    bonus = bonus or cfg.BONUS

    base_rtp_now = closed_form_rtp(paytable, bonus)
    if base_rtp_now <= 0:
        raise ValueError("the paytable pays nothing; nothing to solve")

    scale = target_rtp / base_rtp_now
    if scale <= 0:
        raise ValueError(f"target RTP {target_rtp} is unreachable with this paytable")

    return scale


# ---------------------------------------------------------------------------
# THE VOLATILITY LADDER
# ---------------------------------------------------------------------------


def solve_mode(mode: cfg.Mode, target_rtp: float = cfg.TARGET_RTP) -> cfg.Paytable:
    """Solve one mode's paytable so it lands on `target_rtp` exactly.

    A mode with an `exact_paytable` is used verbatim - that rung IS the shipped machine and
    must not be re-derived. Otherwise the mode's shape is relative, so RTP is affine in
    `five_ball` alone: evaluate with the top prize paying nothing and then paying one, and
    interpolate. Each mode is solved independently; no mode inherits a constant.
    """
    weights = {"default": cfg.mode_reels(mode)}
    free_weights = {"default": cfg.mode_free_reels(mode)}

    if mode.exact_paytable is not None:
        table = mode.exact_paytable
        achieved = closed_form_rtp(table, reels=weights, free_reels=free_weights)
        if abs(achieved - target_rtp) > 1e-5:
            raise AssertionError(
                f"mode {mode.name} ships an exact paytable returning {achieved:.6f}, "
                f"not the {target_rtp} target"
            )
        return table

    shape = cfg.mode_paytable_shape(mode)

    def rtp_at(top: float) -> float:
        absolute = {key: top * value for key, value in shape.items()}
        table = cfg.Paytable(**{**absolute, "five_ball": top, "five_wild": top})
        return closed_form_rtp(table, reels=weights, free_reels=free_weights)

    base = rtp_at(0.0)
    slope = rtp_at(1.0) - base
    if slope <= 0:
        raise ValueError(f"mode {mode.name}: the paytable pays nothing, nothing to solve")

    top = (target_rtp - base) / slope
    if top <= 0:
        raise ValueError(
            f"mode {mode.name}: the lower tiers alone already return {base:.6f}, which is "
            f"above the {target_rtp} budget. Flatten the tiers or lower the density."
        )

    achieved = rtp_at(top)
    if abs(achieved - target_rtp) > 1e-9:
        raise AssertionError(f"mode {mode.name} drifted: wanted {target_rtp}, got {achieved}")

    absolute = {key: top * value for key, value in shape.items()}
    return cfg.Paytable(**{**absolute, "five_ball": top, "five_wild": top})


@dataclass(frozen=True)
class ModeSheet:
    name: str
    label: str
    blurb: str
    rtp: float
    top_prize: float
    max_multiplier: int
    max_win: float
    wincap: float


def mode_sheets(target_rtp: float = cfg.TARGET_RTP) -> List[ModeSheet]:
    """Solve and summarise every mode on the ladder."""
    out: List[ModeSheet] = []
    for mode in cfg.MODES.values():
        table = solve_mode(mode, target_rtp)
        weights = {"default": cfg.mode_reels(mode)}
        free_weights = {"default": cfg.mode_free_reels(mode)}
        out.append(
            ModeSheet(
                name=mode.name,
                label=mode.label,
                blurb=mode.blurb,
                rtp=closed_form_rtp(table, reels=weights, free_reels=free_weights),
                top_prize=table.five_ball,
                max_multiplier=min(
                    cfg.BONUS.multiplier_add * (max(cfg.VAULTS.triggers.values()) - 1) + 1,
                    cfg.BONUS.multiplier_cap,
                ),
                max_win=min(
                    table.five_ball
                    * len(cfg.PAYLINES)
                    * (cfg.BONUS.multiplier_add * (max(cfg.VAULTS.triggers.values()) - 1) + 1),
                    mode.wincap,
                ),
                wincap=mode.wincap,
            )
        )
    return out
