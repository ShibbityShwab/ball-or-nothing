// BALL OR NOTHING - Stake Engine event player.
//
// In production this file receives an `events` array from the RGS `play/` endpoint and
// plays it back. There is no game logic at play time: the outcome was already decided and
// pre-computed by the Math SDK before the player pressed the button.
//
// In demo mode (no RGS) it simulates locally using engine.js, which mirrors the Python
// math core. `pytest tests/test_js_parity.py` cross-checks every payline against Python.
//
// This file is presentation only: DOM, animation, and input.
//
// A NOTE ON THE BYPASS
// --------------------
// THE BYPASS is the VAULT-bypass minigame: a memory sequence you actually play, with your
// accuracy and time measured and shown. It always grants access, because the round was
// decided before you arrived - it is the entry ritual, not a gate.
//
// There is NO WAGER. Earlier revisions offered a 50/50 double-or-lose on the BALLGAME
// total, and it was removed: Stake books are static and pre-computed, so a mid-round
// player decision has no settlement path. Nothing here can change what a round pays,
// and nothing in the UI claims otherwise. See .omo/evidence/gate-answers.md.

import {
  BONUS,
  PAYLINES,
  SYMBOLS,
  countScatters,
  getMode,
  modeList,
  setMode,
  spinRound,
  winLevel,
} from "./engine.js";
import { brandMark, generatedArt, loadGeneratedAssets, symbolArt } from "./symbols.js";

const SPEED = {
  normal: { spin: 620, stagger: 90, bonusSpin: 380, bonusStagger: 60, settle: 320 },
  turbo: { spin: 240, stagger: 35, bonusSpin: 170, bonusStagger: 28, settle: 130 },
};

// Demo-only QA affordance: `?rig=bonus` forces the next spin to open the BALLGAME so the
// feature can be exercised without waiting out a 1-in-176 event. Production never runs
// this path - the RGS supplies the outcome.
const RIG = new URLSearchParams(location.search).get("rig");

const els = {
  reels: [...document.querySelectorAll(".reel-strip")],
  paylineLayer: document.getElementById("payline-layer"),
  win: document.getElementById("win"),
  winCell: document.querySelector(".readout-cell--win"),
  balance: document.getElementById("balance"),
  banner: document.getElementById("banner"),
  spin: document.getElementById("spin"),
  spinSub: document.getElementById("spin-sub"),
  ante: document.getElementById("ante"),
  fast: document.getElementById("fast"),
  status: document.getElementById("status"),
  particles: document.getElementById("particles"),
  tag: document.getElementById("tag"),
  autospinCounts: [...document.querySelectorAll(".autospin-count")],
  autospinStop: document.getElementById("autospin-stop"),
  autospinRemaining: document.getElementById("autospin-remaining"),
  betLevels: [...document.querySelectorAll(".bet-level")],
  bonusBar: document.getElementById("bonus-bar"),
  bonusSpins: document.getElementById("bonus-spins"),
  bonusMult: document.getElementById("bonus-mult"),
  bonusTotal: document.getElementById("bonus-total"),
  overlay: document.getElementById("overlay"),
  overlayInner: document.getElementById("overlay-inner"),
  feedList: document.getElementById("feed-list"),
  feedEmpty: document.getElementById("feed-empty"),
};

const TAGS = [
  "Ten lines. One question.",
  "The house edge is only 3%. The dignity edge is 100%.",
  "You had them when you sat down.",
  "Statistically, you are the product.",
];

let balanceCents = 100_000;
let betCents = 100;
let spinning = false;
let autospinRemaining = 0;
let autospinTotal = 0;
let autospinStopRequested = false;

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const money = (v) => v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// ---------------------------------------------------------------------------
// Board rendering
// ---------------------------------------------------------------------------

function symbolEl(name, compact) {
  const el = document.createElement("div");
  el.className = `symbol symbol--${name}${compact ? " symbol--compact" : ""}`;

  const src = generatedArt(name);
  if (src) {
    const img = document.createElement("img");
    img.className = "symbol-art";
    img.src = src;
    img.alt = "";
    el.append(img);
  } else {
    el.innerHTML = symbolArt(name);
  }

  const label = document.createElement("span");
  label.className = "symbol-label";
  label.textContent = name;
  el.append(label);
  return el;
}

function renderBoard(board) {
  els.reels.forEach((strip, r) => {
    strip.innerHTML = "";
    // Compact: one cell tall, so three of them fill the three-row window.
    for (const symbol of board[r]) strip.appendChild(symbolEl(symbol, true));
    strip.style.transition = "none";
    strip.style.transform = "translateY(0)";
  });
  clearPaylines();
}

