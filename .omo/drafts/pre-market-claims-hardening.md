---
slug: pre-market-claims-hardening
status: plan_complete_self_reviewed
intent: clear
review_required: true
plan_path: .omo/plans/pre-market-claims-hardening.md
plan_sha256: 189625db5a11486e6eff6ff563e9258b240d030baf14755012645a371fc9b7fb
review_round_id: r1-b8e12c93fa34
review_round_limit: 5
pending-action: review .omo/plans/pre-market-claims-hardening.md
review:
  plan_reviewer:
    status: gated_unavailable
    workspace_root: C:/Users/ShibbityShwab/Documents/GitHub/ball-or-nothing
    runtime_home: null
    target: .omo/plans/pre-market-claims-hardening.md
    round_id: r1-b8e12c93fa34
    plan_sha256: 189625db5a11486e6eff6ff563e9258b240d030baf14755012645a371fc9b7fb
    launch_id: l1-muxlfs9t
    session: null
    result: plan-reviewer spawn refused: plan gate locked (session was not a user-invoked ulw-plan workflow). Substituted notepad self-review: structural self-check passed (14 impl rows / 4 final rows, all grammar-valid, all category lines present, all GAP refs defined, header order correct); HC1-HC6, RK1-RK10 mitigations, OQ1-OQ4 gates, and lead scope note verified woven into todos. Recommend a follow-up user-invoked ulw-plan session for the high-accuracy plan-reviewer round if more rigor is wanted.
approach: Phase the plan as USER-INPUT GATES (OQ2 scope gate, OQ1+OQ3 wager gate, OQ4 demo gate) followed by three parallel execution waves that make every claim true (RK2-RK9), then the gated decisions (D3 wager fate, D1 demo split, D7 score metagame) and RK10 provenance, with no git commits to the shared parent (HC5).
---

# Draft: pre-market-claims-hardening

## Affected user and ideal state

Affected users: (1) the demo player (sees advertised numbers, spins the demo); (2) the casino operator/partner consuming the math claims (RTP, hit rate, max win); (3) the Stake integrator running the SDK adapter; (4) the developer running tests and parity (will never be silent-skipped again).

IS-1 | Every number the demo player sees is code-true: advertised max win and hit rate match computed values, and no demo spin can exceed the advertised cap | reason: the demo is the product's face; a number that lies is a compliance defect
IS-2 | The operator receives claims that are literally true and derivable from the shipped code (RTP exact closed-form, hit rate, max win) | reason: HC6 - claims must be literally true or relabelled
IS-3 | A player's win events carry one consistent money number (no inverted winWithoutMult, no unmulitplied wins) | reason: RGS credits one number, UI animates another today
IS-4 | The integrator gets an adapter that calls the Python core and consumes books with quotas matching the closed form | reason: HC3 one owner per fact; HC4 - anything assuming the SDK runs is labelled unverifiable
IS-5 | The developer's parity suite hard-fails instead of skipping, and Python is the single source of event JSON | reason: parity that skips certifies nothing; two hand mirrors certify shared bugs (D2)
IS-6 | The consumer of the finished product gets a demo that is an honest artifact (event-player) not a second money-path implementation | reason: D1 - conflating demo and money path hid every event-stream bug
IS-7 | The skill metagame is a real first-class score (persistent personal best) when the product is a skill-game | reason: D7 - "skill layer" must be true if claimed; HC2 - it must never touch payout
IS-8 | The developer has a reproducible PAR-sheet artifact tagging exact RTP to the code state | reason: RK10 - zero commits, no reproducible RTP artifact today

GAP-1 | demo ceiling is 1,143,660x vs advertised 25,000x (three cap semantics: core caps post-double, frontend never caps, PAR sheet caps a formula) | closes IS-1/IS-2 | todo 4
GAP-2 | advertised hit rate 22.6% stale (code: 0.1899) | closes IS-1/IS-2 | todo 5
GAP-3 | free-spin winInfo emits unmultiplied wins and inverted winWithoutMult | closes IS-3 | todo 6
GAP-4 | JS and Python event streams diverged | closes IS-5 | todo 10
GAP-5 | parity test silently skips without bun/node | closes IS-5 | todo 7
GAP-6 | false "adapter overrides draw_board" docstring + dead game_override.py | closes IS-4 | todo 8
GAP-7 | adapter quotas invented, contradict machine | closes IS-4 | todo 9
GAP-8 | no reproducible RTP artifact, zero commits | closes IS-8 | todo 14
GAP-9 | demo conflates simulator and money path | closes IS-6 | todo 12
GAP-10 | wager EV claim false above 12,500x (delete-or-replace per OQ1/OQ3) | closes IS-2/IS-3 | todo 11
GAP-11 | skill layer not first-class/persistent | closes IS-7 (only when OQ2=skill-game) | todo 13

## Components (topology ledger)

