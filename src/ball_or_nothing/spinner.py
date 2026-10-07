"""Core spin resolution for the 5x3 board, including the BALLGAME.

No SDK imports, no I/O, no global state: give it a seed and it returns a SpinOutcome for
the whole round. That isolation is what makes the math testable and what lets one
implementation drive the Stake book generator, the RTP verifier, and the frontend.

LINE RULES
----------
Ten paylines across 5 reels x 3 rows. Each line is read left to right from reel 0 and pays
for the longest run of a single symbol, with WILD substituting. VAULT is a scatter: it
never substitutes and it breaks a line. Three or more VAULTs anywhere on the board open
the BALLGAME.

A line of nothing but wilds pays as BALL at whatever length it reached.

NO MID-ROUND WAGER
------------------
There is deliberately no double-or-nothing step. Stake Engine books are static and
pre-computed - "no server-side game logic executed at play time" - so a player decision
made mid-round has no settlement path, and a pre-computed branch is still a decision the
client cannot communicate back. The rejected design and its full reasoning are in
`.omo/hyperplan-insight-bundle.md`; the record of the platform question is in
`.omo/evidence/gate-answers.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import config as cfg
from .rng import SplitMix64


@dataclass(frozen=True)
class LineWin:
    line_index: int
    symbol: str
    kind: int
    payout: float


@dataclass(frozen=True)
class FreeSpin:
    index: int
    board: List[List[str]]
    multiplier: int
    payout: float
    wins: Tuple[LineWin, ...]


@dataclass(frozen=True)
class BonusRound:
    spins: List[FreeSpin]
    total: float
    final_multiplier: int
    start_spins: int

    @property
    def spin_count(self) -> int:
        return len(self.spins)


@dataclass(frozen=True)
class SpinOutcome:
    sim_id: int
    board: List[List[str]]
    payout_multiplier: float
    win_kind: str
    criteria: str
    base_payout: float = 0.0
    wins: Tuple[LineWin, ...] = ()
    bonus: Optional[BonusRound] = None

    @property
    def is_win(self) -> bool:
        return self.payout_multiplier > 0

    @property
    def triggered_bonus(self) -> bool:
        return self.bonus is not None


CRITERIA_BY_KIND = {
    "jackpot": "win",
    "win": "win",
    "loss": "0",
    "bonus": "bonus",
}


def line_symbols(board: List[List[str]], line_index: int) -> Tuple[str, ...]:
    rows = cfg.PAYLINES[line_index]
    return tuple(board[reel][rows[reel]] for reel in range(cfg.NUM_REELS))


def evaluate_line(symbols: Tuple[str, ...], table: Dict[Tuple[int, str], float]) -> Tuple[str, int, float]:
    """Resolve one payline into (symbol, kind, payout).

    Wild substitution: leading wilds take on the identity of the first real symbol. A
    line that is nothing but wilds pays as BALL, and a VAULT anywhere ends the run
    because a scatter never substitutes.
    """
    run_symbol: Optional[str] = None
    length = 0

    for symbol in symbols:
        if symbol == cfg.WILD:
            length += 1
            continue
        if symbol == cfg.VAULT:
            break
        if run_symbol is None:
            run_symbol = symbol
            length += 1
        elif symbol == run_symbol:
            length += 1
        else:
            break

    if run_symbol is None:
        run_symbol = cfg.BALL

    if run_symbol not in cfg.PAYING_SYMBOLS or length < 3:
        return run_symbol, length, 0.0
    return run_symbol, length, table.get((length, run_symbol), 0.0)


def evaluate_board(
    board: List[List[str]],
    table: Dict[Tuple[int, str], float] | None = None,
) -> Tuple[float, Tuple[LineWin, ...]]:
    table = table if table is not None else cfg.Paytable().as_table()
    wins: List[LineWin] = []
    total = 0.0
    for index in cfg.PAYLINES:
        symbol, kind, payout = evaluate_line(line_symbols(board, index), table)
        if payout > 0:
            wins.append(LineWin(index, symbol, kind, payout))
            total += payout
    return total, tuple(wins)


def count_scatters(board: List[List[str]]) -> int:
    return sum(row.count(cfg.VAULT) for row in board)


def draw_board(
    rng: SplitMix64,
    weights: Dict[str, Dict[str, int]] | None = None,
) -> List[List[str]]:
    """Draw a 5x3 board, one independent weighted draw per position."""
    reel_weights = (weights or cfg.REEL_WEIGHTS)["default"]
    return [
        [rng.weighted_choice(reel_weights) for _ in range(cfg.NUM_ROWS)]
        for _ in range(cfg.NUM_REELS)
    ]


def wild_spin_probability(weights: Dict[str, Dict[str, int]] | None = None) -> float:
    """Probability a spin shows at least one WILD, so it advances the multiplier ladder.

    Measured on the free-game reels by default: that is where the ladder advances.
    """
    reel_weights = (weights or cfg.FREEGAME_WEIGHTS)["default"]
    total = sum(reel_weights.values())
    p_wild = reel_weights[cfg.WILD] / total
    return 1.0 - (1.0 - p_wild) ** (cfg.NUM_REELS * cfg.NUM_ROWS)


def bonus_spins_for(scatters: int, vaults: cfg.Vault | None = None) -> int:
    vaults = vaults or cfg.VAULTS
    return vaults.triggers.get(scatters, 0)


def play_bonus(
    rng: SplitMix64,
    table: Dict[Tuple[int, str], float],
    bonus: cfg.Bonus | None = None,
    scatters: int = 3,
) -> BonusRound:
    """Run the BALLGAME.

    The multiplier starts at 1 and doubles for each free spin that showed a wild,
    applying from the NEXT spin onward, so the round builds toward the end.
    """
    bonus = bonus or cfg.BONUS
    total_spins = bonus_spins_for(scatters)
    spins: List[FreeSpin] = []
    multiplier = 1
    total = 0.0

    for i in range(total_spins):
        board = draw_board(rng, cfg.FREEGAME_WEIGHTS)
        payout, wins = evaluate_board(board, table)
        payout *= multiplier
        total += payout
        spins.append(
            FreeSpin(
                index=i,
                board=board,
                multiplier=multiplier,
                payout=payout,
                wins=wins,
            )
        )
        if any(cfg.WILD in row for row in board):
            multiplier = min(multiplier + bonus.multiplier_add, bonus.multiplier_cap)

    return BonusRound(
        spins=spins,
        total=total,
        final_multiplier=multiplier,
        start_spins=total_spins,
    )


def spin(
    sim_id: int,
    paytable: cfg.Paytable | None = None,
    bonus: cfg.Bonus | None = None,
) -> SpinOutcome:
    """Play one complete round, deterministically, from `sim_id`.

    The round is entirely a function of the seed: base board, and the BALLGAME if three or
    more VAULTs appeared. There is no player decision anywhere in it, which is exactly what