function clearPaylines() {
  els.paylineLayer.innerHTML = "";
  for (const el of document.querySelectorAll(".symbol.is-paying")) {
    el.classList.remove("is-paying");
  }
}

// Mark the symbols that actually paid so the win is unmissable on a busy board. The
// visible row for a landed reel is the last three children of its strip.
function markPaying(wins) {
  for (const win of wins) {
    const rows = PAYLINES[win.lineIndex];
    const covered = Math.min(win.kind, els.reels.length);
    for (let reel = 0; reel < covered; reel++) {
      const visible = [...els.reels[reel].children].slice(-3);
      const el = visible[rows[reel]];
      if (el) el.classList.add("is-paying");
    }
  }
}

// Draw the winning lines as polylines through the grid. The viewBox is 0-500 by 0-300 so
// each reel is 100 wide and each row 100 tall; the centre of (reel, row) is what we want.
// Only the reels the win actually covers get a point - drawing the whole payline would
// light reels that never paid.
function drawPaylines(wins) {
  clearPaylines();
  if (wins && wins.length) markPaying(wins);
  const ns = "http://www.w3.org/2000/svg";
  const palette = ["#f4b942", "#5cd97a", "#7bd88f", "#d4763f", "#7aa2f7"];
  wins.slice(0, 5).forEach((win, i) => {
    const rows = PAYLINES[win.lineIndex];
    const covered = Math.min(win.kind, rows.length);
    const points = rows
      .slice(0, covered)
      .map((row, reel) => `${reel * 100 + 50},${row * 100 + 50}`)
      .join(" ");
    const line = document.createElementNS(ns, "polyline");
    line.setAttribute("points", points);
    line.setAttribute("stroke", palette[i % palette.length]);
    line.setAttribute("stroke-width", "4");
    line.setAttribute("fill", "none");
    line.setAttribute("stroke-linecap", "round");
    line.setAttribute("opacity", "0.9");
    line.classList.add("payline-path");
    els.paylineLayer.appendChild(line);
  });
}

// ---------------------------------------------------------------------------
// Reel animation
// ---------------------------------------------------------------------------

function stripSymbols(finalColumn, length) {
  const decoys = SYMBOLS.filter((s) => s !== "VAULT");
  const out = [];
  for (let i = 0; i < length; i++) out.push(decoys[Math.floor(Math.random() * decoys.length)]);
  return out.concat(finalColumn);
}

function runReel(strip, finalColumn, prepend, duration) {
  const seq = stripSymbols(finalColumn, prepend);
  strip.innerHTML = "";
  for (const name of seq) strip.appendChild(symbolEl(name, true));
  strip.style.transition = "none";

  const cell = strip.firstElementChild.offsetHeight || 44;
  const distance = -(seq.length - finalColumn.length) * cell;
  strip.style.transform = "translateY(0)";

  return new Promise((resolve) => {
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      strip.style.transition = "none";
      resolve();
    };
    strip.addEventListener("transitionend", finish, { once: true });
    setTimeout(finish, duration + 150);
    requestAnimationFrame(() => {
      strip.style.transition = `transform ${duration}ms cubic-bezier(0.16, 0.84, 0.32, 1)`;
      strip.style.transform = `translateY(${distance}px)`;
    });
  });
}

async function animateBoard(board, timing, prepend = 6) {
  await Promise.all(
    els.reels.map((strip, r) => runReel(strip, board[r], prepend, timing.spin + r * timing.stagger))
  );
}

// ---------------------------------------------------------------------------
// Effects
// ---------------------------------------------------------------------------

function burst(count, colour) {
  const rect = document.getElementById("cabinet").getBoundingClientRect();
  for (let i = 0; i < count; i++) {
    const p = document.createElement("div");
    p.className = "particle";
    p.style.left = `${50 + (Math.random() - 0.5) * 46}%`;
    p.style.top = `${rect.top + rect.height * 0.7}px`;
    p.style.background = colour;
    p.style.setProperty("--dx", `${(Math.random() - 0.5) * 620}px`);
    p.style.setProperty("--dy", `${60 + Math.random() * 280}px`);
    p.style.setProperty("--dur", `${1.1 + Math.random() * 1.2}s`);
    els.particles.appendChild(p);
    setTimeout(() => p.remove(), 2500);
  }
}

function setBanner(text, klass) {
  els.banner.textContent = text;
  els.banner.className = `banner${klass ? ` ${klass}` : ""}`;
}

function showWin(amount) {
  els.win.textContent = money(amount);
  els.winCell.classList.toggle("is-zero", amount === 0);
}

