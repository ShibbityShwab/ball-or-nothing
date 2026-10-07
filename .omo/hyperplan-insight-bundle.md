# Hyperplan Insight Bundle: BALL OR NOTHING — pre-market critical review

## Original User Request
"do a critical review of what we have now and how we can improve it before we enter the market"

## Context: what the product is
A Stake Engine slot game at C:/Users/ShibbityShwab/Documents/GitHub/ball-or-nothing: 5 reels x 3 rows, 10 paylines, 7 symbols (BALL/NUT/SACK/COIN/LOSS/WILD/VAULT). Python math core (src/ball_or_nothing/) with a JS mirror (frontend/engine.js) kept in sync by tools/js_parity.mjs. A Stake Math SDK adapter (games/masterbetty_ball_or_nothing/) that has NEVER RUN because the SDK repo is private. Frontend demo with AI-generated art. 92 tests pass.

Lead-verified facts (I ran these myself, not relayed):
- RTP = 0.969999 exact by closed form; base 0.5447 + bonus 0.4253
- BALLGAME trigger 1 in 176; max multiplier 20; paytable five_ball = 272.3
- 92 tests pass; parity suite 9/9 passed on this machine (bun present, so the skip branch was NOT exercised here)
- No stubs/TODOs in the code
- Repo root is C:/Users/ShibbityShwab/Documents/GitHub with ZERO git commits (unborn HEAD). It is a parent folder containing many unrelated projects, so a commit there sweeps them all.

