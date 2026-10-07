"""BALL OR NOTHING - game-specific executable helpers.

The engine's Executables layer holds shared actions; this subclass exists so any
game-specific action can live here without touching src/. The current game needs none,
because the whole round is one line of evaluation, so it is intentionally empty.
"""


class GameExecutables:
    pass
