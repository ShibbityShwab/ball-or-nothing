> Ask: turn the battle-tested insight bundle into an executable work plan, returned verbatim for the lead to present. Wanted: a decision-complete plan that respects all 6 hard constraints, weaves all 10 risk mitigations into tasks, surfaces all 4 open questions as user-input gates, and sequences by dependency. For you: the plan is written at `.omo/plans/pre-market-claims-hardening.md` (14 implementation todos + 4 final verifiers, 3 gates + 3 waves), the ledger is in `.omo/drafts/pre-market-claims-hardening.md`, and every structural check passed (all task rows column-zero and grammar-valid, all category lines present, all GAP refs defined, all IS rows proven). One honest caveat: the high-accuracy plan-reviewer round could not run — the plan gate is locked because this session was not a user-invoked ulw-plan workflow — so a notepad self-review was performed and recorded instead; a follow-up user-invoked ulw-plan session can run the plan-reviewer round on this same plan file if more rigor is wanted. No clarifying questions were needed: all four open questions are embedded as user-input gates (todos 1-3) with verbatim wording. Now: no task remains. Next: no task remains — the plan follows verbatim for presentation.

---

# pre-market-claims-hardening - Work Plan

## TL;DR (For humans)

**Who this is for and what changes for them:** The people who will see this product before market: a player trying the demo, a casino operator or partner reading the RTP / hit-rate / max-win claims, a platform integrator running the SDK adapter, and the developer who has to re-prove the math later. After this plan, every number any of them sees is literally true and derivable from the shipped code, and the one strategic question (what market is this for?) is answered before scope-dependent work starts.

**What you'll get:** Three short yes/no/choose questions answered up front (market, wager platform capability, demo role), then the demo cap fixed so it can never show 1.1 million x against an advertised 25,000x, the stale hit rate replaced with the code-true number everywhere, the free-spin win display fixed to one consistent number, parity tests that fail loudly instead of skipping, Python made the single source of the event data, the SDK adapter made honest and fed with code-derived quotas and pre-computed books, the wager made delete-or-replace per the platform answer, the demo split into an honest simulator plus an event player, a first-class persistent skill score (only if the skill-game market is chosen), and a reproducible RTP PAR sheet artifact so the exact 0.969999 RTP is provable from a clean checkout.

**Why this approach:** The bundle's proven insight is that every bug here hides behind "the demo works" and behind claims that are only true conditionally. So the plan fixes by ownership, not by patching: one cap constant on one path, one source of event data (Python), one money-path definition, one hard gate. Every remaining open question is surfaced as an explicit question before the task that depends on it, so no scope is built on a guess.

**What it will NOT do:** It will not rewrite the product, add symbols, paylines, or mechanics, or touch the payout math that makes the RTP exactly derivable (the closed-form 0.969999 stays closed-form). It will not make any git commit — the repo lives inside a shared parent folder with zero commits, so provenance work stops at a prepared commit plan until you say where to commit. It will not claim the SDK adapter runs until the SDK repo is reachable.

**Effort:** Large
**Risk:** Medium - two irreversible-looking choices (wager fate, market) are gated on user answers, but the SDK adapter stays unverifiable until the private SDK repo is reachable, and no commit can be made without direction.
**Decisions to sanity-check:** G1 - which market (the default recommendation is the honest provably-fair 97% slot; alternatives are a regulated skill-game or a B2B math engine). G2 - whether the Stake platform supports mid-round branching in a static book, which decides wager replace-vs-delete. G3 - whether the demo is a marketing artifact or an internal QA tool.

