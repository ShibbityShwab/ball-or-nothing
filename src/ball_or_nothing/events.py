"""The game's event stream: the exact JSON the RGS returns and the frontend plays.

Stake Engine never runs game logic at play time. The RGS picks a pre-computed simulation
and returns its `events` array; the frontend is a pure event player. This module is the
contract between the two halves of the product, and it mirrors frontend/engine.js
function-for-function so the adapter and the demo cannot describe the same round
differently.

EVENT ORDER
-----------
  reveal -> (winInfo -> setWin)? -> [fsTrigger -> (freespinUpdate -> reveal -> wins ->
  updateGlobalMult)* -> freespinEnd] -> setTotalWin -> finalWin

Every index is sequential from 0 across the whole simulation, which the SDK requires and
the frontend relies on to play the array in order.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from . import config as cfg
from .spinner import BonusRound, FreeSpin, LineWin, SpinOutcome

REVEAL = "reveal"
WIN_INFO = "winInfo"
SET_WIN = "setWin"
SET_TOTAL_WIN = "setTotalWin"
FINAL_WIN = "finalWin"
FS_TRIGGER = "fsTrigger"
FREESPIN_UPDATE = "freespinUpdate"
UPDATE_GLOBAL_MULT = "updateGlobalMult"
FREESPIN_END = "freespinEnd"

# Presentation tiers, chosen against the actual paytable rather than left at round numbers:
# the top prize is 272x, so the ceiling has to sit above it or a five-of-a-kind gets the
# second-best celebration.
WIN_LEVELS = (
    (0.0, 0),
    (1.0, 1),
    (5.0, 2),
    (20.0, 3),
    (80.0, 4),
    (250.0, 5),
)


def win_level(multiplier: float) -> int:
    """Which win-presentation tier a multiplier falls into."""
    level = 0
    for threshold, tier in WIN_LEVELS:
        if multiplier >= threshold:
            level = tier
    return level


def board_positions(board: List[List[str]]) -> List[List[Dict[str, str]]]:
    """The board as the RGS sends it: one list per reel, each holding its rows."""
    return [[{"name": symbol} for symbol in reel] for reel in board]


def win_positions(win: LineWin) -> List[Dict[str, int]]:
    """The reel/row coordinates a winning line actually covers.

    A win of kind K covers the first K reels of its payline, which is what the frontend
    needs to highlight - sending the whole payline would light positions that did not pay.
    """
    rows = cfg.PAYLINES[win.line_index]
    return [{"reel": reel, "row": rows[reel]} for reel in range(min(win.kind, cfg.NUM_REELS))]


def win_payload(win: LineWin, multiplier: int) -> Dict[str, Any]:
    """One line win, in the shape the RGS expects.

    `LineWin.payout` is the RAW, unmultiplied line value. The BALLGAME multiplies each
    free spin by a climbing multiplier, so the CREDITED amount is raw * multiplier and the
    per-line values must sum to `totalWin` - which they did not, once: `win` carried the raw
    value while `totalWin` carried the multiplied one, and `winWithoutMult` divided an
    already-raw number by the multiplier a second time.

    Both fields are derived from the single raw value, here, in one place.
    """
    credited = win.payout * multiplier
    return {
        "symbol": win.symbol,
        "kind": win.kind,
        "win": credited,
        "positions": win_positions(win),
        "meta": {
            "lineIndex": win.line_index,
            "multiplier": multiplier,
            "winWithoutMult": win.payout,
        },
    }


def reveal_event(board: List[List[str]], index: int, game_type: str = cfg.GAME_TYPE) -> Dict[str, Any]:
    return {
        "index": index,
        "type": REVEAL,
        "board": board_positions(board),
        "paddingPositions": [],
        "gameType": game_type,
        "anticipation": [],
    }


def _append_events(
    events: List[Dict[str, Any]],
    board: List[List[str]],
    total: float,
    wins: Tuple[LineWin, ...] | List[LineWin],
    multiplier: int,
    game_type: str = cfg.GAME_TYPE,
) -> None:
    events.append(reveal_event(board, len(events), game_type))
    if total <= 0:
        return
    events.append(
        {
            "index": len(events),
            "type": WIN_INFO,
            "totalWin": total,
            "wins": [win_payload(w, multiplier) for w in wins],
        }
    )
    events.append(
        {
            "index": len(events),
            "type": SET_WIN,
            "amount": total,
            "winLevel": win_level(total),
        }
    )


def build_base_events(outcome: SpinOutcome) -> List[Dict[str, Any]]:
    """Events for the base spin, excluding anything the feature adds."""
    events: List[Dict[str, Any]] = []

    if outcome.bonus is not None:
        # The triggering spin pays nothing itself; the scatter count is the news.
        events.append(reveal_event(outcome.board, len(events)))
        events.append(
            {
                "index": len(events),
                "type": FS_TRIGGER,
                "scatters": _scatter_count(outcome),
                "spins": outcome.bonus.start_spins,
            }
        )
    else:
        _append_events(events, outcome.board, outcome.base_payout, outcome.wins, 1)

    return events


def _scatter_count(outcome: SpinOutcome) -> int:
    return sum(reel.count(cfg.VAULT) for reel in outcome.board)


def build_bonus_events(outcome: SpinOutcome) -> List[Dict[str, Any]]:
    """Events for the BALLGAME, in the order the frontend plays them."""
    if outcome.bonus is None:
        return []

    events: List[Dict[str, Any]] = []
    running = 0.0

    for free in outcome.bonus.spins:
        events.append(
            {
                "index": len(events),
                "type": FREESPIN_UPDATE,
                "currentSpin": free.index + 1,
                "totalSpins": outcome.bonus.spin_count,
                "multiplier": free.multiplier,
            }
        )
        _append_events(
            events, free.board, free.payout, free.wins, free.multiplier, cfg.FREEGAME_TYPE
        )
        if free.payout > 0:
            running += free.payout
            events.append(
                {"index": len(events), "type": SET_TOTAL_WIN, "amount": running}
            )

        after = _multiplier_after(free)
        if after != free.multiplier:
            events.append(
                {
                    "index": len(events),
                    "type": UPDATE_GLOBAL_MULT,
                    "multiplier": after,
                }
            )

    events.append(
        {
            "index": len(events),
            "type": FREESPIN_END,
            "totalWin": outcome.bonus.total,
            "finalMultiplier": outcome.bonus.final_multiplier,
        }
    )
    return events


def _multiplier_after(free: FreeSpin) -> int:
    if any(cfg.WILD in reel for reel in free.board):
        return min(free.multiplier + cfg.BONUS.multiplier_add, cfg.BONUS.multiplier_cap)
    return free.multiplier


def build_events(outcome: SpinOutcome) -> List[Dict[str, Any]]:
    """The complete event sequence for one round.

    This function owns the running `index`: every branch above inserts a placeholder and
    the sequence is renumbered once at the end, so no branch can restart the counter.

    There is deliberately NO bypass event. Stake books are pre-computed and cannot carry a
    mid-round player decision; see `.omo/evidence/gate-answers.md` (G2-branch: no).
    """
    events = build_base_events(outcome)
    events.extend(build_bonus_events(outcome))
    events.append(
        {
            "index": 0,
            "type": SET_TOTAL_WIN,
            "amount": outcome.payout_multiplier,
        }
    )
    events.append(
        {
            "index": 0,
            "type": FINAL_WIN,
            "amount": outcome.payout_multiplier,
        }
    )

    for i, event in enumerate(events):
        event["index"] = i
    return events


def build_book(outcome: SpinOutcome) -> Dict[str, Any]:
    """One simulation as a book entry, in the SDK's books JSONL shape."""
    bonus_win = outcome.bonus.total if outcome.bonus else 0.0
    return {
        "id": outcome.sim_id,
        "payoutMultiplier": outcome.payout_multiplier,
        "events": build_events(outcome),
        "criteria": outcome.criteria,
        "baseGameWins": outcome.base_payout,
        "freeGameWins": bonus_win,
    }
