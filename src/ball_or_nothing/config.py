"""Game parameters for BALL OR NOTHING.

5 reels x 3 rows, 10 paylines, plus the BALLGAME free-spin feature and THE BYPASS.

Board
  Reels are drawn as INDEPENDENT per-position weights rather than as strip windows. A
  strip window correlates the three visible rows, which makes the exact RTP depend on the
  strip layout; independent draws make the marginal of every position identical and the
  RTP exactly computable.

  The adapter does NOT override the engine's draw to match. It calls THIS module's
  `draw_board` directly (see `games/masterbetty_ball_or_nothing/gamestate.py`), so there is
  exactly one board model in the product. An earlier version of this docstring claimed an
  override that did not exist - the file was a bare `pass` - which is the kind of promise a
  math product cannot afford to break.

Payouts are multiples of the total bet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

GAME_ID = "masterbetty_ball_or_nothing"
WORKING_NAME = "Ball or Nothing"
PROVIDER_NUMBER = 0  # assigned by the provider registry on submission
WIN_TYPE = "lines"

BALL = "BALL"    # top payer
NUT = "NUT"
SACK = "SACK"
COIN = "COIN"    # bottom payer
LOSS = "LOSS"    # blank
WILD = "WILD"    # substitutes, and drives the BALLGAME multiplier
VAULT = "VAULT"  # scatter: 3 or more anywhere opens the BALLGAME

SYMBOLS: Tuple[str, ...] = (BALL, NUT, SACK, COIN, LOSS, WILD, VAULT)
PAYING_SYMBOLS: Tuple[str, ...] = (BALL, NUT, SACK, COIN)

GAME_TYPE = "basegame"
FREEGAME_TYPE = "freegame"

NUM_REELS = 5
NUM_ROWS = 3

# Weights out of 1000.
#
# These took real searching. Two constraints fight each other on a 5x3 board: ten
# paylines must not hit so often that every spin pays a token amount, and the top symbol
# must be rare enough that five-of-a-kind can pay something worth chasing. Wild is the
# knife edge - at 10% it made five-of-a-kind 1 in 10,824 per line, ten times too common to
# pay a headline. At 4% with 55% paying density, the hit rate lands at 22.6% per spin and
# five BALL sits at 1 in 29,911 per line.
REEL_WEIGHTS: Dict[str, Dict[str, int]] = {
    "default": {
        BALL: 87,
        NUT: 122,
        SACK: 148,
        COIN: 192,
        LOSS: 386,
        WILD: 40,
        VAULT: 25,
    }
}

# Free spins run hotter: fewer blanks, more of everything that pays, and a higher wild
# rate to drive the multiplier ladder. Without this the feature would feel like a slower
# version of the base game.
FREEGAME_WEIGHTS: Dict[str, Dict[str, int]] = {
    "default": {
        BALL: 100,
        NUT: 130,
        SACK: 150,
        COIN: 170,
        LOSS: 360,
        WILD: 70,
        VAULT: 20,
    }
}

PAYLINES: Dict[int, List[int]] = {
    0: [1, 1, 1, 1, 1],
    1: [0, 0, 0, 0, 0],
    2: [2, 2, 2, 2, 2],
    3: [0, 1, 2, 1, 0],
    4: [2, 1, 0, 1, 2],
    5: [0, 0, 1, 0, 0],
    6: [2, 2, 1, 2, 2],
    7: [1, 0, 0, 0, 1],
    8: [1, 2, 2, 2, 1],
    9: [0, 1, 1, 1, 0],
}


@dataclass(frozen=True)
class Paytable:
    """Line payouts in bet multiples, keyed by (kind, symbol).

    Wild only pays at five-of-a-kind, per the SDK's advice: a wild-only payout at a
    shorter kind can outpay a longer mixed line and makes the evaluation ambiguous.
    """

    five_ball: float = 272.3
    four_ball: float = 5.0
    three_ball: float = 0.4

    five_nut: float = 100.0
    four_nut: float = 2.5
    three_nut: float = 0.2

    five_sack: float = 50.0
    four_sack: float = 1.5
    three_sack: float = 0.15

    five_coin: float = 20.0
    four_coin: float = 1.0
    three_coin: float = 0.1

    five_wild: float = 272.3

    def as_table(self) -> Dict[Tuple[int, str], float]:
        return {
            (5, BALL): self.five_ball,
            (4, BALL): self.four_ball,
            (3, BALL): self.three_ball,
            (5, NUT): self.five_nut,
            (4, NUT): self.four_nut,
            (3, NUT): self.three_nut,
            (5, SACK): self.five_sack,
            (4, SACK): self.four_sack,
            (3, SACK): self.three_sack,
            (5, COIN): self.five_coin,
            (4, COIN): self.four_coin,
            (3, COIN): self.three_coin,
            (5, WILD): self.five_wild,
        }


@dataclass(frozen=True)
class Bonus:
    """The BALLGAME: free spins with a multiplier that climbs on wild-bearing spins.

    The ladder is ADDITIVE, not doubling. With a wild on 10% of positions, 1 - 0.9^15
    means 79% of free spins contain a wild, so a doubling ladder compounds to an expected
    multiplier in the thousands and eats the entire RTP budget. Adding one per
    wild-bearing spin keeps the expectation near 8x while the cap still allows a large
    tail on a lucky round.
    """

    spins: int = 12
    multiplier_add: int = 1
    multiplier_cap: int = 50


@dataclass(frozen=True)
class Vault:
    """Scatter trigger: how many VAULT symbols open the BALLGAME, and for how long."""

    triggers: Dict[int, int] = field(
        default_factory=lambda: {3: 12, 4: 15, 5: 20}
    )


BONUS = Bonus()
VAULTS = Vault()

WINCAP: float = 25_000.0
TARGET_RTP: float = 0.97


# ---------------------------------------------------------------------------
# THE VOLATILITY LADDER
# ---------------------------------------------------------------------------
# "BALL OR NOTHING" is the risk selector: the name describes the choice, not a wager.
#
# This is legal where the old mid-round wager was not. A decision made AT BET TIME is a
# bet-mode selection - the round stays entirely pre-computed, so there is nothing for the
# platform to settle mid-round. It is the same structure as Plinko's low/medium/high risk
# selector and Mines' mine count, which the research identified as THE reason those games
# sit at the top of Stake: player-controlled volatility is the engagement driver.
#
# Every mode is independently solved to exactly TARGET_RTP. No mode shares a constant with
# another, so retuning one cannot silently break another.
#
# The dial is TIER spread, not symbol spread. BALL stays the premium symbol in every mode
# (that is the theme); what changes is how much five-of-a-kind pays relative to
# three-of-a-kind. A flat tier ratio puts the return in the FREQUENT tier (low volatility);
# a steep one puts it in the RARE tier (high volatility).


@dataclass(frozen=True)
class Mode:
    """One rung of the ladder.

    `tier_flat` is the volatility dial: five : four : three = 1 : tier_flat : tier_flat^2.
    `density` is the combined weight of the four paying symbols out of 1000. `wincap` is
    set per mode because a low-volatility mode has no business advertising a ceiling it
    can never approach.

    `exact_paytable`: when set, the mode uses that table verbatim instead of a solved
    shape. The BALL rung uses it so that rung IS the previously shipped, independently
    verified machine rather than a geometric approximation of it.
    """

    name: str
    label: str
    blurb: str
    density: int
    wild: int
    tier_flat: float
    wincap: float
    exact_paytable: "Paytable | None" = None
    exact_base_reels: Dict[str, int] | None = None
    exact_free_reels: Dict[str, int] | None = None


# Weighted like the shipped table so the symbol premium is preserved across every mode.
SYMBOL_RATIO: Dict[str, float] = {BALL: 1.0, NUT: 0.367, SACK: 0.184, COIN: 0.073}

MODES: Dict[str, Mode] = {
    "keep_it": Mode(
        name="keep_it",
        label="KEEP IT",
        blurb="wins constantly, small",
        density=500,
        wild=140,
        tier_flat=0.15,
        wincap=5_000.0,
    ),
    "ball": Mode(
        name="ball",
        label="BALL",
        blurb="the balanced machine",
        density=550,
        wild=40,
        tier_flat=0.0184,
        wincap=25_000.0,
        # Verbatim: this rung IS the shipped, independently verified machine, including
        # its separate free-game reelset.
        exact_paytable=Paytable(),
        exact_base_reels={BALL: 87, NUT: 122, SACK: 148, COIN: 192, LOSS: 386, WILD: 40, VAULT: 25},
        exact_free_reels={BALL: 100, NUT: 130, SACK: 150, COIN: 170, LOSS: 360, WILD: 70, VAULT: 20},
    ),
    "nothing": Mode(
        name="nothing",
        label="NOTHING",
        blurb="rarely, then enormously",
        density=305,
        wild=40,
        tier_flat=0.045,
        wincap=250_000.0,
    ),
}

DEFAULT_MODE = "ball"


def mode_reels(mode: Mode) -> Dict[str, int]:
    """The mode's base reels as concrete weights out of 1000."""
    if mode.exact_base_reels is not None:
        return dict(mode.exact_base_reels)
    return _expand_reels(mode.density, mode.wild)