function addFeedEntry(text, tier) {
  if (els.feedEmpty) {
    els.feedEmpty.remove();
    els.feedEmpty = null;
  }
  const li = document.createElement("li");
  li.className = `feed-item feed-item--${tier}`;
  li.textContent = text;
  els.feedList.prepend(li);
  while (els.feedList.children.length > 7) els.feedList.lastElementChild.remove();
}

// ---------------------------------------------------------------------------
// THE BYPASS - the NoPixel-style access minigame
// ---------------------------------------------------------------------------

const HACK_TILES = 16;
const HACK_STEPS = 4;

function buildHackGrid() {
  const grid = document.createElement("div");
  grid.className = "hack-grid";
  for (let i = 0; i < HACK_TILES; i++) {
    const tile = document.createElement("button");
    tile.type = "button";
    tile.className = "hack-tile";
    tile.dataset.index = String(i);
    tile.disabled = true;
    grid.appendChild(tile);
  }
  return grid;
}

// A real sequence-memory game: the pattern flashes, you repeat it, your time and accuracy
// are measured and shown. It always grants access - see the note at the top of the file.
//
// It builds INSIDE the stable #overlay-inner container rather than replacing the overlay's
// markup: clobbering overlay.innerHTML once destroyed that container and every later write
// went to a detached node, leaving the round waiting on buttons that were never rendered.
function playHack(timing) {
  return new Promise((resolve) => {
    const sequence = Array.from({ length: HACK_STEPS }, () => Math.floor(Math.random() * HACK_TILES));

    els.overlayInner.innerHTML = `
      <div class="hack">
        <div class="hack-head">
          <span class="hack-kicker">BREACH PROTOCOL</span>
          <span class="hack-title">THE BYPASS</span>
          <span class="hack-sub" id="hack-sub">memorise the sequence</span>
        </div>
      </div>`;

    const hack = els.overlayInner.querySelector(".hack");
    const grid = buildHackGrid();
    hack.appendChild(grid);
    const sub = els.overlayInner.querySelector("#hack-sub");

    const tiles = [...grid.children];
    let flashing = true;

    const flash = async (index, ms) => {
      tiles[index].classList.add("is-lit");
      await wait(ms);
      tiles[index].classList.remove("is-lit");
    };

    const runFlash = async () => {
      await wait(400);
      for (const index of sequence) {
        await flash(index, Math.max(160, timing.settle * 0.7));
        await wait(Math.max(90, timing.settle * 0.35));
      }
      flashing = false;
      sub.textContent = "repeat it";
      tiles.forEach((t) => (t.disabled = false));
      startedAt = performance.now();
    };

    let startedAt = 0;
    let step = 0;
    let mistakes = 0;

    tiles.forEach((tile) => {
      tile.addEventListener("click", async () => {
        if (flashing) return;
        const index = Number(tile.dataset.index);

        if (index === sequence[step]) {
          tile.classList.add("is-good");
          setTimeout(() => tile.classList.remove("is-good"), 220);
          step += 1;
          if (step === sequence.length) {
            const elapsed = Math.round(performance.now() - startedAt);
            tiles.forEach((t) => (t.disabled = true));
            sub.textContent = "access granted";
            grid.classList.add("is-open");
            const rating = mistakes === 0 && elapsed < 4000 ? "CLEAN" : "MESSY";
            const badge = document.createElement("div");
            badge.className = "hack-badge";
            badge.textContent = `${rating} EXTRACTION \u00b7 ${(elapsed / 1000).toFixed(2)}s`;
            hack.appendChild(badge);
            setTimeout(() => resolve({ elapsed, mistakes, rating }), Math.max(500, timing.settle * 2));
          }
        } else {
          mistakes += 1;
          tile.classList.add("is-bad");
          setTimeout(() => tile.classList.remove("is-bad"), 300);
        }
      });
    });

    runFlash();
  });
}

// ---------------------------------------------------------------------------
// Round playback
// ---------------------------------------------------------------------------