## Hard Constraints (Survived Adversarial Review)
- HC1. The closed-form RTP must stay exactly derivable. Any change making payout depend on player behaviour destroys the base+line+binomial-multiplier decomposition. (skeptic's attack on creative C2, uncontested)
- HC2. Skill must NOT touch the payout. (creative conceded this form)
- HC3. Every fact needs exactly ONE owner — one event source, one board generator, one money-path definition, one hard gate. (architect Round 3 through-line; confirmed by every attack that landed)
- HC4. The Stake SDK is private and the adapter cannot be executed here. Label anything assuming it runs as UNVERIFIABLE.
- HC5. No commits, no LICENSE; the git root is a shared parent directory. Do NOT commit to Documents/GitHub without explicit user direction.
- HC6. Compliance claims must be literally true or relabelled. "RTP 0.970000 EXACT" and "max win 25,000x" are conditional today; four documents assert an invariant the code violates.

## Decisions (Converged Through Debate)
- D1. The demo must SPLIT, not be relabelled: a local simulator (math QA, exercises engine.js) plus a thin event-player shim (the only production frontend, the only code tested against real RGS JSON). Conflating them in game.js is what let every event-stream bug hide behind "the demo works". (validator V3 + architect A1 + creative converged)
- D2. Fix contract drift by making PYTHON the single source of the event JSON, not by widening the parity test — a parity test over two hand-written mirrors certifies they agree on the same bug. The JS engine survives as the offline simulator, certified at line-eval plus constants. (creative Round 2; conceded by validator V7 and architect A3)
- D3. The wager's fate is delete-or-replace, not repair. Its EV contribution is exactly zero; it has no settlement path (R1); it never enters the book (V5/R2); its player choice does not exist in the event contract (A2). Creative's replacement: a pre-bonus, two-branch, precomputed decision (guaranteed 1x vs a precomputed 0-3x branch) inside a static book with a real, disclosed EV.
- D4. The adapter should CALL the core, not mirror it. Delete the false "the SDK adapter overrides draw_board to match" docstring (config.py:9) and call core draw_board/evaluate_board directly. (creative + validator V6 + architect A5)
- D5. Precompute books in Python with the seeded core and let the SDK consume them, rather than asking the SDK's reject-and-resample loop to produce randomness a deterministic exact-math core was designed not to have. (creative Round 2 on V4; refined by validator V4 and architect A4)
- D6. The adapter is "freeze until runnable", not "delete" — it is the only production path. (skeptic S6 Round 3)
- D7. Skill becomes a real SCORE metagame, not money. The hack already measures accuracy and elapsed time and shows a CLEAN/MESSY badge; make it first-class and persistent (personal best) so "skill layer" is true. RTP-safe by construction. (creative C2 Round 3)

## Risks & Mitigations
- RK1. Wager is EV-NEGATIVE above 12,500x. VERIFIED: spinner.py applies min(total, WINCAP) AFTER the bypass double, so E[take] = 12,500 < E[walk] = t for t > 12,500. RTP magnitude sub-1e-6 (max bonus in 200k natural sims 5,464x) so it is a purity/compliance defect, NOT a material leak — but "EV-neutral by construction" is FALSE above 12,500x and four documents assert it. Mitigation: delete the wager (D3), or exempt it from the cap, or bound the stake at WINCAP/2 and disclose.
- RK2. The demo's real ceiling is 1,143,660x — 45.7x the advertised 25,000x. VERIFIED BY LEAD: per-spin max 2,723x x SUM(multipliers 1..20 = 210) = 571,830x uncapped bonus, doubled by the wager. THREE cap semantics: core caps post-doubling (spinner.py:291); frontend never caps (game.js:411 returns round.bonus.total, game.js:472 doubles with no clamp); PAR sheet caps a formula (par.py:188). Mitigation: one cap constant on one path, plus a test asserting the demo cannot exceed it.
- RK3. Advertised hit rate is stale. VERIFIED BY LEAD: README.md:41, frontend/index.html:117, games/.../readme.txt:32,59 say 22.6% / "1 in 4.4"; par.hit_rate() = 0.189895, Monte Carlo = 0.1948. The 22.6% came from an earlier weight sweep, never re-derived after the final weights landed. Mitigation: regenerate every advertised number from the code; add a test that fails when a doc number disagrees with the computed one.
- RK4. Free-spin winInfo emits per-line wins UNMULTIPLIED and winWithoutMult INVERTED. VERIFIED BY LEAD: FreeSpin.wins holds raw payouts while FreeSpin.payout is multiplied; win_payload emits "win": raw and "winWithoutMult": raw/multiplier (dividing an already-raw value). Measured: spin.payout 1.4 at multiplier 7 vs sum(wins) = 0.2. The RGS would credit one number and the UI animate another. Mitigation: derive once at emission; drop the redundant per-line "win" field.
- RK5. JS and Python event streams HAVE ALREADY DIVERGED. VERIFIED: JS winInfo keys {type,totalWin,multiplier,wins,index} vs Python {index,type,totalWin,wins}; JS wins[0] {lineIndex,symbol,kind,payout} vs Python {symbol,kind,win,positions,meta}; JS reveal cells raw strings ("VAULT") vs Python [{"name":"VAULT"}]; JS emits no bypass events. The one cross-language test never constructs an event stream. Mitigation: D2.
- RK6. SDK adapter quotas are invented, not derived, and contradict the machine. VERIFIED: declared win quota 0.31 vs measured 0.189983 (~63% more wins demanded than the reels produce); bonus 0.0045 vs 0.005630 (~21% mass rejection); zero 0.6853 vs 0.804387. run_spin also loops on an unchanging sim (gamestate.py:50-54) and never reads the Distribution conditions. Consequence is INFERRED, not observed (SDK private) — claim "quotas are unmeetable against the repo's own math", NOT "infinite loop". Mitigation: derive quotas FROM the closed form, or precompute books in Python (D5).
- RK7. "adapter overrides draw_board" is FALSE. VERIFIED: config.py:9 asserts it; game_override.py is a bare `pass`; grep finds no draw_board under games/. It also ships shuffled BR0/FR0 strips (a windowed model) that run_spin never consults (independent per-position draws). Mitigation: D4.
- RK8. BypassResult is self-contradictory on the money path. VERIFIED: `taken` documented as "the player walked away" but hardcoded True (spinner.py:244); `target` always 0, never read; neither is emitted. The money path is in practice defined by the demo's inline Math.random. Mitigation: model the two-branch decision in the schema, or excise the wager from the book generator.
- RK9. Parity silently SKIPS without bun/node, so "92 passed" can mean parity unproven. VERIFIED: test_js_parity.py:43 pytest.skip. (bun IS present here; it did not skip on this machine.) Mitigation: hard-fail instead of skip.
- RK10. No provenance and no reproducible RTP artifact. VERIFIED: zero commits (unborn HEAD); no LICENSE; the exact-RTP derivation lives only in code. Mitigation: a committed baseline plus a reproducible PAR-sheet artifact tagged to a revision. NOTE HC5 — the git root is a shared parent directory.

## Open Questions (Unresolved Debate)
- OQ1. Can a Stake Engine book branch on a mid-round player decision? Docs say games are "entirely of static, pre-computed files" with "no server-side game logic executed at play time", and is_feature is documented as running WITHOUT player interaction. Zero doc matches for branch/choice/gamble. This is a ONE-QUESTION platform gate, not a research sprint; it gates D3 (replace vs delete). Ask the platform. If no: delete the wager, and either rename or accept the name is a promise the game does not keep.
- OQ2. What market is this actually for? The debate could NOT converge. Three framings: (a) a casino game (licensing, audit, provenance); (b) a skill-game (different regulation; HC2 forbids skill touching payout); (c) a B2B math/engine for other studios (the closed-form RTP + parity harness are the genuinely novel assets). Creative's reframe: without the wager the product is "a provably-fair 97% slot with an entry ritual" — honest, shippable, and indistinguishable from a thousand others, with the "NOTHING" half of its own name dead. Needs a USER DECISION before scope is set.
- OQ3. Delete the wager and keep the name, or replace it with a precomputed two-branch decision? Depends on OQ1. If deleted without replacing or renaming, the title lies — which all members agreed is worse than the current broken wager.
- OQ4. Is the demo a marketing artifact or an internal QA tool? The debate split. Validator called "ship the play-money demo" a second product with its own hosting/advertising exposure that validates nothing about the money path. This changes what "fix the demo" means.

## Adversarial Provenance
- skeptic survived: 6 of 7 (S4 conceded on arithmetic; S7 partial)
- validator survived: 6 of 7 (V3's "not an event player" framing conceded as misdiagnosis; the FALSE-LABEL half survives)
- researcher survived: 6 of 7 (R6's doc-contradiction half dropped as unfalsifiable; the import-fragility half survives)
- architect survived: 7 of 7 (all refined; A6 defended intact; A4's consequence clause conceded)
- creative survived: 4 of 7 (C5, C6, C7 conceded; C1/C2/C4 refined into buildable form)
- Total findings filtered out (conceded/destroyed): 8
- Dedup: 35 raw findings collapsed to ~10 distinct defects. The entire adapter cluster (V4, V5, V6, R2, R6, A4, A5, A6) is ONE decision: fix-or-freeze the never-run games/masterbetty_ball_or_nothing/ directory.

## Lead Note on Scope
The user asked for a critical review AND a path to market. Be ruthless about scope: the members repeatedly warned this bundle's risk is scope inflation. The highest-value work is the small number of things that make claims TRUE (RK2-RK9) plus the one strategic decision (OQ2). Do not turn this into a rewrite.