def mode_free_reels(mode: Mode) -> Dict[str, int]:
    """The mode's free-game reels. Falls back to the base reels when not pinned."""
    if mode.exact_free_reels is not None:
        return dict(mode.exact_free_reels)
    if mode.exact_base_reels is not None:
        return dict(mode.exact_base_reels)
    return _expand_reels(mode.density, mode.wild)


def _expand_reels(density: int, wild: int) -> Dict[str, int]:
    shape = [1.0, 1.4, 1.7, 2.2]
    total = sum(shape)
    weights: Dict[str, int] = {}
    for (symbol, _ratio), s in zip(SYMBOL_RATIO.items(), shape):
        weights[symbol] = int(density * s / total)
    weights[WILD] = wild
    weights[VAULT] = 25
    weights[LOSS] = 1000 - sum(weights.values())
    if weights[LOSS] < 0:
        raise ValueError(f"density {density} + wild {wild} exceeds 1000")
    return weights


def mode_paytable_shape(mode: Mode) -> Dict[str, float]:
    """Relative paytable for a mode, scaled by five_ball so the solver can finish it.

    Tiers are the mode's volatility dial; the symbol ratios are shared so BALL is the
    premium symbol everywhere.
    """
    shape: Dict[str, float] = {}
    for symbol, ratio in SYMBOL_RATIO.items():
        shape[f"five_{symbol.lower()}"] = ratio
        shape[f"four_{symbol.lower()}"] = ratio * mode.tier_flat
        shape[f"three_{symbol.lower()}"] = ratio * mode.tier_flat * mode.tier_flat
    return shape