async function playBonusRound(round, timing) {
  els.overlay.hidden = false;
  els.overlayInner.innerHTML = `
    <div class="overlay-kicker">VAULT BREACHED</div>
    <div class="overlay-title">BALLGAME</div>
    <div class="overlay-sub">${round.bonus.startSpins} free spins &middot; multiplier climbs on every wild</div>`;
  burst(50, "#f4b942");
  await wait(timing.settle * 3);
  els.overlay.hidden = true;

  els.bonusBar.hidden = false;
  els.bonusTotal.textContent = "0.00";
  els.bonusMult.textContent = "1x";

  let running = 0;
  for (const free of round.bonus.spins) {
    els.bonusSpins.textContent = `${free.index + 1} / ${round.bonus.spins.length}`;
    els.bonusMult.textContent = `${free.multiplier}x`;
    els.bonusMult.classList.toggle("is-hot", free.multiplier > 1);

    await animateBoard(free.board, timing, 3);

    if (free.payout > 0) {
      running += free.payout;
      els.bonusTotal.textContent = money(running);
      showWin(free.payout);
      drawPaylines(free.wins);
      els.bonusBar.classList.remove("flash");
      void els.bonusBar.offsetWidth;
      els.bonusBar.classList.add("flash");
      if (free.multiplier >= 8) burst(30, "#f4b942");
      await wait(timing.settle);
      clearPaylines();
    } else {
      await wait(timing.bonusSpin * 0.5);
    }
  }

  els.bonusBar.hidden = true;
  return round.bonus.total;
}

// The wager is gone. Stake books are static and pre-computed, so a mid-round decision has
// no settlement path - see .omo/evidence/gate-answers.md (G2-branch: no). The hack survives
// as an entry ritual; nothing after it can change what the round pays.

async function playRound(round, timing) {
  clearPaylines();
  els.banner.className = "banner";
  setBanner("...");

  await animateBoard(round.board, timing);

  let total = round.payout;

  if (round.bonus) {
    els.overlay.hidden = false;
    els.overlayInner.innerHTML = "";
    await playHack(timing);
    els.overlay.hidden = true;

    total = await playBonusRound(round, timing);

    setBanner(
      total > 0 ? `BALLGAME PAID  ${total.toFixed(2)}x` : "BALLGAME PAID  NOTHING",
      total > 0 ? "is-jackpot" : "is-loss"
    );
    if (total > 0) {
      burst(70, "#f4b942");
      addFeedEntry(`BALLGAME  ${total.toFixed(2)}x`, total >= 200 ? "gold" : "win");
    }
    await wait(timing.settle * 2);
  } else if (round.basePayout > 0) {
    drawPaylines(round.wins || []);
    showWin(round.basePayout);
    const best = Math.max(...round.wins.map((w) => w.payout));
    setBanner(`WIN  ${round.basePayout.toFixed(2)}x`, best >= 50 ? "is-jackpot" : "is-win");
    if (best >= 50) burst(60, "#f4b942");
    if (round.basePayout >= 20) addFeedEntry(`LINE WIN  ${round.basePayout.toFixed(2)}x`, best >= 50 ? "gold" : "win");
    await wait(timing.settle);
  } else {
    setBanner("NOTHING.", "is-loss");
    els.tag.textContent = TAGS[Math.floor(Math.random() * TAGS.length)];
  }

  // THE ONE CAP. Read from the ACTIVE MODE, never a module constant: three separate cap
  // semantics - core, PAR sheet and frontend - is what once let the demo display a payout
  // 45x the advertised maximum.
  const capped = Math.min(total, getMode().wincap);
  showWin(capped);
  return capped;
}

// ---------------------------------------------------------------------------
// Spin control
// ---------------------------------------------------------------------------

async function doSpin() {
  if (spinning) return;
  spinning = true;
  els.spin.disabled = true;

  const timing = els.fast.checked ? SPEED.turbo : SPEED.normal;
  const forced = RIG === "bonus" && !globalThis.__rigUsed ? 3 : null;
  if (forced) globalThis.__rigUsed = true;

  const round = spinRound(Math.random, forced);

  balanceCents -= betCents;
  els.status.textContent = "Spinning...";
  els.balance.textContent = money(balanceCents / 100);

  const total = await playRound(round, timing);

  balanceCents += Math.round(total * betCents);
  els.balance.textContent = money(balanceCents / 100);
  showWin(total * (betCents / 100));

  els.status.textContent = round.bonus
    ? `Vault breached \u00b7 ${countScatters(round.board)} scatters \u00b7 paid ${total.toFixed(2)}x`
    : `Round ${round.id} \u00b7 ${total > 0 ? "something back" : "the house thanks you"}`;

  spinning = false;
  els.spin.disabled = false;
}

function setAutospinControls(active) {
  els.autospinCounts.forEach((b) => (b.disabled = active));
  els.autospinStop.hidden = !active;
  els.autospinRemaining.hidden = !active;
  els.betLevels.forEach((b) => (b.disabled = active));
  if (!active) {
    els.autospinCounts.forEach((b) => b.classList.remove("is-selected"));
    els.autospinRemaining.textContent = "";
  }
}

