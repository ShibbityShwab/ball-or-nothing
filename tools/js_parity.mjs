// Emits the JS engine's resolution of every possible payline as JSON, so the Python side
// can assert the two implementations agree. Run by tests/test_js_parity.py.
//
// 7 symbols over 5 reels = 16,807 lines, which is small enough to enumerate exhaustively
// rather than sampling - a sampled check could miss the one rule that drifted.
//
// Usage: node tools/js_parity.mjs

import {
  PAYING,
  PAYTABLE,
  SYMBOLS,
  WEIGHTS,
  FREE_WEIGHTS,
  PAYLINES,
  BONUS,
  VAULT_TRIGGERS,
  WINCAP,
  evaluateLine,
} from "../frontend/engine.js";

const rows = [];
for (const a of SYMBOLS)
  for (const b of SYMBOLS)
    for (const c of SYMBOLS)
      for (const d of SYMBOLS)
        for (const e of SYMBOLS) {
          const line = [a, b, c, d, e];
          const r = evaluateLine(line);
          rows.push({ line: line.join(","), symbol: r.symbol, kind: r.kind, payout: r.payout });
        }

process.stdout.write(
  JSON.stringify({
    paytable: PAYTABLE,
    paying: PAYING,
    weights: WEIGHTS,
    freeWeights: FREE_WEIGHTS,
    paylines: PAYLINES,
    bonus: BONUS,
    vaultTriggers: VAULT_TRIGGERS,
    wincap: WINCAP,
    rows,
  })
);
