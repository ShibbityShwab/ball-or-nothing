# BALL OR NOTHING

A Stake Engine slot game. **5 reels, 3 rows, 10 paylines.** Land three or more VAULTs and
you breach the BALLGAME. Play it well enough and you get offered a way to lose everything.

> **Status: math core, frontend, and tests are built and verified. The Stake SDK adapter is
> written but has not been executed against the real Math SDK** (that repo is private).

```
src/ball_or_nothing/
    config.py        Symbols, weights, paytable, paylines, BALLGAME
    spinner.py       Line evaluation, board draw, bonus round
    par.py           Closed-form RTP + Monte Carlo verifier + solver
    events.py        The event stream the RGS returns and the frontend plays
    cli.py           `python -m ball_or_nothing.cli par | verify | demo | tune`
tests/               53 math + 28 event-stream + 9 JS/Python parity tests
frontend/
    engine.js        Pure game engine (mirrors the Python math) - no DOM
    symbols.js       Symbol artwork, hand-authored SVG on a shared lighting contract
    game.js          Event player: rendering, paylines, the BYPASS minigame
tools/js_parity.mjs  Runs the JS engine headless for the parity test
games/masterbetty_ball_or_nothing/   Stake Engine Math SDK game directory
```

## The game

| Symbol | Role |
| - | - |
| BALL | top payer - 272.3x for five |
| NUT / SACK / COIN | descending payers |
| LOSS | blank |
| WILD | substitutes; advances the BALLGAME multiplier |
| VAULT | scatter - three or more opens the BALLGAME |

Lines run left to right from reel 0 and pay the longest run of one symbol, wilds
substituting. VAULT never substitutes and breaks a line.

| Stat | Value |
| - | - |
| RTP | **97.00%** (base 0.5447 + bonus 0.4253) |
| Hit rate | ~19% of spins (1 in 5.2) |
| BALLGAME | **1 in 176** |
| Max multiplier | 20x |
| **Max win** | **25,000x** |

### The BALLGAME
12 / 15 / 20 free spins for 3 / 4 / 5 VAULTs, on richer reels. A multiplier starts at 1x
and gains +1 for every free spin containing a wild, to a cap of 50.

### THE BYPASS — the skill layer

**One thing, not two.** THE BYPASS is a sequence-memory minigame in the NoPixel thermite
style: a pattern flashes, you repeat it, your accuracy and time are measured and shown.

It **always grants access**, because the round was decided before you arrived. It is the
entry ritual, not a gate, and nothing in the UI claims otherwise.

**There is no wager.** Earlier revisions offered a 50/50 double-or-lose on the BALLGAME
total. It was removed, and the reason is structural rather than a matter of taste: Stake
Engine books are *entirely static, pre-computed files* with *no server-side game logic
executed at play time*, so a decision made mid-round has no settlement path. A
pre-computed branch does not fix that either — the client still has to tell the server
which branch was taken, and there is no mechanism for that. A "choice" between two
pre-computed branches would be theatre wearing a feature's jacket.

Full reasoning and the platform evidence: `.omo/evidence/gate-answers.md`.

## Why the math is exact

Three pieces, no simulation required:

* **Base** — `E[spin] = 10 × E[single line]`. Expectation is linear, so ten correlated
  paylines do not matter; only the marginal of one line does.
* **Line** — `E[line] = Σ over all 7^5 = 16,807 symbol sequences`, weighted exactly.
* **Bonus** — the multiplier after n wild-bearing spins is `1 + K` with `K ~ Binomial(n, p)`,
  and its expectation is closed form.

`monte_carlo()` independently plays real rounds and must agree; the tests assert it.

```bash
python -m ball_or_nothing.cli par            # exact PAR sheet
python -m ball_or_nothing.cli verify 200000  # closed form vs Monte Carlo
```

Two constants had to be found by search, not chosen: the wild weight and the paying-symbol
density. Ten paylines push the hit rate past 80% if the reels are too dense, and a 10% wild
made five-of-a-kind 1 in 10,824 per line — ten times too common to pay a headline.

