// BALL OR NOTHING - pure game engine for the 5x3 board.
//
// No DOM, no rendering, no side effects: give it an RNG and it returns rounds and event
// streams. Split out from game.js so it can be executed headless by the parity test,
// which cross-checks every one of the 7^5 = 16,807 possible paylines against the Python
// math core.
//
// THIS FILE MIRRORS src/ball_or_nothing/spinner.py AND events.py. If you change the rules
// in one, change them in the other, or `pytest tests/test_js_parity.py` will fail - which
// is the point of having it.

import { DEFAULT_MODE, MODES } from "./modes.js";

export const SYMBOLS = ["BALL", "NUT", "SACK", "COIN", "LOSS", "WILD", "VAULT"];

// The active rung of the volatility ladder. Set through setMode(); every draw, every
// paytable lookup and the cap read from it, so switching rungs changes the whole machine
// and not just one part of it.
let activeMode = MODES[DEFAULT_MODE];

export function setMode(name) {
  const mode = MODES[name];
  if (!mode) throw new Error(`unknown mode: ${name}`);
  activeMode = mode;
  return mode;
}

export function getMode() {
  return activeMode;
}

export function modeList() {
  return Object.values(MODES);
}
export const PAYING = ["BALL", "NUT", "SACK", "COIN"];

export const NUM_REELS = 5;
export const NUM_ROWS = 3;

export const WEIGHTS = {
  BALL: 87,
  NUT: 122,
  SACK: 148,
  COIN: 192,
  LOSS: 386,
  WILD: 40,
  VAULT: 25,
};

export const FREE_WEIGHTS = {
  BALL: 100,
  NUT: 130,
  SACK: 150,
  COIN: 170,
  LOSS: 360,
  WILD: 70,
  VAULT: 20,
};

export const PAYTABLE = {
  "5:BALL": 272.3, "4:BALL": 5.0, "3:BALL": 0.4,
  "5:NUT": 100.0, "4:NUT": 2.5, "3:NUT": 0.2,
  "5:SACK": 50.0, "4:SACK": 1.5, "3:SACK": 0.15,
  "5:COIN": 20.0, "4:COIN": 1.0, "3:COIN": 0.1,
  "5:WILD": 272.3,
};

export const PAYLINES = [
  [1, 1, 1, 1, 1],
  [0, 0, 0, 0, 0],
  [2, 2, 2, 2, 2],
  [0, 1, 2, 1, 0],
  [2, 1, 0, 1, 2],
  [0, 0, 1, 0, 0],
  [2, 2, 1, 2, 2],
  [1, 0, 0, 0, 1],
  [1, 2, 2, 2, 1],
  [0, 1, 1, 1, 0],
];

export const BONUS = { multiplierAdd: 1, multiplierCap: 50 };
export const VAULT_TRIGGERS = { 3: 12, 4: 15, 5: 20 };
export const WINCAP = 25000;

// No mid-round wager. Stake books are static and pre-computed, so a player decision made
// during a round has no settlement path. See .omo/evidence/gate-answers.md (G2-branch: no).

export const WIN_LEVELS = [
  [0.0, 0],
  [1.0, 1],
  [5.0, 2],
  [20.0, 3],
  [80.0, 4],
  [250.0, 5],
];

export function weightedChoice(weights, rng) {
  const total = Object.values(weights).reduce((a, b) => a + b, 0);
  let roll = rng() * total;
  for (const [key, weight] of Object.entries(weights)) {
    if (roll < weight) return key;
    roll -= weight;
  }
  return Object.keys(weights)[0];
}

// One independent weighted draw per position. The Python core models the board the same
// way, which is what keeps the exact RTP valid for both.
export function drawBoard(rng, weights) {
  const w = weights || activeMode.weights;
  const board = [];
  for (let reel = 0; reel < NUM_REELS; reel++) {
    const column = [];
    for (let row = 0; row < NUM_ROWS; row++) column.push(weightedChoice(w, rng));
    board.push(column);
  }
  return board;
}

export function lineSymbols(board, lineIndex) {
  const rows = PAYLINES[lineIndex];
  return rows.map((row, reel) => board[reel][row]);
}

// Returns { symbol, kind, payout }. Leading wilds take the identity of the first real
// symbol; VAULT is a scatter and never substitutes, so it ends the run.
export function evaluateLine(symbols, paytable) {
  const table = paytable || activeMode.paytable;
  let runSymbol = null;
  let length = 0;

  for (const symbol of symbols) {
    if (symbol === "WILD") {
      length += 1;
      continue;
    }
    if (symbol === "VAULT") break;
    if (runSymbol === null) {
      runSymbol = symbol;
      length += 1;
    } else if (symbol === runSymbol) {
      length += 1;
    } else {
      break;
    }
  }

  if (runSymbol === null) runSymbol = "BALL";
  if (!PAYING.includes(runSymbol) || length < 3) return { symbol: runSymbol, kind: length, payout: 0 };

  const payout = table[`${length}:${runSymbol}`] || 0;
  return { symbol: runSymbol, kind: length, payout };
}

