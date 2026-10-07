BALL OR NOTHING
===============
game_id: masterbetty_ball_or_nothing

MECHANICS
---------
5 reels x 3 rows, 10 paylines, plus the BALLGAME free-spin feature.
THE BYPASS is a presentation-only minigame with no wager behind it.

Symbols
  BALL    top payer
  NUT     high
  SACK    mid
  COIN    low
  LOSS    blank
  WILD    substitutes for every payer; advances the BALLGAME multiplier
  VAULT   scatter - three or more anywhere opens the BALLGAME; never substitutes

Line rules (left to right from reel 0, wilds substitute)
  5 BALL     272.3x      5 NUT     100x       5 SACK    50x       5 COIN   20x
  4 BALL       5.0x      4 NUT     2.5x       4 SACK   1.5x       4 COIN    1.0x
  3 BALL       0.4x      3 NUT     0.2x       3 SACK  0.15x       3 COIN    0.1x
  5 WILD     272.3x      (wild pays at five only, so it can never outpay a longer line)
  VAULT breaks a line rather than substituting.

Reels (weights out of 1000, all reels identical within a set)
  Base:  BALL 87 / NUT 122 / SACK 148 / COIN 192 / LOSS 386 / WILD 40 / VAULT 25
  Free:  BALL 100 / NUT 130 / SACK 150 / COIN 170 / LOSS 360 / WILD 70 / VAULT 20

  These took real searching. Ten paylines reward dense reels with an 80%+ hit rate, which
  turns the game into losses disguised as wins; and a 10% wild made five-of-a-kind 1 in
  10,824 per line, ten times too common to pay a headline. At the values above the hit
  rate is ~19% per spin (1 in 5.2) and five BALL sits at 1 in 29,911 per line.

  The strip files are SHUFFLED, each column independently. A strip grouped by symbol would
  show three identical symbols on any window draw far more often than the weights allow,
  and one shared shuffle would put the same symbol on every reel at a given stop.

THE BALLGAME
------------
  Triggered by 3 / 4 / 5+ VAULTs, awarding 12 / 15 / 20 free spins on the free-game reels.
  A multiplier starts at 1x and gains +1 for every free spin containing a wild, applying
  from the NEXT spin onward, capped at 50.
  No retrigger: that is what keeps the bonus expectation closed form.

THE BYPASS
----------
  A sequence-memory minigame shown when the BALLGAME opens. Presentation only: it always
  grants access, and nothing the player does changes what the round pays.

  NO WAGER. An earlier revision offered a 50/50 double-or-lose on the BALLGAME total. It is
  removed: Stake books are entirely static, pre-computed files with no server-side logic at
  play time, so a mid-round decision has no settlement path. A pre-computed branch does not
  help - the client still cannot tell the server which branch was taken.

MATH
----
  exact RTP        0.970000   (target 0.97, house edge 3.00%)
  base share       0.5447     (56.1% of RTP)
  bonus share      0.4253     (43.9% of RTP)
  hit rate         ~19% of base spins (1 in 5.2)
  BALLGAME         0.005674   (1 in 176)
  top prize        272.3x     (five BALL)
  max multiplier   20x        (20 spins, +1 per wild-bearing spin)
  MAX WIN          25,000x    (wincap; the theoretical ceiling)

  RTP is exact, not estimated. Ten paylines were paid for one line's worth of work:
      E[spin] = 10 * E[single line]            (expectation is linear, so correlation
                                                between the paylines does not matter)
      E[line] = sum over all 7^5 = 16,807 symbol sequences, weighted exactly
      E[bonus] = sum over scatter buckets of S(spins) * E[free spin],
                 S = sum_i E[min(1 + K, cap)], K ~ Binomial(i-1, p_wild)
                                                (closed form via the binomial MGF)

  Re-solve after any change:
      python -m ball_or_nothing.cli tune 0.97

DISTRIBUTIONS
-------------
  winCap  quota 0.0002  win_criteria 25000, force_wincap
  bonus   quota 0.0045  force_freegame, scatter_triggers {3:12, 4:15, 5:20}
  win     quota 0.31
  0       quota 0.6853  win_criteria 0.0

WIN EVALUATION
--------------
  This adapter deliberately does NOT use the SDK's Lines.get_lines(). The published RTP,
  hit rate and max win are computed against ball_or_nothing.spinner.evaluate_board, and
  the frontend mirrors that same code. Running the books through a second, differently
  implemented line evaluator would make the shipped math a different machine from the
  audited one. The SDK is used for its wallet and event plumbing instead.

STATUS
------
UNRUN. github.com/StakeEngine/math-sdk is private, so `make setup` cannot install the
engine here. Written from the published docs; expect one round of API drift on first run.

OPEN PLATFORM QUESTION
----------------------
The one platform question - can a Stake book branch on a mid-round player decision? - was
answered from the platform's own documentation: no. See .omo/evidence/gate-answers.md.
