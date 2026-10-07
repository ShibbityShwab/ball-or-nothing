"""BALL OR NOTHING - Stake Engine GameConfig.

Every number that defines the machine is imported from the engine-agnostic core, so the
adapter can never drift from the verified math. Retune `src/ball_or_nothing/config.py`,
not this file.

Layout follows games/0_0_lines.

A NOTE ON WIN EVALUATION
------------------------
The SDK ships `Lines.get_lines()`, and this game deliberately does NOT use it. The RTP,
the hit rate and the max win in the repo README are computed against
`ball_or_nothing.spinner.evaluate_board`, and the frontend mirrors that same code. Running
the books through a second, differently-implemented line evaluator would make the shipped
math a different machine from the audited one - so the board is evaluated by the verified
core and the SDK is used for its event and wallet plumbing instead.
"""

from src.config.config import Config
from src.config.betmode import BetMode
from src.config.distributions import Distribution

from ball_or_nothing import config as core


class GameConfig(Config):
    def __init__(self):
        super().__init__()

        self.game_id = core.GAME_ID
        self.provider_number = core.PROVIDER_NUMBER
        self.working_name = core.WORKING_NAME
        self.wincap = core.WINCAP
        self.win_type = core.WIN_TYPE
        self.rtp = core.TARGET_RTP
        self.construct_paths()

        self.num_reels = core.NUM_REELS
        self.num_rows = [core.NUM_ROWS] * core.NUM_REELS

        self.paytable = core.Paytable().as_table()
        self.paylines = {index: rows for index, rows in core.PAYLINES.items()}

        self.special_symbols = {
            "wild": [core.WILD],
            "scatter": [core.VAULT],
        }

        # Scatter-count to free-spin award, per game type. Only the base game can trigger:
        # the BALLGAME does not retrigger, which keeps the bonus expectation closed form.
        self.freespin_triggers = {
            self.basegame_type: dict(core.VAULTS.triggers),
            self.freegame_type: {},
        }

        self.reels = {}
        for reel_id, filename in REEL_FILES.items():
            self.reels[reel_id] = self.read_reels_csv(f"{self.reels_path}/{filename}")

        pay = core.Paytable()
        top = pay.five_ball

        core_mode = core.bet_modes()[0]
        self.bet_modes = [
            BetMode(
                name=core_mode.name,
                cost=core_mode.cost,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=core_mode.auto_close_disabled,
                is_feature=core_mode.is_feature,
                is_buybonus=core_mode.is_buybonus,
                distributions=[
                    Distribution(
                        criteria=spec.criteria,
                        quota=spec.quota,
                        win_criteria=spec.win_criteria,
                        conditions={
                            **spec.conditions,
                            # Every distribution is pinned to this mode's reel files so the
                            # books come from the mode's reels and nothing else.
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                        },
                    )
                    for spec in core_mode.distributions
                ],
            )
        ]

        # Surfaced for the frontend config so the UI can label the top prize without
        # hard-coding it.
        self.five_of_a_kind_ball = top


REEL_FILES = {
    "BR0": "BR0.csv",
    "FR0": "FR0.csv",
}
