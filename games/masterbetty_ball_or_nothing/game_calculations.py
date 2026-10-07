"""BALL OR NOTHING - game-specific board calculations.

Empty by design: win evaluation is a single payline check that the core resolves in
spinner._line_winner, and duplicating it here would create a second source of truth for
the payout rules.
"""


class GameCalculations:
    pass
