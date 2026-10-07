"""BALL OR NOTHING - engine overrides.

First in the MRO.

WHAT THIS FILE MUST NOT DO
--------------------------
It must NOT override `draw_board`. The board is drawn by the verified core
(`ball_or_nothing.spinner.draw_board`) and the game state calls that directly, so there is
exactly one board model in the product. An earlier revision of `config.py` claimed this
file overrode the draw "so the math and the implementation cannot disagree" - while the
file was a bare `pass`. Never reintroduce that claim: a comment asserting a guarantee the
code does not provide is the most dangerous thing a math product can ship.

Nothing needs overriding for this game: the default reset_book, seed, and win-manager
behaviour all apply. The file exists because the SDK's expected layout includes it, and
because the next mechanic that needs an override belongs here rather than in a patched
copy of src/.
"""

from src.state.state import State  # type: ignore  # provided by the Math SDK


class GameStateOverride(State):
    pass
