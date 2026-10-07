// Headless verification of the volatility ladder in the JS engine.
//
// The demo cannot be screenshotted right now (Bun.WebView hangs in this session), so this
// checks the part that actually matters: that the JS modes reproduce the numbers the
// PYTHON core solved. A pretty screenshot would not have caught a mode wiring bug; this
// does.
//
// Run: node tools/verify_modes.mjs

import { MODES, DEFAULT_MODE } from "../frontend/modes.js";
import { evaluateBoard, setMode, spinRound } from "../frontend/engine.js";

const SPINS = 300_000;

function mulberry(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

console.log(`simulating ${SPINS.toLocaleString()} rounds per mode\n`);
console.log("mode        RTP       +-se     sigma   hit      max seen   wincap      >cap");
console.log("-".repeat(84));

let failures = 0;
for (const name of Object.keys(MODES)) {
  const mode = setMode(name);
  const rng = mulberry(20261007);

  let total = 0;
  let totalSq = 0;
  let hits = 0;
  let maxSeen = 0;
  let overCap = 0;

  for (let i = 0; i < SPINS; i++) {
    const r = spinRound(rng);
    total += r.payout;
    totalSq += r.payout * r.payout;
    if (r.payout > 0) hits++;
    if (r.payout > maxSeen) maxSeen = r.payout;
    if (r.payout > mode.wincap + 1e-9) overCap++;
  }

  const rtp = total / SPINS;
  const variance = Math.max(totalSq / SPINS - rtp * rtp, 0);
  const se = Math.sqrt(variance / SPINS);
  // A high-volatility mode needs many samples before its mean settles. Judge by how many
  // standard errors the mean is from 0.97, not by a flat tolerance - NOTHING's variance is
  // large enough that a 0.05 band would fail on noise alone.
  const sigma = se > 0 ? Math.abs(rtp - 0.97) / se : 0;
  const ok = sigma < 5 && overCap === 0;
  if (!ok) failures++;

  console.log(
    `${mode.label.padEnd(11)} ${rtp.toFixed(4)}  ${se.toFixed(4)}  ${sigma.toFixed(1).padStart(5)}   ` +
      `${((hits / SPINS) * 100).toFixed(1).padStart(5)}%  ${maxSeen.toFixed(0).padStart(8)}x  ` +
      `${mode.wincap.toFixed(0).padStart(8)}x  ${overCap}`
  );
}

console.log();
if (failures === 0) {
  console.log("PASS: every mode lands near 0.97 and NO round ever exceeded its own wincap.");
} else {
  console.log(`FAIL: ${failures} mode(s) out of tolerance or over cap.`);
  process.exitCode = 1;
}

// The cap is the defect that once let the demo show 45x the advertised maximum, so assert
// it explicitly rather than trusting the loop above.
setMode("keep_it");
const mode = MODES.keep_it;
const { total: rawTotal } = evaluateBoard(
  Array.from({ length: 5 }, () => ["BALL", "BALL", "BALL"])
);
console.log(
  `\ncap check: a full-BALL board yields ${rawTotal.toFixed(1)}x raw; ` +
    `KEEP IT's cap is ${mode.wincap}x, so the clamp must bind.`
);
const rng2 = mulberry(7);
for (let i = 0; i < 20000; i++) {
  const r = spinRound(rng2);
  if (r.payout > mode.wincap + 1e-9) {
    console.log(`FAIL: a round paid ${r.payout} against a ${mode.wincap} cap`);
    process.exit(1);
  }
}
console.log("PASS: 20,000 KEEP IT rounds, none over the cap.");