async function runAutospin(count) {
  autospinTotal = count;
  autospinRemaining = count;
  autospinStopRequested = false;
  els.autospinStop.disabled = false;
  setAutospinControls(true);

  while (autospinRemaining > 0) {
    if (autospinStopRequested) break;
    if (balanceCents < betCents) {
      setBanner("OUT OF FUNDS.", "is-loss");
      els.status.textContent = "Autospin stopped: not enough balance for another bet.";
      break;
    }
    els.autospinRemaining.textContent = `${autospinTotal - autospinRemaining + 1} / ${autospinTotal}`;
    await doSpin();
    autospinRemaining--;
  }

  const completed = autospinTotal - autospinRemaining;
  const stopped = autospinStopRequested && autospinRemaining > 0;
  setAutospinControls(false);
  autospinRemaining = 0;
  autospinTotal = 0;
  autospinStopRequested = false;

  els.status.textContent = stopped
    ? `Autospin stopped after ${completed} spin${completed === 1 ? "" : "s"}.`
    : `Autospin finished: ${completed} spin${completed === 1 ? "" : "s"}.`;
}

function setBet(value) {
  betCents = Math.round(value * 100);
  els.ante.textContent = money(value);
  els.spinSub.textContent = `${money(value)} bet`;
  els.betLevels.forEach((b) => b.classList.toggle("is-selected", Number(b.dataset.bet) === value));
}

els.spin.addEventListener("click", doSpin);

els.betLevels.forEach((button) => {
  button.addEventListener("click", () => {
    if (spinning || autospinRemaining > 0) return;
    setBet(Number(button.dataset.bet));
  });
});

els.autospinCounts.forEach((button) => {
  button.addEventListener("click", () => {
    if (spinning || autospinRemaining > 0) return;
    els.autospinCounts.forEach((b) => b.classList.toggle("is-selected", b === button));
    runAutospin(Number(button.dataset.count));
  });
});

els.autospinStop.addEventListener("click", () => {
  autospinStopRequested = true;
  els.autospinStop.disabled = true;
  els.autospinRemaining.textContent = "stopping...";
});

document.addEventListener("keydown", (e) => {
  if ((e.code === "Space" || e.code === "Enter") && !els.spin.disabled && autospinRemaining === 0) {
    e.preventDefault();
    doSpin();
  }
});

await loadGeneratedAssets();

renderBoard([
  ["BALL", "NUT", "SACK"],
  ["NUT", "COIN", "BALL"],
  ["SACK", "BALL", "NUT"],
  ["COIN", "SACK", "BALL"],
  ["BALL", "NUT", "COIN"],
]);
showWin(0);
els.balance.textContent = money(balanceCents / 100);
setBet(1);

// The volatility ladder. Choosing a rung is a bet-time decision, so the round stays fully
// pre-computed - which is why this is legal where the old mid-round wager was not.
const modeLevels = document.getElementById("mode-levels");
for (const mode of modeList()) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "mode-level";
  button.dataset.mode = mode.name;
  button.innerHTML = `<span class="mode-name">${mode.label}</span>` +
    `<span class="mode-blurb">${mode.blurb}</span>` +
    `<span class="mode-max">up to ${mode.wincap.toLocaleString("en-US")}x</span>`;
  modeLevels.appendChild(button);
}

function applyMode(name) {
  const mode = setMode(name);
  for (const b of modeLevels.children) {
    b.classList.toggle("is-selected", b.dataset.mode === name);
  }
  const foot = document.getElementById("foot-max");
  if (foot) foot.textContent = `${mode.wincap.toLocaleString("en-US")}x`;
  els.status.textContent = `${mode.label}: ${mode.blurb}.`;
  const maxEl = document.querySelector(".maxwin-value");
  if (maxEl) maxEl.innerHTML = `${mode.wincap.toLocaleString("en-US")}<small>x</small>`;
}

modeLevels.addEventListener("click", (e) => {
  const button = e.target.closest(".mode-level");
  if (!button) return;
  if (spinning || autospinRemaining > 0) return;
  applyMode(button.dataset.mode);
});

applyMode(modeList()[1] ? modeList()[1].name : modeList()[0].name);

const brandSlot = document.getElementById("brand-mark");
if (brandSlot) {
  const brandSrc = generatedArt("BRAND");
  if (brandSrc) {
    const img = document.createElement("img");
    img.className = "brand-art";
    img.src = brandSrc;
    img.alt = "";
    brandSlot.appendChild(img);
  } else {
    brandSlot.innerHTML = brandMark(56);
  }
}