the platform's static pre-computed book model requires.
    """
    paytable = paytable or cfg.Paytable()
    bonus = bonus or cfg.BONUS
    table = paytable.as_table()
    rng = SplitMix64(sim_id)

    board = draw_board(rng)
    base_payout, base_wins = evaluate_board(board, table)
    scatters = count_scatters(board)

    round_bonus: Optional[BonusRound] = None
    total = base_payout

    if scatters >= 3:
        round_bonus = play_bonus(rng, table, bonus, scatters)
        total = round_bonus.total

    # The wincap is applied ONCE, here, to the whole round - base and bonus together. The
    # frontend must never re-derive it: three separate cap semantics is what let the demo
    # display a payout 45x the advertised maximum.
    total = min(total, cfg.WINCAP)
    kind = "bonus" if round_bonus else ("win" if base_payout > 0 else "loss")

    return SpinOutcome(
        sim_id=sim_id,
        board=board,
        payout_multiplier=total,
        win_kind=kind,
        criteria=CRITERIA_BY_KIND[kind],
        base_payout=base_payout,
        wins=base_wins,
        bonus=round_bonus,
    )


def all_lines(table: Dict[Tuple[int, str], float] | None = None) -> List[Tuple[Tuple[str, ...], Tuple[str, int, float]]]:
    """Enumerate every 5-symbol line the reels can produce (7^5 = 16807)."""
    table = table if table is not None else cfg.Paytable().as_table()
    out: List[Tuple[Tuple[str, ...], Tuple[str, int, float]]] = []
    for a in cfg.SYMBOLS:
        for b in cfg.SYMBOLS:
            for c in cfg.SYMBOLS:
                for d in cfg.SYMBOLS:
                    for e in cfg.SYMBOLS:
                        symbols = (a, b, c, d, e)
                        out.append((symbols, evaluate_line(symbols, table)))
    return out


def symbol_probabilities(weights: Dict[str, Dict[str, int]] | None = None) -> Dict[str, float]:
    reel_weights = (weights or cfg.REEL_WEIGHTS)["default"]
    total = sum(reel_weights.values())
    return {symbol: w / total for symbol, w in reel_weights.items()}