@dataclass
class BetModeSpec:
    name: str
    cost: float
    is_feature: bool = False
    is_buybonus: bool = False
    auto_close_disabled: bool = False
    distributions: List["DistributionSpec"] = field(default_factory=list)


@dataclass
class DistributionSpec:
    criteria: str
    quota: float
    win_criteria: float | None = None
    conditions: Dict[str, object] = field(default_factory=dict)


def bet_modes() -> List[BetModeSpec]:
    """The distribution quotas the book generator must satisfy.

    These are DERIVED, not chosen. The previous values were invented and contradicted the
    machine: a win quota of 0.31 demanded 1.59x more winning rounds than the reels can
    produce, so a generator honouring it could only ever miss or distort the reels.

    `test_math.py::TestQuotas` asserts these against the measured rates, so they cannot
    drift away from the math again.
    """
    return [
        BetModeSpec(
            name="base",
            cost=1.0,
            is_feature=True,
            distributions=[
                # A policy quota, not a derivable one: the wincap bucket exists to
                # guarantee the advertised ceiling is reachable in the book set.
                DistributionSpec(
                    criteria="winCap",
                    quota=0.0002,
                    win_criteria=WINCAP,
                    conditions={"force_wincap": True},
                ),
                # = the real BALLGAME trigger rate, 1 in 176.
                DistributionSpec(criteria="bonus", quota=0.005674),
                # = the real round hit rate, 1 in 5.1.
                DistributionSpec(criteria="win", quota=0.195453),
                # the remainder; sums to 1.0 with the two above.
                DistributionSpec(criteria="0", quota=0.798873, win_criteria=0.0),
            ],
        )
    ]


def all_valid_symbol_names() -> Tuple[str, ...]:
    return SYMBOLS