## Stake SDK

Stake Engine games are **static, pre-computed files**: the Math SDK simulates every outcome
ahead of time and the RGS returns a pre-generated `events` array. See the
[game format docs](https://mintlify.wiki/StakeEngine/math-sdk/concepts/game-format).

`games/masterbetty_ball_or_nothing/` follows that layout. **It has not been run** — the
SDK's `requirements.txt` pins a private repository, so the engine cannot be installed here.

**No open platform questions remain.** The one that did — whether a Stake book can branch
on a mid-round player decision — was answered from the platform's own documentation
(no). See `.omo/evidence/gate-answers.md`.

## The artwork

Every symbol is hand-authored SVG in `frontend/symbols.js`, built on one shared lighting
contract (warm key light upper-left, cool rim light lower-right, navy ambient from below,
one bold specular each). That is what makes seven different objects read as a single set.

SVG rather than bitmaps because the whole set is a few kilobytes, stays sharp at any size,
and needs no asset pipeline. The earlier build drew Unicode characters (● ○ ◆ ▲ ✕ ★ ■),
which is exactly why it looked like a placeholder.

Symbols marked `is-paying` pulse while a winning line is on screen, so the reels that
actually paid are unmissable on a busy board.

## Generating the artwork with AI

The game ships with hand-authored SVG symbols in `frontend/symbols.js` and no external
asset dependency. To replace them with AI-generated art:

```bash
VENICE_API_KEY=<key> node tools/generate_assets.mjs
node tools/generate_assets.mjs --dry-run     # preview prompts, no key needed
```

That writes `frontend/assets/manifest.json`, which the game fetches on load and prefers
over the drawn art — so shipping a generated set is regenerate-and-reload, not a code
change. Delete the manifest to fall straight back to SVG.

**Venice, not OpenAI.** `generate_image` needs an `OPENAI_API_KEY`; Venice's API is
reachable with a key you can get at <https://venice.ai/settings/api>. It is OpenAI-compatible
for chat but *not* for images: the endpoint is `POST /api/v1/image/generate` with its own
request shape, returning base64 in `images[]`.

Two constraints worth knowing before you pick a model:

* **Sizing differs by family, and mixing the fields is a hard 400.** Pixel models
  (`venice-sd35`) take `width`/`height` up to 1280. Aspect models (`qwen-image-*`)
  **reject** those fields and want `aspect_ratio`. Resolution models (`gpt-image-2-*`,
  `nano-banana-*`) take `aspect_ratio` plus `resolution` (`1K`/`2K`/`4K`). The script
  picks a scheme from the model name and retries with the other on a 400, so a new model
  does not need a code change.
* **There is no transparency parameter.** The generator renders each symbol on a flat matte
  ground and the frontend feathers that away with a radial CSS mask, so the square boundary
  never shows on the reel.

A key attached to a paying Venice account sees ~44 image models. The default is
`gpt-image-2-5-sunburst` (best quality, roughly 30 s per symbol, so about four minutes for
the set); `gpt-image-2-5-flare` is faster and `venice-sd35` is cheapest. List what your own
key can reach with:

```bash
curl -s 'https://api.venice.ai/api/v1/models?type=image' -H "Authorization: Bearer $VENICE_API_KEY"
```

**On Windows, `setx` only reaches processes started afterwards.** If you export the key
and then run the generator from a shell that was already open, it will not see it. The
one-liner above reads the key from the registry and runs node in a child process that does:

```powershell
$env:VENICE_API_KEY = [Environment]::GetEnvironmentVariable('VENICE_API_KEY','User')
node tools/generate_assets.mjs
```

## Running the frontend

```bash
python -m http.server 8080 --directory frontend
```

Then open <http://localhost:8080>. `?rig=bonus` forces the next spin to open the BALLGAME,
for testing the feature without waiting out a 1-in-176 event.

## Disclaimer

This is a gambling product. It has not been audited, certified, or submitted to any
regulator or platform. Passing the tests in this repo is not a regulatory math review.
