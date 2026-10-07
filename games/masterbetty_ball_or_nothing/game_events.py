"""BALL OR NOTHING - event emitters.

Events are constructed by the engine-agnostic core (ball_or_nothing.events) so that the
frontend and the SDK adapter share one event vocabulary - the same code produces the book
the RGS serves and the stream the demo plays. This module re-exports those builders under
the names the SDK's examples use, so game code reads consistently.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ball_or_nothing.events import (  # noqa: E402,F401
    FINAL_WIN,
    FREESPIN_END,
    FREESPIN_UPDATE,
    FS_TRIGGER,
    REVEAL,
    SET_TOTAL_WIN,
    SET_WIN,
    UPDATE_GLOBAL_MULT,
    WIN_INFO,
    build_base_events,
    build_bonus_events,
    build_book,
    build_events,
    win_level,
    win_positions,
)