Your next move: answer the three gate questions (they appear as the first tasks and are repeated in the executor's instructions), then run `/ulw-execute pre-market-claims-hardening`. Full execution detail follows below.

---

> TL;DR (machine): Large, Medium, 14 implementation todos + 4 final verifiers in 3 gates + 3 waves; claims-made-true + one strategic gate.

## Scope
### Affected user and ideal state

**Affected user:** Four groups, in order of how directly they touch the product: (1) the demo player - someone spinning the frontend demo and reading the advertised numbers; (2) the casino operator / partner consuming the math claims (RTP, hit rate, max win) before market entry; (3) the Stake platform integrator running the SDK adapter; (4) the developer (or future auditor) who must re-prove the math from code. Today every group can be shown a number the code contradicts; after this plan, every claim they consume is code-true and every check that proves it fails loudly instead of silently passing.

| Row | Statement | Reason |
| --- | --- | --- |
| IS-1 | Every number the demo player sees matches the code: advertised max win, hit rate, and per-spin winnings shown to the user | the demo is the product's face; a demo spin showing 1,143,660x against an advertised 25,000x is a compliance defect (HC6) |
| GAP-1 | The demo's real ceiling is 1,143,660x (2,723x x 210 x wager double) because the core caps post-double, the frontend never caps, and the PAR sheet caps a formula - three cap semantics, no single owner | closed by todo 4 |
| IS-2 | The operator receives an RTP, hit rate, and max win that are literally true and derivable from the shipped code | HC6: claims must be literally true or relabelled |
| GAP-2 | Advertised hit rate 22.6% / "1 in 4.4" is stale; code says 0.189895 / ~1 in 5.27, and four documents assert the stale number | closed by todo 5 |
| GAP-10 | The wager is EV-negative above 12,500x, so "EV-neutral by construction" is false there - four documents assert an invariant the code violates | closed by todo 11 |
| IS-3 | A player's free-spin win events carry one consistent money number: the credited total equals the animated total, with winWithoutMult meaning what its name says | the RGS credits one number while the UI animates another today (RK4) |
| GAP-3 | Free-spin winInfo emits per-line wins unmultiplied and winWithoutMult inverted | closed by todo 6 |
| IS-4 | The integrator gets an adapter that calls the Python core (one board generator, one money path) and consumes quotas/books derived from the closed form | HC3: one fact, one owner; HC4: anything assuming the SDK runs is labelled unverifiable |
| GAP-6 | The adapter ships a false "overrides draw_board" docstring and a dead game_override.py | closed by todo 8 |
| GAP-7 | Adapter quotas are invented (win 0.31 vs machine 0.189983) and contradict the machine | closed by todo 9 |
| IS-5 | The developer's parity suite hard-fails when a JS runtime is missing, and Python is the single source of the event JSON the JS mirror is certified against | a skipped parity test certifies nothing (RK9); two hand-written mirrors certifying each other can share the same bug (D2) |
| GAP-4 | JS and Python event streams have diverged: different winInfo keys, different wins entry shape, different reveal cells, missing bypass events | closed by todo 10 |
| GAP-5 | tests/test_js_parity.py:43 silently skips without bun/node | closed by todo 7 |
| IS-6 | The demo the consumer plays is an honest event player: it renders the event stream produced by the money path, and never computes its own money | D1: conflating the demo with the money path let every event-stream bug hide behind "the demo works" |
| GAP-9 | The demo's money path is defined by an inline Math.random in the frontend, not by the engine | closed by todo 12 |
| IS-7 | When the chosen market is a skill-game, the skill layer is a real first-class score: accuracy, elapsed time, and personal best persist across sessions - and it never touches payout | D7 + HC2: the "skill layer" claim must be true if made, and skill must never move the money |
| GAP-11 | The skill hack measures accuracy/time and shows CLEAN/MESSY but is not first-class or persistent | closed by todo 13 (only when G1=skill-game) |
| IS-8 | A developer or auditor can reproduce the exact RTP from a clean checkout via a committed PAR-sheet script, tagged to the code state that produced it | RK10: zero commits, no reproducible RTP artifact exists today |
| GAP-8 | No provenance, no reproducible RTP artifact, git root is a shared parent with unborn HEAD (HC5) | closed by todo 14 |

### Must have
- The three user-input gates answered and recorded before any gated task runs (HC rule: every Open Question surfaces as an explicit gate).
- Todos 4-10, 14 (the claims-true work, RK2-RK9 + RK10) with passing agent-executed QA - this is the lead's stated highest-value scope.
- Todos 11-13 executed per the recorded gate answers, or recorded as skipped with the gate reason.
- The final verification wave F1-F4, all APPROVE.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- NO product rewrite, no new symbols, paylines, or mechanics (lead scope note: do not turn this into a rewrite).
- NO payout change that breaks the closed-form RTP derivability (HC1): the base + line + binomial-multiplier decomposition must stay exactly derivable.
- NO skill-to-payout coupling (HC2).
- NO git commit, init, or tag to the shared parent Documents/GitHub without explicit user direction (HC5); provenance todo stops at a prepared commit plan + artifact.
- NO claim that the SDK adapter runs until the SDK repo is reachable (HC4).
- NO relabelling instead of fixing where a fix is possible (HC6).
- NO parity test that can skip silently (RK9 mitigation).

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after (TDD-style: write the failing case first where cheap, then the fix) + framework: pytest for Python (existing 92-test suite), bun/node subprocess for the JS mirror via tests/test_js_parity.py, bun for frontend behavior checks.
- Evidence: every todo writes its happy + failure QA output to .omo/evidence/task-<N>.txt (outside ulw-loop, per template). Gate answers are recorded once in .omo/evidence/gate-answers.md and referenced by the gated todos.
- Full suite gate per task: `python -m pytest tests/ -q` (bun is present on this machine, so the parity suite must actually run - a skip is a FAIL after todo 7).
- HC4 label discipline: any QA that would require the private SDK is replaced by import-and-call structure checks and is labelled UNVERIFIABLE in the evidence file; it never blocks a todo.

## Execution strategy
### Parallel execution waves

Wave 0 - gates: todos 1-3. These are the three user-input gates (G1 market, G2 wager platform, G3 demo role). They must be answered before the todos they gate; they can be answered in any order and recorded in .omo/evidence/gate-answers.md.

Wave 1 - claims-true, independent (run in parallel, 6 todos): todos 4 (cap semantics), 5 (hit-rate docs), 6 (winInfo), 7 (parity hard-fail), 8 (adapter call-core), 14 (provenance PAR sheet). None of these depends on a gate; each touches disjoint files except todos 4 and 5, which both touch advertised numbers - todo 4 owns max-win doc numbers, todo 5 owns hit-rate doc numbers, and they must not edit each other's numbers (noted in each todo).

Wave 2 - source-of-truth + books (parallel): todos 9 (quotas + precomputed books, blocked by 8 because both touch the adapter), 10 (Python event source, blocked by 7 because both touch js_parity/tests/test_js_parity.py).

Wave 3 - gated decisions: todos 11 (wager fate, gated by G2; blocked by 4, 6, 10 - it edits spinner, events, docs, frontend), 12 (demo split, gated by G3; blocked by 4 and 10), 13 (skill score, gated by G1; blocked by 12 - both touch the frontend).

Final verification wave: F1-F4, run in parallel after ALL todos, ALL must APPROVE, then wait for the user's explicit okay before declaring complete.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 (G1 market) | nothing | 13 (skill score) | 2, 3, and all of Wave 1 |
| 2 (G2 wager platform) | nothing | 11 (wager fate) | 1, 3, and all of Wave 1 |
| 3 (G3 demo role) | nothing | 12 (demo split) | 1, 2, and all of Wave 1 |
| 4 cap semantics | nothing | 11, 12 | 5, 6, 7, 8, 14 |
| 5 hit-rate docs | nothing | nothing | 4, 6, 7, 8, 14 |
| 6 winInfo fix | nothing | 11 | 4, 5, 7, 8, 14 |
| 7 parity hard-fail | nothing | 10 | 4, 5, 6, 8, 14 |
| 8 adapter call-core | nothing | 9 | 4, 5, 6, 7, 14 |
| 9 quotas + books | 8 | nothing | 10, 14 |
| 10 Python event source | 7 | 11, 12 | 9, 14 |
| 11 wager fate | 2, 4, 6, 10 | nothing | 13 |
| 12 demo split | 3, 4, 10 | 13 | 11 |
| 13 skill score | 1, 12 | nothing | 11 |
| 14 provenance PAR sheet | nothing | nothing | 4, 5, 6, 7, 8, then 9, 10 |
| F1-F4 | all todos | nothing | each other |

## Todos
> Implementation + Test = ONE todo. Never separate.
> GATE MECHANISM: todos 1-3 are USER-INPUT GATES. The executor asks the user the exact question listed, records the answer in .omo/evidence/gate-answers.md, and routes gated todos by it. A gated todo whose gate answer makes it moot is recorded as SKIPPED with the gate reason, and the final wave treats a justified skip as complete - a silent skip is a FAIL.

- [ ] 1. G1: Ask the user which market this product is for (OQ2 - gates scope)
  What to do / Must NOT do: Ask verbatim: "What market is this for? (a) casino game - licensing, audit, provenance required; (b) skill-game - different regulation, and skill must never touch payout; (c) B2B math/engine for other studios - the closed-form RTP + parity harness are the asset. My recommendation: (a) the honest provably-fair 97% slot, because it is shippable today and the compliance fixes in this plan are exactly what it needs." Record the answer. MUST NOT choose for the user; MUST NOT start todo 13 unless the answer is (b) skill-game. If the answer changes scope beyond this plan's tasks, STOP and report back instead of expanding.
  Closes: GAP-11
  Parallelization: Wave 0 | Blocked by: nothing | Blocks: 13
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md (OQ2, lead note on scope); the three framings are the only surviving ones from the adversarial debate - do not invent new market options.
  Acceptance criteria (agent-executable): .omo/evidence/gate-answers.md exists and contains `G1-market: ` followed by one of casino / skill-game / b2b-engine, plus the date.
  QA scenarios (name the exact tool + invocation): happy - user answers (a); Evidence .omo/evidence/gate-answers.md. failure - user answers with a fourth option: record it verbatim and STOP, reporting the scope delta to the user before running any gated todo. Evidence .omo/evidence/task-1.txt
  Commit: N (HC5 - no commits anywhere in this plan until the user directs where)
  Recommended task executor category: quick - it is a scripted question with a recorded answer, no reasoning.

- [ ] 2. G2: Ask the user whether the Stake book can branch on a mid-round player decision (OQ1) and derive the wager fate (OQ3)
  What to do / Must NOT do: Ask verbatim: "Can a Stake Engine book branch on a mid-round player decision? The platform docs say games are entirely static pre-computed files with no server-side game logic at play time. This is a one-question platform gate: if NO, the wager must be deleted and we then either rename the game or accept that the name promises what the game does not do - which do you prefer (rename / accept)? If YES, we replace the wager with a precomputed two-branch decision (guaranteed 1x vs a precomputed 0-3x branch) inside the static book with a real, disclosed EV." Record BOTH answers: `G2-branch: yes|no` and `G3-wager: delete-rename | delete-accept | replace`. MUST NOT decide for the user; MUST NOT implement anything in this todo.
  Closes: GAP-10
  Parallelization: Wave 0 | Blocked by: nothing | Blocks: 11
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md (OQ1, OQ3, D3); RK1 for why delete-or-replace, not repair; RK8 for the BypassResult contradiction that any wager change must also fix.
  Acceptance criteria (agent-executable): .omo/evidence/gate-answers.md contains `G2-branch:` with yes|no AND `G3-wager:` with one of delete-rename | delete-accept | replace.
  QA scenarios (name the exact tool + invocation): happy - user answers no + delete-rename; Evidence .omo/evidence/gate-answers.md. failure - user answers yes but refuses the replacement EV disclosure: record it, STOP, and report that a hidden-EV replacement violates HC6. Evidence .omo/evidence/task-2.txt
  Commit: N
  Recommended task executor category: quick - scripted two-part question, recorded answer.

- [ ] 3. G3: Ask the user what the demo is for (OQ4)
  What to do / Must NOT do: Ask verbatim: "Is the demo a marketing artifact or an internal QA tool? If marketing, it must be an event player that renders the engine's events and never computes money itself. If internal QA, the simulator part is what matters and the pretty wrapper is optional. My recommendation: treat it as both in one split - the simulator for math QA, the event-player shim for anything a user sees." Record `G4-demo: marketing | qa-tool | both`.
  Closes: GAP-9
  Parallelization: Wave 0 | Blocked by: nothing | Blocks: 12
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md (OQ4, D1 - the split, not a relabel).
  Acceptance criteria (agent-executable): .omo/evidence/gate-answers.md contains `G4-demo:` with one of marketing | qa-tool | both.
  QA scenarios (name the exact tool + invocation): happy - user answers both; Evidence .omo/evidence/gate-answers.md. failure - user answers neither and asks to ship game.js as-is: record and STOP, reporting that it contradicts D1 and RK2/RK4/RK5. Evidence .omo/evidence/task-3.txt
  Commit: N
  Recommended task executor category: quick - scripted question, recorded answer.

- [ ] 4. One cap constant on one path; demo cannot exceed the advertised 25,000x
  What to do / Must NOT do: Unify the three cap semantics into ONE cap constant owned by Python config and mirrored verbatim in frontend/engine.js: core caps post-double (src/ball_or_nothing/spinner.py:291), frontend never caps (frontend/game.js:411 returns round.bonus.total uncapped, game.js:472 doubles with no clamp), PAR sheet caps a formula (src/ball_or_nothing/par.py:188). The cap is WINCAP = 25,000x; apply it so the demo's displayed total can never exceed it. Update the max-win statements in README.md, frontend/index.html, games/masterbetty_ball_or_nothing/readme.txt to say exactly what the code enforces. MUST NOT change payout below the cap; MUST NOT change the RTP derivation (HC1); MUST NOT touch the hit-rate numbers (todo 5 owns those); MUST NOT invent a second cap source (HC3).
  Closes: GAP-1
  Parallelization: Wave 1 | Blocked by: nothing | Blocks: 11, 12
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md RK2 (lead-verified: per-spin max 2,723x, sum of multipliers 1..20 = 210, wager double = 1,143,660x ceiling); src/ball_or_nothing/spinner.py:291; frontend/game.js:411, 472; src/ball_or_nothing/par.py:188; frontend/engine.js constants block; tests/test_math.py.
  Acceptance criteria (agent-executable): `python -m pytest tests/ -q` green; a new test (tests/test_math.py) asserts the capped spin/bonus math never exceeds WINCAP including the post-double path; a JS-side check (bun) asserts the demo's total-win display path clamps to WINCAP for a synthetic max bonus; grep shows exactly ONE cap definition source (`WINCAP`) mirrored to engine.js.
  QA scenarios (name the exact tool + invocation): happy - `python -m pytest tests/test_math.py -q -k cap`; Evidence .omo/evidence/task-4.txt. failure - temporarily raise the frontend cap and confirm the demo test fails; Evidence .omo/evidence/task-4.txt
  Commit: N
  Recommended task executor category: deep-low - cross-module money-path reasoning (spinner, par, frontend) but every step is evidence-settled from the cited lines.

- [ ] 5. Regenerate advertised hit rate from the code and add a doc-consistency test
  What to do / Must NOT do: The advertised 22.6% / "1 in 4.4" is stale (README.md:41, frontend/index.html:117, games/masterbetty_ball_or_nothing/readme.txt:32,59). Compute the code-true numbers from src/ball_or_nothing/par.py (hit_rate() = 0.189895, ~1 in 5.27 - recompute, do not trust this plan's arithmetic) and replace the doc values. Add a test (tests/test_math.py) that reads the shipped doc files, extracts the advertised hit-rate strings, and FAILS when they disagree with the computed value. MUST NOT edit max-win numbers (todo 4 owns them); MUST NOT change the weights or the math to match the docs - docs follow code, never the reverse (HC6).
  Closes: GAP-2
  Parallelization: Wave 1 | Blocked by: nothing | Blocks: nothing
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md RK3; README.md:41; frontend/index.html:117; games/masterbetty_ball_or_nothing/readme.txt:32,59; src/ball_or_nothing/par.py hit_rate(); tests/test_math.py for test style.
  Acceptance criteria (agent-executable): `python -m pytest tests/ -q` green; the new doc-consistency test passes with the updated docs; `python -c "from ball_or_nothing.par import hit_rate; print(hit_rate())"` matches the advertised rounded number.
  QA scenarios (name the exact tool + invocation): happy - `python -m pytest tests/test_math.py -q -k doc`; Evidence .omo/evidence/task-5.txt. failure - put 22.6% back in one doc and confirm the test fails; Evidence .omo/evidence/task-5.txt
  Commit: N
  Recommended task executor category: unspecified-low - doc edits + one straightforward test.

- [ ] 6. Fix free-spin winInfo: one money number, correct winWithoutMult
  What to do / Must NOT do: In src/ball_or_nothing/events.py, FreeSpin.wins holds raw unmultiplied payouts while FreeSpin.payout is multiplied; win_payload emits "win": raw and "winWithoutMult": raw/multiplier - i.e. dividing an already-raw value. Derive each emitted value once at emission from the multiplied payout; drop the redundant per-line "win" field if the schema allows, and make winWithoutMult the pre-multiplier total (its literal name). Update frontend/engine.js and frontend/game.js to consume the corrected keys, and update tests/test_events.py expectations. MUST NOT change payout amounts themselves (HC1); MUST NOT widen the parity test to hide the difference - the test must assert the specific corrected shape (D2).
  Closes: GAP-3
  Parallelization: Wave 1 | Blocked by: nothing | Blocks: 11
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md RK4 (lead-verified: spin.payout 1.4 at multiplier 7 vs sum(wins) = 0.2); src/ball_or_nothing/events.py FreeSpin + win_payload; frontend/engine.js winInfo; tests/test_events.py.
  Acceptance criteria (agent-executable): `python -m pytest tests/ -q` green; a test constructs a free-spin round at a known multiplier and asserts sum(emitted wins) equals the credited payout AND winWithoutMult equals the pre-multiplier total; the JS mirror's winInfo for the same seeded round matches key-for-key.
  QA scenarios (name the exact tool + invocation): happy - `python -m pytest tests/test_events.py -q`; Evidence .omo/evidence/task-6.txt. failure - revert the multiplication in the emitter and confirm the test fails; Evidence .omo/evidence/task-6.txt
  Commit: N
  Recommended task executor category: unspecified-low - one emitter + mirror edit, test-verifiable.

- [ ] 7. Parity must hard-fail, never skip
  What to do / Must NOT do: tests/test_js_parity.py:43 pytest.skip when bun/node is absent. Replace with pytest.fail with a message naming the missing runtime; update the module docstring so it no longer describes skipping as acceptable. bun IS present on this machine, so the suite must actually run here. MUST NOT weaken the runtime detection; MUST NOT make CI skip on failure.
  Closes: GAP-5
  Parallelization: Wave 1 | Blocked by: nothing | Blocks: 10
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md RK9; tests/test_js_parity.py:43 and _runtime(); tools/js_parity.mjs.
  Acceptance criteria (agent-executable): grep finds no pytest.skip in tests/test_js_parity.py; `python -m pytest tests/test_js_parity.py -q` passes on this machine (bun present, parity actually executed); a PATH-restricted run (hide bun/node from PATH) fails instead of skipping.
  QA scenarios (name the exact tool + invocation): happy - `python -m pytest tests/test_js_parity.py -q`; Evidence .omo/evidence/task-7.txt. failure - run with a PATH that excludes bun and node, confirm pytest reports FAILED not SKIPPED; Evidence .omo/evidence/task-7.txt
  Commit: N
  Recommended task executor category: quick - one-line skip->fail swap plus docstring, fully mechanical.

- [ ] 8. Adapter calls the core; delete the false override claim
  What to do / Must NOT do: Delete the false docstring at src/ball_or_nothing/config.py:9 ("the SDK adapter overrides draw_board to match") and delete games/masterbetty_ball_or_nothing/game_override.py (a bare pass). Make the adapter's game code call core draw_board/evaluate_board directly (D4) so the adapter is a caller, not a mirror. The adapter has NEVER RUN (SDK private - HC4): every check here is import-and-call structure, labelled UNVERIFIABLE for real SDK execution. MUST NOT delete the adapter itself (D6 freeze-until-runnable); MUST NOT reimplement board logic in the adapter (HC3).
  Closes: GAP-6
  Parallelization: Wave 1 | Blocked by: nothing | Blocks: 9
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md RK7, D4, D6; src/ball_or_nothing/config.py:9; games/masterbetty_ball_or_nothing/game_override.py; games/masterbetty_ball_or_nothing/gamestate.py; games/masterbetty_ball_or_nothing/game_events.py; games/masterbetty_ball_or_nothing/game_calculations.py.
  Acceptance criteria (agent-executable): grep under games/ finds no draw_board definition and no reference to game_override; `python -c "import games.masterbetty_ball_or_nothing.gamestate"` (or the package's import path per pyproject) succeeds; the gamestate call path resolves to ball_or_nothing.core functions (inspect the import/call in code).
  QA scenarios (name the exact tool + invocation): happy - `python -m pytest tests/ -q` plus the import check; Evidence .omo/evidence/task-8.txt, labelled UNVERIFIABLE-against-SDK per HC4. failure - re-add the docstring and confirm the grep check fails; Evidence .omo/evidence/task-8.txt
  Commit: N
  Recommended task executor category: unspecified-low - small mechanical adapter edits with structure verification.

- [ ] 9. Adapter quotas from the closed form + precomputed books in Python
  What to do / Must NOT do: The declared quotas contradict the machine (win 0.31 vs 0.189983, bonus 0.0045 vs 0.005630, zero 0.6853 vs 0.804387) and run_spin loops on an unchanging sim without reading the Distribution conditions (games/masterbetty_ball_or_nothing/gamestate.py:50-54). Per D5: add a Python precompute tool that generates static books with the seeded core (deterministic) and have the adapter consume them; derive any quota values FROM the closed form (par.py) or drop them in favor of the precomputed books. MUST NOT ask the SDK's reject-and-resample loop to produce randomness (D5); MUST NOT claim the SDK accepts the books until run against it (HC4 - label UNVERIFIABLE); MUST NOT delete the adapter (D6).
  Closes: GAP-7
  Parallelization: Wave 2 | Blocked by: 8 | Blocks: nothing
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md RK6, D5; games/masterbetty_ball_or_nothing/gamestate.py:50-54; games/masterbetty_ball_or_nothing/game_config.py; src/ball_or_nothing/par.py; tools/ for precompute-tool placement convention.
  Acceptance criteria (agent-executable): the precompute tool runs deterministically (same output bytes on two runs); the book JSON contains a stated EV/RTP that matches the closed form 0.969999 within 1e-6; grep shows quota constants either removed or equal to closed-form-derived values.
  QA scenarios (name the exact tool + invocation): happy - run precompute twice, `cmp` the outputs; Evidence .omo/evidence/task-9.txt, labelled UNVERIFIABLE-against-SDK per HC4. failure - hand-edit one quota back to 0.31 and confirm the consistency check fails; Evidence .omo/evidence/task-9.txt
  Commit: N
  Recommended task executor category: unspecified-low - mechanical derivation + one new deterministic tool.

- [ ] 10. Python is the single source of the event JSON
  What to do / Must NOT do: RK5 (lead-verified divergence): JS winInfo keys {type,totalWin,multiplier,wins,index} vs Python {index,type,totalWin,wins}; JS wins[0] {lineIndex,symbol,kind,payout} vs Python {symbol,kind,win,positions,meta}; JS reveal cells raw strings vs Python [{"name":"VAULT"}]; JS emits no bypass events. Per D2: make Python the single source of the event JSON. Add/point a Python CLI (src/ball_or_nothing/cli.py or a tools/ script) that emits the full event stream for a seeded spin (base + free spins + bonus) as JSON; certify the JS engine at line-eval + constants (the existing js_parity.mjs contract) AND construct an event-stream parity check that compares the JS mirror's event output against the Python-emitted stream for the same seeds, field by field. MUST NOT widen parity into "two mirrors agree" without the Python-emitted golden stream (D2); MUST NOT change event semantics while fixing keys - only the shape (any semantic bug belongs to todo 6).
  Closes: GAP-4
  Parallelization: Wave 2 | Blocked by: 7 | Blocks: 11, 12
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md RK5, D2; frontend/engine.js winInfo/reveal/bypass; src/ball_or_nothing/events.py; tools/js_parity.mjs; tests/test_js_parity.py.
  Acceptance criteria (agent-executable): `python -m pytest tests/ -q` green; the event-stream parity test constructs an event stream and compares it against the Python-emitted JSON (not a hand-written expectation); a seeded Python emission and the JS mirror emission for the same seed differ in ZERO fields.
  QA scenarios (name the exact tool + invocation): happy - run the Python emitter for a fixed seed, run the JS parity tool, diff is empty; Evidence .omo/evidence/task-10.txt. failure - rename one JS winInfo key and confirm the parity test fails; Evidence .omo/evidence/task-10.txt
  Commit: N
  Recommended task executor category: deep-low - cross-language event-contract work; the contract itself is settled by the bundle, the executor settles the field-by-field mapping from the code.

- [ ] 11. Wager fate: delete or replace, per G2; fix BypassResult; make every EV claim true
  What to do / Must NOT do: Read G2-branch and G3-wager from .omo/evidence/gate-answers.md. If branch=no: delete the wager (spinner.py bypass logic, events, frontend wager UI), and per G3-wager either rename the game (all four doc sites + package names that advertise the wager) or record the accepted-name decision in the docs as a disclosed promise gap. If branch=yes: replace the wager with D3's precomputed two-branch decision inside a static book - guaranteed 1x vs a precomputed 0-3x branch, EV disclosed - implemented as precomputed data, never as a live player-decision at play time. Either way fix RK8: BypassResult.taken hardcoded True ("the player walked away") and target always 0 and never emitted (src/ball_or_nothing/spinner.py:244) - model the two-branch decision in the schema or excise the wager entirely. MUST NOT repair the EV-negative wager in place (RK1/D3 - delete-or-replace); MUST NOT let player behavior affect payout (HC1); MUST NOT leave any doc claiming EV-neutral where the code is not (HC6).
  Closes: GAP-10
  Parallelization: Wave 3 | Blocked by: 2, 4, 6, 10 | Blocks: nothing
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md RK1 (EV-negative above 12,500x - verified), RK8, D3, OQ1/OQ3; src/ball_or_nothing/spinner.py wager/bypass + :244; src/ball_or_nothing/events.py; frontend/game.js wager UI; README.md / frontend/index.html / games/masterbetty_ball_or_nothing/readme.txt; the four doc sites asserting the invariant.
  Acceptance criteria (agent-executable): `python -m pytest tests/ -q` green; a test proves the wager's EV contribution is exactly 0 (deleted) or equals the disclosed precomputed EV (replaced) for every reachable stake, including stakes above 12,500x; grep finds no doc asserting EV-neutral-by-construction unless the code proves it; the BypassResult contradiction is gone (taken/target removed or schema-true).
  QA scenarios (name the exact tool + invocation): happy - `python -m pytest tests/ -q -k wager` (or new test file); Evidence .omo/evidence/task-11.txt. failure - restore the old EV-negative path and confirm the EV test fails; Evidence .omo/evidence/task-11.txt
  Commit: N
  Recommended task executor category: deep-high - this is the one decision with contract/schema consequences and a user-supplied fork; correctness is argued from the EV invariant, not just observed.

- [ ] 12. Split the demo into simulator + event player (D1), per G3
  What to do / Must NOT do: The demo's money path is the inline Math.random in the frontend (RK8 consequence). Split frontend: (a) a local simulator that exercises engine.js for math QA (paylines, odds); (b) a thin event-player shim - the only production-facing frontend - that renders the Python-emitted event stream (todo 10's JSON) and computes NO money itself. If G4-demo=qa-tool, (b) can stay minimal; if marketing, (b) gets the pretty wrapper and the simulator stays internal. Delete the demo's own money computation (game.js inline Math.random path). MUST NOT keep a money path in the demo (HC3 one money-path owner); MUST NOT test anything against real RGS JSON (none is available - HC4 label); MUST NOT rewrite the whole frontend - the scope is the split, not a redesign (lead scope note).
  Closes: GAP-9
  Parallelization: Wave 3 | Blocked by: 3, 4, 10 | Blocks: 13
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md D1, OQ4; frontend/game.js (money path, wager double), frontend/engine.js (line-eval math), frontend/index.html, frontend/symbols.js, frontend/styles.css; tools/js_parity.mjs; .omo/evidence/gate-answers.md G4-demo.
  Acceptance criteria (agent-executable): the event-player renders a fixed Python-emitted event file with no JS money computation (grep the player file for Math.random / payout arithmetic); the simulator still passes the full parity suite; a bun-based check loads the event-player, feeds it the seeded event JSON, and asserts the displayed total equals the stream's total.
  QA scenarios (name the exact tool + invocation): happy - `python -m pytest tests/ -q` plus the bun event-player replay check; Evidence .omo/evidence/task-12.txt. failure - feed the player an event file with a total altered by 1 and confirm the display check fails; Evidence .omo/evidence/task-12.txt
  Commit: N
  Recommended task executor category: unspecified-high - multi-file frontend restructure (game.js split) with a behavioral replay check.

- [ ] 13. First-class persistent skill SCORE (D7) - only when G1=skill-game
  What to do / Must NOT do: Read G1-market. If not skill-game: do NOT build this; record "SKIPPED: G1-market=<answer>" in .omo/evidence/task-13.txt - that is a justified skip. If skill-game: the hack already measures accuracy and elapsed time and shows a CLEAN/MESSY badge; make SCORE first-class and persistent (personal best via localStorage), surfaced in the UI. MUST NOT let the score touch payout in any way (HC2); MUST NOT change the payout math (HC1 - RTP must stay exactly derivable).
  Closes: GAP-11
  Parallelization: Wave 3 | Blocked by: 1, 12 | Blocks: nothing
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md D7, HC2; frontend/game.js skill/SCORE/CLEAN-MESSY code; frontend/index.html; .omo/evidence/gate-answers.md G1-market.
  Acceptance criteria (agent-executable): if skill-game: personal best persists across reloads (bun localStorage check or a deterministic JS check of the storage calls); `python -m pytest tests/ -q` still green with RTP 0.969999 asserted; grep shows the score code has no reference to payout/wincap. If not skill-game: .omo/evidence/task-13.txt contains the skip reason.
  QA scenarios (name the exact tool + invocation): happy - skill-game path: run the persistence check; Evidence .omo/evidence/task-13.txt. failure - make the score add 1x to the payout and confirm the RTP test fails; Evidence .omo/evidence/task-13.txt
  Commit: N
  Recommended task executor category: unspecified-low - small frontend feature, but conditional on the gate.

- [ ] 14. Reproducible PAR-sheet artifact + commit plan (RK10, HC5-safe)
  What to do / Must NOT do: Add a reproducible PAR-sheet script (tools/ or src/ball_or_nothing/) that emits the exact closed-form RTP (0.969999), hit rate, max win, bonus frequency, and the derivation inputs as a JSON artifact, deterministic across runs; tag it with a content hash so a later auditor can match the artifact to the code state. Record the git state (zero commits, unborn HEAD at the shared parent C:/Users/ShibbityShwab/Documents/GitHub) in the evidence file, and WRITE - do not execute - a commit plan: the exact commands for `git init` in the ball-or-nothing subdirectory, initial commit, and tagging the PAR artifact, to run only after explicit user direction. MUST NOT run git init/commit/tag now (HC5); MUST NOT commit to the parent; MUST NOT add a LICENSE silently (HC5 mentions no LICENSE - flag it in the commit plan as a user decision).
  Closes: GAP-8
  Parallelization: Wave 1 | Blocked by: nothing | Blocks: nothing
  References (executor has NO interview context - be exhaustive): .omo/hyperplan-insight-bundle.md RK10, HC5, lead note on git root; src/ball_or_nothing/par.py (RTP derivation); the .omo/hyperplan-insight-bundle.md RTP figures (0.969999 = base 0.5447 + bonus 0.4253).
  Acceptance criteria (agent-executable): the PAR script runs twice and produces byte-identical JSON; the JSON contains rtp=0.969999 (exact) and the derived hit rate from par.py; .omo/evidence/task-14.txt contains the git-state record and the prepared (unexecuted) commit plan including the LICENSE question.
  QA scenarios (name the exact tool + invocation): happy - run the script twice, `cmp` outputs; Evidence .omo/evidence/task-14.txt. failure - alter one derivation input and confirm the artifact hash changes and RTP no longer matches; Evidence .omo/evidence/task-14.txt
  Commit: N
  Recommended task executor category: unspecified-low - deterministic script + documentation of git state.

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit
  Verify every todo 1-14 either has its acceptance criteria met and evidenced, or is a justified skip (gates 13 only). Check the structural contract: every implementation row matches `- [ ] N. <title>`, every final row matches `- [ ] F<n>. <title>`, all column-zero, every implementation row carries a `Recommended task executor category:` line, no prose bullet is counted as a task. Evidence .omo/evidence/f1.txt
- [ ] F2. Code quality review
  Review each changed file for the project's existing conventions (the repo's Python core style, the JS mirror style, doc tone); run the full suite and any linters the repo configures (pyproject has basedpyright config - run it if installed; else note it); no new warnings introduced in changed files. Evidence .omo/evidence/f2.txt
- [ ] F3. Real manual QA
  Run the real surface: `python -m pytest tests/ -q` (all green, parity actually executed), the Python event emitter for a handful of seeds, the event-player replay for one seeded round, the demo in a browser headlessly (bun WebView or the existing tools) asserting the displayed total never exceeds WINCAP. Evidence .omo/evidence/f3.txt
- [ ] F4. Ideal-state fidelity
  Walk IS-1..IS-8 against the delivered repo one-by-one: for each row, name the delivering todo and the proving QA evidence path from that todo's evidence file; any IS row with no proof becomes new `- [ ] N.` rows (never a note); a G1-based skip of IS-7 counts as satisfied-by-decision only with the gate answer recorded. Evidence .omo/evidence/f4.txt

## Commit strategy
> HC5 governs: the git root is a SHARED PARENT directory (Documents/GitHub) with zero commits. Every todo carries Commit: N.
- No commit, init, or tag is executed anywhere in this plan.
- Todo 14 produces the prepared commit plan (init in the ball-or-nothing subdirectory, initial commit, PAR-sheet tag, LICENSE decision) and the reproducible PAR-sheet artifact; the user's explicit direction turns that plan into the one and only commit point for this work.
- Evidence files live under .omo/evidence/ and are machine-consumed records, not commit payloads.

## Success criteria
> One row per IS row. The plan is complete only when every IS row has a delivering todo and a proving QA scenario; F4 checks the delivered behavior against these rows 1:1, and a shortfall becomes new `- [ ] N.` rows, never a note.
| IS | Delivering todo(s) | Proving QA scenario | Evidence |
| --- | --- | --- | --- |
| IS-1 demo numbers true | 4, 5 | demo cap test (task-4), doc-consistency test (task-5) | .omo/evidence/task-4.txt, task-5.txt |
| IS-2 operator claims true | 4, 5, 11 | cap + doc tests; wager EV test | .omo/evidence/task-4.txt, task-5.txt, task-11.txt |
| IS-3 one money number per win event | 6 | winInfo emission test | .omo/evidence/task-6.txt |
| IS-4 integrator gets a truthful adapter | 8, 9 | import/structure check + book determinism (UNVERIFIABLE-against-SDK per HC4) | .omo/evidence/task-8.txt, task-9.txt |
| IS-5 parity fails loudly, Python owns event JSON | 7, 10 | skip->fail check + event-stream parity diff | .omo/evidence/task-7.txt, task-10.txt |
| IS-6 demo is an honest event player | 12 | event-player replay check | .omo/evidence/task-12.txt |
| IS-7 real skill score (skill-game market only) | 13 | persistence check + RTP still 0.969999, or justified skip | .omo/evidence/task-13.txt |
| IS-8 reproducible RTP artifact | 14 | PAR script byte-identical twice, hash tag | .omo/evidence/task-14.txt |

---

**Artifacts written (planner scope only — no product code touched):**
- `.omo/plans/pre-market-claims-hardening.md` — the plan above (final SHA-256 `189625db5a11486e6eff6ff563e9258b240d030baf14755012645a371fc9b7fb`)
- `.omo/drafts/pre-market-claims-hardening.md` — durable ledger: intent, ideal-state/gap rows, decisions, scope IN/OUT, review state, gate status

**Review status:** `review_required: true` was recorded, but the plan-reviewer spawn was refused by the plan gate (this session was not a user-invoked ulw-plan workflow). Per policy I did not retry or bypass; a notepad self-review was performed instead: header order exact, 14/14 implementation rows and 4/4 final rows column-zero and grammar-valid, every implementation row carries a `Recommended task executor category:` line, every `Closes:` GAP reference has a defined row, every IS row has a proving QA scenario in Success criteria, and HC1-HC6 / RK1-RK10 / OQ1-OQ4 were re-checked one-by-one against the todo list. A follow-up user-invoked ulw-plan session on this plan file can run the high-accuracy plan-reviewer round if the lead wants that rigor before handoff.

[task_id: st_01a11489 - continue with task_send(to="st_01a11489", message="...")]