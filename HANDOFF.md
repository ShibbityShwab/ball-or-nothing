# BALL OR NOTHING — publisher handoff

**game_id:** `masterbetty_ball_or_nothing`
**status:** math verified and frozen; SDK adapter written but never executed (see §4)

This document is for whoever submits the game to Stake Engine. It says what is proven,
what is not, and what remains to be done. Nothing here is aspirational — every claim marked
**verified** was reproduced from the code in this repository.

---

## 1. What the game is

A 5-reel × 3-row slot, 10 paylines, seven symbols. Land three or more VAULTs to open the
BALLGAME (free spins with a climbing multiplier).

The differentiator is the **volatility ladder**. "BALL OR NOTHING" is not a wager — it is
the risk selector. The player chooses a rung at bet time, exactly like Plinko's
low/medium/high risk or Mines' mine count:

| Mode | RTP | Top prize | Max win | Character |
| --- | --- | --- | --- | --- |
| **KEEP IT** | 0.9700000 | 31.2× | 5,000× | wins constantly, small |
| **BALL** | 0.9699990 | 272.3× | 25,000× | the balanced machine |
| **NOTHING** | 0.9700000 | 2,585.5× | 250,000× | rarely, then enormously |

**Every rung is independently solved to 0.97.** No mode shares a constant with another, so
retuning one cannot silently move another — `test_math.py::TestVolatilityLadder` asserts it.

**BALL is not a re-derivation.** It ships the exact previously verified paytable and reels
verbatim, so the headline numbers in the README still hold on that rung. A test pins it.

### Why the decision is at bet time and not mid-round

This matters and was settled against the platform's own documentation, not by preference.
Stake Engine games are *"entirely of **static, pre-computed files**. There is no
server-side game logic executed at play time,"* and `is_feature` is documented as running
*"without requiring player interaction between rounds."*

An earlier revision offered a 50/50 double-or-lose wager *during* the BALLGAME. It was
removed. A mid-round decision has no settlement path, and a pre-computed two-branch
substitute does not fix it either — the client still has to tell the server which branch was
taken, and there is no mechanism for that. A "choice" between two pre-computed branches
would be theatre wearing a feature's jacket.

A decision made **at bet time** is a bet-mode selection. The round stays entirely
pre-computed. There is nothing to settle mid-round. That is why the ladder is legal where
the wager was not.

---

## 2. The verified math

| | |
| --- | --- |
| RTP | **0.969999** exact, by closed form |
| RTP split | base 0.5447 + bonus 0.4253 |
| BALLGAME trigger | 1 in 176 |
| Hit rate | ~19% of spins (1 in 5.2) |
| Max multiplier | 20× |

Reproduce all of it:

```bash
cd C:/Users/ShibbityShwab/Documents/GitHub/ball-or-nothing
python -m pip install -e .            # or: set PYTHONPATH=src
python -m ball_or_nothing.cli par     # the exact PAR sheet
python -m ball_or_nothing.cli modes   # the volatility ladder, each solved to 0.97
python -m ball_or_nothing.cli verify 200000   # closed form vs Monte Carlo
```

**Why it is exact, not estimated.** Three closed forms, no sampling:

- **Base** — `E[spin] = 10 × E[single line]`. Expectation is linear, so the ten correlated
  paylines do not matter; only the marginal of one line does.
- **Line** — summed exactly over all 7⁵ = 16,807 symbol sequences.
- **Bonus** — the multiplier after *n* wild-bearing spins is `1 + K` with
  `K ~ Binomial(n, p)`, so its expectation is closed form from the binomial MGF.

Monte Carlo is run *as a check* on those closed forms, and the tests assert they agree.

**RTP is solved, not guessed.** `cli tune 0.97` returns the top prize that lands exactly on
target. Re-run it after any reel or paytable change.

---

## 3. Test status

```
105 passed
```

That includes:

- **The JS/Python parity gate** — all 16,807 paylines resolved in both implementations and
  compared. **This hard-fails if no JS runtime is present.** It used to skip, which meant
  "105 passed" could have silently meant "parity unproven". Do not weaken it.