C1 gates | three user-input gates answered and recorded | active | .omo/evidence/gate-answers.md
C2 claims-core | cap semantics, hit-rate docs, winInfo emission made code-true | active | .omo/evidence/task-4|5|6.txt
C3 parity | parity suite hard-fails and Python becomes the event-JSON source | active | .omo/evidence/task-7|10.txt
C4 adapter | adapter calls core, quotas derived from closed form, books precomputed in Python | active (unverifiable against SDK until SDK repo is reachable - HC4) | .omo/evidence/task-8|9.txt
C5 gated-decisions | wager fate (D3), demo split (D1), score metagame (D7) | deferred on gates G1-G3 | .omo/evidence/task-11|12|13.txt
C6 provenance | reproducible PAR-sheet artifact + commit plan (no commits without direction - HC5) | active | .omo/evidence/task-14.txt

## Open assumptions (announced defaults)

A1 | test strategy = tests-after (repo has 92 passing tests; new claims get new tests) | framework: pytest + bun (bun is present on this machine) | reversible
A2 | RTP display in docs = 0.9700 (rounded presentation) derived from the closed form 0.969999; the PAR sheet carries the exact value; nothing may say "EXACT" next to a rounded value | HC6 | reversible
A3 | cap constant lives in Python config and is mirrored verbatim in engine.js; frontend caps by clamping to that constant at render | HC3 one owner per fact | reversible
A4 | adapter work is code-correctness only; no claim that the SDK runs (HC4 unverifiable) | HC4 | n/a
A5 | no git commits at all until the user directs where the repo lives (HC5 shared parent) | HC5 | reversible

## Findings (cited - path:lines)

Sourced from the hyperplan insight bundle (all lead-verified or survived adversarial debate); executor may re-read but not re-litigate.

F1 RTP exact = 0.969999 (base 0.5447 + bonus 0.4253) - src/ball_or_nothing/par.py
F2 RK2 cap semantics: src/ball_or_nothing/spinner.py:291 (cap post-double), frontend/game.js:411+472 (never caps, doubles), src/ball_or_nothing/par.py:188 (formula)
F3 RK3 stale hit rate: README.md:41, frontend/index.html:117, games/masterbetty_ball_or_nothing/readme.txt:32+59 vs par.hit_rate() 0.189895
F4 RK4 winInfo: src/ball_or_nothing/events.py (FreeSpin.wins raw, winWithoutMult = raw/multiplier)
F5 RK5 divergence: frontend/engine.js vs src/ball_or_nothing/events.py event keys
F6 RK6 quotas: games/masterbetty_ball_or_nothing/gamestate.py:50-54
F7 RK7 false override claim: src/ball_or_nothing/config.py:9 + games/masterbetty_ball_or_nothing/game_override.py (bare pass)
F8 RK8 BypassResult: src/ball_or_nothing/spinner.py:244 (taken hardcoded True, target always 0)
F9 RK9 skip: tests/test_js_parity.py:43 pytest.skip
F10 RK10 provenance: git root is a shared parent with unborn HEAD; no LICENSE

## Decisions (with rationale)

D1 demo split (simulator + event-player) - conflation let event bugs hide; executor implements per G3
D2 Python single source of event JSON; JS stays offline simulator certified at line-eval + constants
D3 wager delete-or-replace per G2 answers (replacement = precomputed two-branch decision in a static book with disclosed EV)
D4 adapter calls core draw_board/evaluate_board directly; delete false docstring
D5 books precomputed in Python with the seeded core; SDK consumes them
D6 adapter is freeze-until-runnable, not delete
D7 SCORE metagame first-class and persistent only when G1=skill-game

## Scope IN

- Make every claim true: cap semantics, hit rate, winInfo, parity hard-fail, event-source unification, adapter truth, quotas, provenance artifact (RK2-RK10)
- Gated decisions: wager fate (D3), demo split (D1), score metagame (D7)
- User-input gates G1 (OQ2 market), G2 (OQ1+OQ3 wager platform), G3 (OQ4 demo)

## Scope OUT (Must NOT have)

- No product rewrite, no new symbols/paylines/mechanics (lead scope note)
- No payout changes that break closed-form derivability (HC1)
- No skill-to-payout coupling (HC2)
- No git commit to the shared parent Documents/GitHub (HC5)
- No claim that the SDK adapter runs until the SDK repo is reachable (HC4)
- No relabelling instead of fixing where a fix is possible (HC6)

## Open questions

OQ1-OQ4 all surface as user-input gates G1-G3 in the plan (not as plan gaps).

## Approval gate
status: authorized-by-hyperplan-handoff

The parent session's hyperplan handoff explicitly delegates: "produce an EXECUTABLE WORK PLAN. Return it as your final response." That delegation is the approval to write the plan file. High-accuracy review (plan-reviewer) runs per the default review_required state recorded above.
