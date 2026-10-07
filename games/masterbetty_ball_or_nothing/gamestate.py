"""BALL OR NOTHING - Stake Engine game state.

The core resolves a whole round deterministically from the simulation number: base board,
BALLGAME if it triggered, and the wager if it was taken. This adapter feeds that result
through the SDK's wallet manager and event book, so the books carry the audited math while
the plumbing stays the engine's.

That is why run_freespin() is a no-op here: the BALLGAME is resolved inside the same
deterministic round rather than driven spin-by-spin by the engine. Both produce the same
book, and doing it this way keeps the shipped result identical to the one the RTP was
verified against.

See the note in game_config.py for why the SDK's own line evaluator is not used.

UNRUN. github.com/StakeEngine/math-sdk is private, so this has never been executed against
the engine. Written from the published docs; expect one round of API drift on first run.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

# The math core lives in src/ at the repo root; the SDK imports games/<id>/ directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from game_override import GameStateOverride  # noqa: E402

from ball_or_nothing import config as core  # noqa: E402
from ball_or_nothing.events import build_events  # noqa: E402
from ball_or_nothing.spinner import LineWin, SpinOutcome, spin as core_spin  # noqa: E402


def win_payload(win: LineWin) -> Dict[str, Any]:
    """One line win in the shape the wallet manager and win events expect."""
    return {
        "symbol": win.symbol,
        "kind": win.kind,
        "win": win.payout,
        "positions": [
            {"reel": reel, "row": core.PAYLINES[win.line_index][reel]}
            for reel in range(min(win.kind, core.NUM_REELS))
        ],
        "meta": {"lineIndex": win.line_index},
    }


class GameState(GameStateOverride):
    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()

            outcome = core_spin(sim)
            self._outcome = outcome

            self.board = outcome.board
            self.win_data = {
                "totalWin": outcome.base_payout,
                "wins": [win_payload(w) for w in outcome.wins],
            }
            self.win_manager.update_spinwin(outcome.base_payout)
            self.win_manager.update_gametype_wins(self.basegame_type)

            if outcome.bonus is not None:
                self.tot_fs = outcome.bonus.spin_count
                self.fs = outcome.bonus.spin_count
                self.global_mult = outcome.bonus.final_multiplier
                self.win_manager.update_spinwin(outcome.bonus.total)
                self.win_manager.update_gametype_wins(self.freegame_type)

            for event in build_events(outcome):
                self.book.add_event(event)

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self):
        """Unused: the BALLGAME is resolved as part of the deterministic round.

        Present because the engine's contract expects the method on the class.
        """
        return