export function evaluateBoard(board, paytable) {
  const table = paytable || activeMode.paytable;
  const wins = [];
  let total = 0;
  for (let i = 0; i < PAYLINES.length; i++) {
    const { symbol, kind, payout } = evaluateLine(lineSymbols(board, i), table);
    if (payout > 0) {
      wins.push({ lineIndex: i, symbol, kind, payout });
      total += payout;
    }
  }
  return { total, wins };
}

export function countScatters(board) {
  let n = 0;
  for (const reel of board) for (const s of reel) if (s === "VAULT") n += 1;
  return n;
}

export function bonusSpinsFor(scatters) {
  return VAULT_TRIGGERS[scatters] || 0;
}

export function playBonus(rng, scatters) {
  const totalSpins = bonusSpinsFor(scatters);
  const spins = [];
  let multiplier = 1;
  let total = 0;

  for (let i = 0; i < totalSpins; i++) {
    const board = drawBoard(rng, activeMode.freeWeights);
    const { total: raw, wins } = evaluateBoard(board);
    const payout = raw * multiplier;
    total += payout;
    spins.push({ index: i, board, multiplier, payout, wins });
    if (board.some((reel) => reel.includes("WILD"))) {
      multiplier = Math.min(multiplier + BONUS.multiplierAdd, BONUS.multiplierCap);
    }
  }

  return { spins, total, finalMultiplier: multiplier, startSpins: totalSpins };
}

let simCounter = Math.floor(Math.random() * 100000);

export function spinRound(rng, forcedScatters) {
  const board = forcedScatters ? rigBoard(forcedScatters) : drawBoard(rng);
  const { total: basePayout, wins } = evaluateBoard(board);
  const scatters = countScatters(board);

  let bonus = null;
  let payout = basePayout;
  if (scatters >= 3) {
    bonus = playBonus(rng, scatters);
    payout = bonus.total;
  }

  return {
    id: simCounter++,
    board,
    basePayout,
    wins,
    payout: Math.min(payout, activeMode.wincap),
    scatters,
    bonus,
  };
}

// Used only by the demo QA flag: builds a board with a known number of scatters.
function rigBoard(scatterCount) {
  const board = [];
  for (let reel = 0; reel < NUM_REELS; reel++) {
    const column = [];
    for (let row = 0; row < NUM_ROWS; row++) column.push("LOSS");
    board.push(column);
  }
  const spots = [
    [0, 0], [1, 0], [2, 0], [3, 0], [4, 0], [0, 1], [1, 1], [2, 1], [3, 1], [4, 1],
  ];
  for (let i = 0; i < Math.min(scatterCount, spots.length); i++) {
    board[spots[i][0]][spots[i][1]] = "VAULT";
  }
  return board;
}

export function winLevel(m) {
  let level = 0;
  for (const [threshold, tier] of WIN_LEVELS) if (m >= threshold) level = tier;
  return level;
}

export function buildEvents(round) {
  const events = [];
  const push = (e) => events.push(e);

  push({ type: "reveal", board: round.board, gameType: "basegame" });

  if (round.bonus) {
    push({ type: "fsTrigger", scatters: round.scatters, spins: round.bonus.startSpins });
  } else if (round.basePayout > 0) {
    push({ type: "winInfo", totalWin: round.basePayout, wins: round.wins || [] });
    push({ type: "setWin", amount: round.basePayout, winLevel: winLevel(round.basePayout) });
  }

  if (round.bonus) {
    let running = 0;
    for (const free of round.bonus.spins) {
      push({
        type: "freespinUpdate",
        currentSpin: free.index + 1,
        totalSpins: round.bonus.spins.length,
        multiplier: free.multiplier,
      });
      push({ type: "reveal", board: free.board, gameType: "freegame" });
      if (free.payout > 0) {
        running += free.payout;
        push({ type: "winInfo", totalWin: free.payout, multiplier: free.multiplier, wins: free.wins });
        push({ type: "setWin", amount: free.payout, winLevel: winLevel(free.payout) });
        push({ type: "setTotalWin", amount: running });
      }
      const after = free.board.some((r) => r.includes("WILD"))
        ? Math.min(free.multiplier + BONUS.multiplierAdd, BONUS.multiplierCap)
        : free.multiplier;
      if (after !== free.multiplier) push({ type: "updateGlobalMult", multiplier: after });
    }
    push({ type: "freespinEnd", totalWin: round.bonus.total, finalMultiplier: round.bonus.finalMultiplier });
  }

  push({ type: "setTotalWin", amount: round.payout });
  push({ type: "finalWin", amount: round.payout });

  events.forEach((e, i) => (e.index = i));
  return events;
}
