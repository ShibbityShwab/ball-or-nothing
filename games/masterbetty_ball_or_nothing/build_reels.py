"""Generate the SDK reel CSVs from the core weight vectors.

The engine reads a reel strip as a list of symbol names per reel; the core expresses the
reels as weights. Deriving the CSV from the core keeps one source of truth, so a retune
cannot leave the published reels disagreeing with the verified RTP.

The strip is SHUFFLED rather than written grouped by symbol. A grouped strip would put the
same symbol on three consecutive stops, and any window-based draw over it would show three
identical symbols far more often than the weights say. Shuffling keeps the marginal exact
and removes that artefact even if the engine ever draws a window.

Run: python games/masterbetty_ball_or_nothing/build_reels.py
"""

import random
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ball_or_nothing import config as core  # noqa: E402

SHUFFLE_SEED = 0xB0BA


def expand(weights: Dict[str, int]) -> List[str]:
    strip: List[str] = []
    for symbol, count in weights.items():
        strip.extend([symbol] * count)
    return strip


def write_strip(target: Path, weights: Dict[str, int], reels: int) -> int:
    """Write a strip file: one row per stop, one column per reel.

    Each column is shuffled independently. Sharing one shuffle across columns would put
    the same symbol on every reel at a given stop, which is the worst possible
    correlation for a slot - five reels landing identically.
    """
    total = sum(weights.values())
    columns: List[List[str]] = []
    for reel in range(reels):
        strip = expand(weights)
        random.Random(SHUFFLE_SEED + reel).shuffle(strip)
        columns.append(strip)

    rows = [",".join(column[i] for column in columns) for i in range(total)]
    target.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return total


def main() -> int:
    out = Path(__file__).resolve().parent / "reels"
    out.mkdir(exist_ok=True)

    targets = (
        ("BR0.csv", core.REEL_WEIGHTS["default"]),
        ("FR0.csv", core.FREEGAME_WEIGHTS["default"]),
    )

    for filename, weights in targets:
        target = out / filename
        stops = write_strip(target, weights, core.NUM_REELS)
        total = sum(weights.values())
        parts = ", ".join(f"{s}={w / total:.1%}" for s, w in weights.items())
        print(f"wrote {target}")
        print(f"  {stops} stops x {core.NUM_REELS} reels: {parts}")
        assert stops == total, f"{filename}: strip is {stops} but weights total {total}"

    # Confirm no two columns are accidentally identical.
    br0 = (out / "BR0.csv").read_text(encoding="utf-8").strip().split("\n")
    columns = list(zip(*[row.split(",") for row in br0]))
    assert len({tuple(c) for c in columns}) == len(columns), "reel columns are correlated"
    print(f"  all {len(columns)} columns independently shuffled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
