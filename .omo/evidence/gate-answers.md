# Gate answers — pre-market-claims-hardening

Recorded by the lead. The plan's Wave 0 gates read this file.

---

## G1-market: casino

**Answer: casino** (Stake Engine slot — a real-money casino game).

Stated directly by the user: "This is for a game to be put on stake."

**Consequences:**
- The skill-game framing (OQ2 option b) is OUT. It is not being built for a regulated
  skill-game market.
- The B2B math-engine framing (OQ2 option c) is OUT as the product; the closed-form RTP
  core remains an internal asset, not a deliverable.
- Todo 13 (first-class persistent skill SCORE / D7) is **SKIPPED** — it was gated on
  `G1=skill-game`. Per the plan, record `SKIPPED: G1-market=casino` in
  `.omo/evidence/task-13.txt`. This is a justified skip, not a failure.
- HC2 still binds regardless: skill must not touch the payout.
- Because this is a casino game, the compliance surface is genuinely in scope:
  licensing, audit, provenance, and literally-true published numbers are now
  requirements rather than nice-to-haves. That makes RK3 (stale hit rate) and HC6
  (claims must be true or relabelled) higher severity than they would be otherwise.

**Answered:** 2026-10-07

---

## G2-branch: no

**Answer: NO — a Stake Engine book cannot branch on a mid-round player decision.**

This was settled from the platform's own documentation rather than left as a task for the
user. Evidence:

- The official Game Format doc states games are "entirely of **static, pre-computed files**.
  There is no server-side game logic executed at play time." The RGS returns a
  simulation's pre-computed `payoutMultiplier` and its pre-computed `events` array.
- The Bet Modes doc describes `is_feature=True` as running "**without** requiring player
  interaction between rounds."
- The researcher member grepped `events.md`, `simulation-lifecycle.md` and `gamestate.md`
  for `interact|branch|choice|mid-round|gamble|double or nothing` and found **zero
  matches**. There is no documented event type for a client decision, and no documented
  settlement path for one.

Absence of a documented mechanism plus an explicit "static, pre-computed" statement is
enough to act on: THE BYPASS cannot be settled as designed.

**Consequences:**
- Todo 11 (wager fate): **the branch is "no" → DELETE the wager.**
  Remove the bypass logic from `spinner.py`, its events from `events.py`, the wager UI
  from `frontend/game.js`, and the EV-neutrality claims from all four doc sites.
- The pre-bonus two-branch precomputed replacement (D3, creative's proposal) is ALSO out:
  a "choice" between two precomputed branches would still require the client to tell the
  server which branch was taken, and there is no event type or settlement path for that.
  A precomputed branch can only be a presentation of a decision the book already made —
  which is theatre, and dishonest to label as a choice.
- THE BYPASS therefore reduces to: the hack minigame ALONE, as an entry ritual, with no
  wager. Its in-game text must not claim the player can change the outcome.

**Answered:** 2026-10-07

---

## G3-wager: delete-rename | delete-accept  (SUFFIX STILL OPEN)

**Answer: DELETE is settled. The suffix — rename vs accept — is NOT.**

The wager is deleted per G2. That leaves a naming problem the whole team flagged:

> Without the wager the product is "a provably-fair 97% slot with an entry ritual" —
> honest and shippable, but with the "NOTHING" half of its own name dead. Deleting the
> wager without renaming or replacing leaves a title that lies, which every member agreed
> is worse than the current broken wager.

**STILL NEEDS THE USER.** Two options:

- `delete-rename` — change the game's name to something the product actually delivers
  (e.g. VAULT BREAKER / BALL GAME), updating all four doc sites plus package and config
  names.
- `delete-accept` — keep BALL OR NOTHING and accept that the name is a joke about the
  base game's binary feel rather than a description of a wager.

Record the choice as `G3-wager: delete-rename` or `G3-wager: delete-accept`.

---

## G3-demo: (STILL OPEN)

**Answer: NOT YET GIVEN.**

Question: is the demo a **marketing artifact** (goes in front of players) or an
**internal QA tool** (never ships)?

This gates todo 12 (split the demo into simulator + event player). The debate split on it:
the validator argued a public play-money demo is a second product with its own hosting and
advertising exposure that validates nothing about the money path, so it is not the cheap
evidence step it appears to be. The plan's own TL;DR lists it as G3.

Record the choice as `G3-demo: marketing` or `G3-demo: qa-only`.

---

## Summary for the executor

| Gate | Status | Effect |
| --- | --- | --- |
| G1-market | **casino** | Todo 13 SKIPPED. Compliance surface in scope. |
| G2-branch | **no** | Todo 11 = DELETE the wager. No replacement branch. |
| G3-wager | **delete**, suffix OPEN | Needs user: rename or accept the name. |
| G3-demo | **OPEN** | Needs user: marketing or QA-only. Blocks todo 12. |

Waves 1 and 2 (the claims-must-be-true work: cap, hit rate, win display, parity
hard-fail, single event source) are **not gated by anything above** and can start
immediately.