- **The volatility ladder** — every rung at exactly 0.97, monotonic max win, no shared
  constants, BALL reproducing the shipped machine.
- **The quotas** — asserted against the *measured* rates, so they cannot drift from the math.
- **The wager is gone** — tests assert no `run_bypass` parameter, no bypass field, no
  bypass events, and that the platform gate answer is still on record.

---

## 4. THE ONE THING THAT IS NOT VERIFIED

**The Stake Math SDK adapter has never been executed.**

`games/masterbetty_ball_or_nothing/` is written and its Python parses, but the SDK's
`requirements.txt` pins a **private** repository (`github.com/StakeEngine/math-sdk`), so it
cannot be installed here. Expect one round of API drift on first real run. Specifically
unverified:

- whether the import paths (`src.config.config`, `src.state.state`) match the real SDK;
- whether `Distribution` takes the exact keyword set used here;
- whether `check_repeat()` clears against the quotas now declared.

**The declared quotas are now derived, not invented.** The previous values contradicted the
machine — a win quota of 0.31 demanded 1.59× more winning rounds than the reels can produce,
so any generator honouring it had to miss or distort the reels. They now equal the measured
rates (win 0.195, bonus 0.005674, remainder 0.799). `TestQuotas` asserts this.

**Known structural risk, stated plainly:** `gamestate.run_spin` loops `while self.repeat`
and draws from a deterministic function of `sim`. If the SDK's loop expects the RNG to
advance between attempts, it will not. The clean fix — if the first run shows it — is to
precompute the book set in Python with the seeded core and have the SDK consume static
books, rather than asking the SDK's resample loop to produce randomness a deterministic
exact-math core was designed not to have.

---

## 5. What a submitter needs to do

1. **Clone the Math SDK** (you will need access to the private repo) and `make setup`.
2. **Run the adapter once.** Expect the drift in §4; fix and re-run.
3. **Run `make reference` / the SDK's own RTP verifier** against the generated books. The
   closed-form RTP is 0.97; the books must agree. If they do not, the adapter is generating
   boards its own way rather than calling the core — see §6.
4. **Generate the books** and submit.

### The parity of the books matters

The adapter deliberately **calls** `ball_or_nothing.spinner.draw_board` and
`evaluate_board` rather than reimplementing them. There must be exactly **one board model**
in the product. An earlier revision of `config.py` claimed the adapter overrode `draw_board`
"so the math and the implementation cannot disagree" — while `game_override.py` was a bare
`pass`. That claim is gone and the file now says what it does not do. If a future change
makes the adapter draw boards its own way, the shipped math stops being the audited math.

---

## 6. Honest caveats

- **This has not been audited or certified by anyone.** Passing 105 tests is not a
  regulatory review. The operator performs their own math verification before publication.
- **No git history exists.** The repository root (`Documents/GitHub`) is a shared parent
  folder with zero commits, containing unrelated projects. **Do not commit there** without
  deciding where this project's history should live. Provenance currently means "the code
  in this folder" and nothing stronger.
- **There is no LICENSE file.** Decide the licence before publishing.
- **The frontend demo is a simulator, not the shipped client.** It plays locally from the
  same core; it does not consume an RGS event stream. It is useful for QA and for showing
  the game, but it is not evidence that the production event contract works — only the
  parity gate speaks to that.
- **The published numbers must be regenerated if anything is retuned.** `cli modes` prints
  the ladder; `cli par` prints the machine. Any number in any document that is not printed
  by those commands is at risk of being stale — which is exactly how the hit rate in the
  README came to say 22.6% for a machine that produces ~19%.

---

## 7. Where the reasoning lives

| Path | What it is |
| --- | --- |
| `.omo/evidence/gate-answers.md` | the platform question and its answer, with evidence |
| `.omo/hyperplan-insight-bundle.md` | the adversarial review that produced the defect list |
| `.omo/plans/pre-market-claims-hardening.md` | the executable plan this handoff implements |

The adversarial review is worth reading before making design changes: it found several
defects that survived a green test suite, including a demo that could display a payout **45×
the advertised maximum**, and it is the reason the wager is gone rather than half-built.
