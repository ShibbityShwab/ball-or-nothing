"""BALL OR NOTHING - Stake Engine simulation entry point.

Run with: python games/masterbetty_ball_or_nothing/run.py

The SDK generates every outcome ahead of time and writes books, lookup tables, and
config JSON to library/. Compression is off here so the output stays human-readable
while the game is being developed; set it True for production (the RGS requires the
compressed books).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from src.books.book_writer import create_books  # noqa: E402
from src.config.config import generate_configs  # noqa: E402

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402


if __name__ == "__main__":
    num_threads = 1
    rust_threads = 8
    batching_size = 50000
    compression = False
    profiling = False

    num_sim_args = {
        "base": 100_000,
    }

    config = GameConfig()
    gamestate = GameState(config)

    create_books(
        gamestate,
        config,
        num_sim_args,
        batching_size,
        num_threads,
        compression,
        profiling,
    )
    generate_configs(gamestate)
