"""Cross-check the JavaScript engine against the Python math core.

The frontend reimplements the win rules so the demo can run with no server, which means
the payout logic exists twice. This test is what stops the two from drifting: it runs
frontend/engine.js in a real JS runtime, resolves every one of the 16,807 possible
paylines, and asserts each payout and symbol matches Python's.

Without this, the demo could quietly disagree with the game that actually pays money.

Skips (rather than fails) when no JS runtime is available, so the suite still runs on a
machine that only has Python.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import pytest

from ball_or_nothing import config as cfg
from ball_or_nothing.spinner import evaluate_line

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "js_parity.mjs"


def _runtime() -> List[str] | None:
    for candidate in ("bun", "node"):
        exe = shutil.which(candidate)
        if exe:
            return [exe, str(SCRIPT)]
    return None


@pytest.fixture(scope="module")
def js_payload() -> Dict[str, Any]:
    argv = _runtime()
    if argv is None:
        # HARD FAIL, never skip. A parity gate that passes by not running is worse than no
        # gate at all: "92 passed" would silently mean "parity unproven" on any machine
        # without a JS runtime. Install bun or node; do not weaken this.
        pytest.fail(
            "no JS runtime found, so the JS/Python parity check cannot run. "
            "Install bun or node - a green suite that skipped this proves nothing."
        )

    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        pytest.fail(f"js parity script failed:\n{result.stderr}")
    return json.loads(result.stdout)


def test_js_agrees_on_every_payline(js_payload: Dict[str, Any]) -> None:
    table = cfg.Paytable().as_table()
    mismatches = []

    for row in js_payload["rows"]:
        symbols = tuple(row["line"].split(","))
        symbol, kind, payout = evaluate_line(symbols, table)
        if abs(payout - row["payout"]) > 1e-9 or symbol != row["symbol"] or kind != row["kind"]:
            mismatches.append(
                f"{row['line']}: js={row['symbol']}|{row['kind']}|{row['payout']} "
                f"py={symbol}|{kind}|{payout}"
            )

    assert not mismatches, (
        f"JS/Python win-rule drift on {len(mismatches)} lines:\n" + "\n".join(mismatches[:20])
    )


def test_all_paylines_are_covered(js_payload: Dict[str, Any]) -> None:
    assert len(js_payload["rows"]) == len(cfg.SYMBOLS) ** cfg.NUM_REELS


def test_js_paytable_matches_python(js_payload: Dict[str, Any]) -> None:
    expected = {f"{k}:{s}": v for (k, s), v in cfg.Paytable().as_table().items()}
    for key, value in expected.items():
        assert js_payload["paytable"][key] == pytest.approx(value), key


def test_js_weights_match_python(js_payload: Dict[str, Any]) -> None:
    assert js_payload["weights"] == cfg.REEL_WEIGHTS["default"]
    assert js_payload["freeWeights"] == cfg.FREEGAME_WEIGHTS["default"]


def test_js_paylines_match_python(js_payload: Dict[str, Any]) -> None:
    for index, rows in cfg.PAYLINES.items():
        assert js_payload["paylines"][index] == rows, index


def test_js_bonus_config_matches_python(js_payload: Dict[str, Any]) -> None:
    assert js_payload["bonus"]["multiplierAdd"] == cfg.BONUS.multiplier_add
    assert js_payload["bonus"]["multiplierCap"] == cfg.BONUS.multiplier_cap
    # The wager is gone; the JS payload must not carry wager config either.
    assert "bypass" not in js_payload


def test_js_vault_triggers_match_python(js_payload: Dict[str, Any]) -> None:
    assert {int(k): v for k, v in js_payload["vaultTriggers"].items()} == cfg.VAULTS.triggers


def test_js_wincap_matches_python(js_payload: Dict[str, Any]) -> None:
    assert js_payload["wincap"] == cfg.WINCAP


def test_js_paying_symbols_match_python(js_payload: Dict[str, Any]) -> None:
    assert js_payload["paying"] == list(cfg.PAYING_SYMBOLS)


def test_the_js_engine_plays_every_mode_at_the_closed_form_rtp() -> None:
    """Run the JS engine headless and check each mode against 0.97.

    This is the parity gate for the VOLATILITY LADDER rather than for line evaluation: the
    demo must play the numbers the Python closed form produced. Judged in sigmas, not a
    flat band - a high-volatility mode has a large standard error and a fixed tolerance
    would fail on sampling noise, which is how a green check quietly means nothing.
    """
    runtime = _runtime()
    if runtime is None:
        pytest.fail("no JS runtime: the ladder parity check cannot run")

    script = ROOT / "tools" / "verify_modes.mjs"
    result = subprocess.run(
        [runtime[0], str(script)], cwd=ROOT, capture_output=True, text=True, timeout=300
    )
    assert result.returncode == 0, f"JS mode verification failed:\n{result.stdout}\n{result.stderr}"
    assert "PASS: every mode lands near 0.97" in result.stdout
    assert "PASS: 20,000 KEEP IT rounds, none over the cap" in result.stdout

    # Every mode must have reported zero rounds over its own cap. The trailing column is
    # the count, so a line not ending in 0 means a round blew through a wincap.
    for line in result.stdout.splitlines():
        if any(line.startswith(m) for m in ("KEEP IT", "BALL", "NOTHING")):
            assert line.rstrip().endswith("0"), f"a round exceeded a wincap: {line}"
