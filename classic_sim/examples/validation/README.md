# Validation study: simulator vs real Classic metagame data

Validates the classic_sim metagame-prediction pipeline against real-world archives.
Data secured Aug 2026 (several sources are archival-fragile; local copies in `data/`).

## Studies

**S1 - Matchup-structure fidelity (primary).** Inject real archived Classic decklists
into the simulator and compare simulated matchup outcomes against real data.
Ground truth: Vicious Syndicate Classic Data Reaper #1/#2 (2021 Classic format =
exact June-2014 card pool, ~90k games) with a full archetype matchup matrix
including our six in-scope archetypes: Freeze Mage, Burn Mage, Face Hunter,
Sunshine (Midrange) Hunter, Aggro Warrior, Control Warrior. The matrix is
extracted: `extract_vs_matchups.py` reads the Tableau SVG export and recovers 172
matchups (38 more fell below vS's 100-game reporting threshold).

The export has no numeric labels, so winrates are decoded from the 9-step diverging
colour scale as BANDED estimates (band midpoints, +/- ~2.5pp) plus an exact ordinal
rank - use the ordinals for rank correlation. The decoding is validated by
complementarity: all 86 reciprocal pairs sum to exactly 100.0%, and it reproduces
the reports' prose (Control Warrior beats Face Hunter 67.5%, Freeze Mage 32.5%).
Output: `data/vs_classic/matchup_matrix.csv`.

In-scope submatrix (row winrate vs column; n/a = under threshold):

|                 | Face Hunter | Sunshine Hunter | Burn Mage | Freeze Mage | Aggro Warrior | Control Warrior |
|-----------------|------|------|------|------|------|------|
| Face Hunter     |  --  | 62.5 | 53.0 | 57.5 | 42.5 | 32.5 |
| Sunshine Hunter | 37.5 |  --  | n/a  | n/a  | n/a  | 37.5 |
| Burn Mage       | 47.0 | n/a  |  --  | 50.0 | n/a  | 32.5 |
| Freeze Mage     | 42.5 | n/a  | 50.0 |  --  | n/a  | 32.5 |
| Aggro Warrior   | 57.5 | n/a  | n/a  | n/a  |  --  | 37.5 |
| Control Warrior | 67.5 | 62.5 | 67.5 | 67.5 | 62.5 |  --  |

Control Warrior beats every in-scope archetype, which makes it the sharpest single
prediction for the simulator to reproduce (or fail to).
Secondary ground truth: HSReplay RANKED_CLASSIC per-deck winrates + decklists
(Wayback capture 2021-05-04, 88 Mage/Hunter/Warrior decks).

**S1 results (run 2026-08-06, after the legendaries pass).** All 88 real decks
are now fully constructible (`extract_hsreplay_decklists.py`), so for the
first time this could run on genuine archived decklists rather than
approximations. `run_s1_matchups.py` picks one representative real deck per
named archetype by signature-card score (no archetype label exists in the
Wayback capture - its `archetype_id` is a single per-class sentinel, not a
real classification), then simulates all 20 in-scope matchup pairs that have
real ground truth, 60 games each, with `GreedyActionSmart` piloting both sides.

**Spearman rank correlation (real ordinal vs. simulated win rate): 0.366.**
Positive but weak - directionally right more than half the time, wrong often
enough that this isn't yet a confident validation. The clearest single cause:
**Freeze Mage's simulated results are bad in every matchup it's in**
(11.7% vs. Face Hunter where real is 42.5%; 38.3% vs. Burn Mage where real is
50.0%; 0.0%/60 games vs. Control Warrior where real is 32.5%) - a systematic,
one-sided pattern across all three of its matchups, not a one-off. Freeze
Mage's real gameplan is delayed-value control (survive on Ice Block/armor,
win on fatigue or a late Alexstrasza+burn line); `GreedyActionSmart`'s 1-ply
lookahead has no way to value "correct now, win in 15 turns" over immediate
board/health swings, so it's a plausible confound that the *strategy*, not
the *card implementations*, is what's failing to reproduce Freeze Mage's real
performance. A second, smaller effect: Face Hunter vs. Aggro Warrior inverts
outright (sim: Face favoured 75%; real: Aggro Warrior favoured, Face only
42.5%) - possibly genuine archetype-representative imprecision (the specific
real decklist picked for "Aggro Warrior" scored lower on its signature set,
7-8, than Face Hunter's 17, so it may be a noisier example of the archetype).

Full comparison: `data/s1_simulated_matrix.csv`.

**S1 re-run with guided MCTS (2026-08-06), distributed across dwail1/dwail2.**
Confirmed the agent-skill hypothesis above rather than just speculating about
it. Ran the same 20 matchups with `MCTS(iterations=150, guided=True)` piloting
both sides instead of `GreedyActionSmart` - the strongest agent in the
codebase (95% vs. `GreedyActionSmart` at this setting, see the engine notes),
but too slow to run locally in reasonable time (~25s/game vs. ~1s for greedy).
Split the 20 pairs across dwail1 and dwail2 (`run_s1_matchups_remote.py
--shard i/2`, 18 and 10 cores respectively via joblib - dwail2 was left more
headroom since it had another job already running), 40 games/matchup, ~15
minutes wall-clock total instead of the multi-hour local estimate.

**Spearman rank correlation: 0.607**, up from 0.366. Freeze Mage specifically
went from "loses almost everything" to roughly matching real win rates: vs.
Face Hunter 11.7% -> 57.5% (real 42.5%), vs. Control Warrior 0.0% -> 12.5%
(real 32.5%, still under but no longer a 0/40 wipeout), vs. Burn Mage
38.3% -> 47.5% (real 50.0%, near-exact). Confirms the original diagnosis:
`GreedyActionSmart`'s 1-ply lookahead, not the card implementations, was
suppressing Freeze Mage's real performance. Not every gap closed - Face
Hunter vs. Sunshine Hunter is still inverted (sim 40% vs. real 62.5% either
way) and a few matchups overshot in the correct direction rather than landing
close - so 0.607 is meaningfully better evidence, not a finished validation.
Full comparison: `data/s1_mcts_matrix.csv`. Deployment for the curious: the
tarball shipped was `src/` + `examples/validation/` (minus the 592MB Zenodo
archive) via scp, run under a pyenv 3.13 venv on each machine (the engine
needs `typing.Self`, unavailable on the machines' default Python 3.8).

**Agent calibration (CMA-ES), following on from the S1 diagnosis.** S1 showed
`GreedyActionSmart`'s hand-tuned 21-feature linear heuristic is a real ceiling
- guided MCTS (whose leaf evaluation is a hardcoded copy of the same weights)
improved correlation from 0.366 to 0.607 purely by searching deeper with the
*same* evaluation function. Rather than accept the hand-tuned weights (or the
21-feature basis they're built on) as fixed, calibrated them against the real
matchup matrix directly - scoped out in detail before building anything (see
session notes), including working through *why* CMA-ES specifically (a
~27-dimensional, noisy, non-differentiable, unevenly-scaled-parameter
optimization is squarely its niche - Bayesian optimization wants far fewer
evaluations than we can afford; plain isotropic evolution strategies ignore
the cross-parameter correlation that matters at this dimensionality) and
what the objective needs to guard against (pure win-rate matching is
gameable - an archetype that already overperforms real players could satisfy
the loss by getting *worse*, not more realistic, so the objective includes a
one-sided skill-floor penalty that only fires on regressions vs. a fixed
`RandomAction` baseline, never rewards exceeding it).

Added 6 features `GreedyActionSmart`'s original 21 structurally can't express
- lethal margin (both directions), weapon durability differential, a
reciprocal (non-linear-in-state, linear-in-weight) fatigue-proximity term,
hero power availability, and unused mana - defaulting to weight 0 so
`GreedyActionSmart()`'s out-of-the-box behaviour is unchanged until
calibration finds a reason to use them. Built on the existing distributed
tournament framework (`metagame.py`'s `run_ssh_tournament`/`run_host` +
`remote_simulator.py`'s dill-over-stdin protocol) rather than a fresh
deploy - dwail1/dwail2 already had a working `venv` with every dependency,
and it's the path their other MAP-Elites tooling expects to find in a
working state. New code: `calibrate_greedy_weights.py` (the CMA-ES loop +
loss function), `calibrate_remote_worker.py` (sibling to
`remote_simulator.py`), `analyze_calibration.py` (confirm-phase + ablation),
`evaluate_cv_generalization.py` (leave-one-archetype-out scoring).

*Result (60-generation search, both machines, ~27k games; confirm phase at
full 60-games/matchup fidelity):*

| | matching MSE (real vs. sim win-rate %, lower is better) |
|---|---|
| Default weights | 487.5 |
| Calibrated weights | **204.1** |

Real improvement, not a rounding error - roughly 58% lower squared error
against the vS matchup matrix. Skill-floor check (win rate vs. `RandomAction`,
should hold steady or improve): 4 of 6 archetypes held steady or improved;
Freeze Mage dipped trivially (1.000 -> 0.983, one extra loss in 60 games) and
Control Warrior dipped more than is comfortable (1.000 -> 0.900). The
skill-floor penalty is evaluated on noisy, early-stopped (4-16 game) samples
during the search loop, so a real but modest regression like Control
Warrior's ~10pp drop can slip through detection some fraction of the time -
worth tightening (more games per skill-floor check, or a larger
`--lambda-skill`) before treating this vector as final, not just a one-off
finding to shrug at.

*Feature ablation* (zero each new feature's fitted weight individually,
holding the rest fixed, re-measure matching MSE - a cheap proxy for
importance, not a full re-optimization; deltas near the ~30-point mark are
within the noise of a 60-game-per-matchup sample and shouldn't be
over-read):

| feature removed | MSE | delta vs. full (204.1) |
|---|---|---|
| `lethal_margin_theirs` | 332.1 | +128.0 |
| `fatigue_proximity` | 266.1 | +62.0 |
| `lethal_margin_mine` | 265.7 | +61.6 |
| `hero_power_available_difference` | 247.2 | +43.1 |
| `unused_mana` | 207.8 | +3.7 (noise) |
| `weapon_durability_difference` | 177.2 | -26.9 (noise, or actively unhelpful) |

The threat-of-lethal and fatigue-proximity features are carrying real
weight; hero power availability plausibly too. Weapon durability and unused
mana were already fitted to near-zero weights and removing them doesn't
clearly hurt (`weapon_durability_difference` improving on removal suggests
its tiny fitted weight is noise-fit, not signal) - candidates to drop in a
future pass rather than genuinely denser signal.

*Leave-one-archetype-out cross-validation* (does calibration generalize, or
did it just memorize the 20 real points? - fit 6 times, each excluding one
archetype's real matchups, then score that fold's fitted weights against
only the held-out matchups it never saw):

| archetype held out | held-out pairs | default MSE | calibrated MSE |
|---|---|---|---|
| Face Hunter | 10 | 451.1 | 645.2 |
| Sunshine Hunter | 4 | 142.4 | 202.1 |
| Freeze Mage | 6 | 666.2 | 1187.5 |
| Burn Mage | 6 | 283.2 | **272.3** |
| Aggro Warrior | 4 | 584.0 | **403.5** |
| Control Warrior | 10 | 411.2 | 1009.6 |
| **overall** | 40 | **423.0** | **620.0** |

**This is the finding that matters more than the headline in-sample number
above, and it's a negative one: on matchups a fold never saw during fitting,
the calibrated weights do worse than the default weights overall (620.0 vs.
423.0 MSE) - only Burn Mage and Aggro Warrior generalized; Face Hunter,
Sunshine Hunter, Freeze Mage, and Control Warrior got worse, Freeze Mage and
Control Warrior by a lot.** Read together with the in-sample result
(487.5 -> 204.1 MSE, fit on all 20 points), this is a textbook overfitting
signature: a ~27-parameter model fit against only 20 sparse, mutually
correlated real data points (each held-out fold has as few as 14-16 training
points) can drive the training loss down without learning anything that
transfers - exactly the risk flagged before any of this was built (see the
regularization rationale above), and exactly why the CV step existed rather
than trusting the in-sample number. `lambda_reg=0.05` evidently wasn't
enough restraint for the amount of ground truth available.

**Conclusion: this calibration run should not be treated as a validated
improvement over the hand-tuned defaults - the in-sample fit looks good, the
cross-validation says it doesn't reliably generalize.** Worth doing
differently before trusting a calibrated vector: stronger regularization
(a materially higher `lambda_reg`, or a stricter prior that only allows the
new features to move, leaving the original 21 fixed), fewer parameters (the
ablation above already suggests dropping `weapon_durability_difference` and
`unused_mana`, which fit to near-zero/noise anyway - down to ~25 dimensions
against 20 points is still tight but less so), or more real ground truth
(the vS matrix's 172 total matchups only gave 20 among our 6 archetypes -
extending representative-archetype coverage would help most). Not attempted
in this pass, given the compute already spent - a reasonable next step
before spending more.

Artifacts: `data/calibrated_weights_full.json` (full-data fit),
`data/calibration_confirm.json` (confirm-phase + ablation detail),
`data/cv_weights_<Archetype>.json` x6 and `data/cv_generalization.json`
(cross-validation).

**Self-play skill training - a cleaner test of the same idea.** The
win-rate-calibration overfitting above raised an obvious follow-up: what if
the agent is just trained to play *well*, with zero exposure to the real
win-rate target anywhere in the loop, on the hypothesis that a genuinely
stronger player naturally reflects real human play better as a side effect
of being stronger - rather than by being fit to match it? This is the same
mechanism that already worked once: guided MCTS, using the *identical*
hand-tuned weights but searching deeper, lifted correlation from 0.366 to
0.607 purely by playing better (see the MCTS section above). This tests
whether evolving stronger weights does the same thing.

`train_self_play_skill.py` optimizes `GreedyActionSmart`'s weights via
CMA-ES against a small, growing **hall-of-fame** (starts as just the default
weights; each generation's best candidate gets promoted in if it decisively
beats the most recent champion, keeping the last 3 - fitness against a
*fixed* opponent plateaus once it's reliably beaten, and averaging across
several past champions rather than only the newest guards against narrowly
exploiting one opponent's blind spots instead of being generally strong).
Trained on **mirror matches from a rotating sample of the full 88-deck real
archive** (resampled every generation), deliberately *not* the 6
representative archetype decks used for the real-matchup evaluation - so a
good result means "got better at Hearthstone", not "learned to pilot these
6 specific decks." No matching loss, no regularization toward the defaults,
no skill-floor penalty - nothing in the objective but "did you win".

Training converged in 23 generations (not the full 80-generation budget),
stopping on stagnation (10 generations with no successful promotion) after
4 promotions: default -> gen1 -> gen4 -> gen6 -> gen13 (final champion).
Healthy self-play dynamics throughout - win rate against the hall-of-fame
oscillated around 50-65% rather than saturating near 100%, meaning the
opponent kept pace rather than the search stalling against something
already fully beaten.

*Result, same confirm-phase methodology (60 games/matchup) as everything
above:*

| | matching MSE (lower is better match to real win rates) |
|---|---|
| Default weights | 486.7 |
| Win-rate-calibrated (in-sample, known to overfit - see above) | 222.7 |
| **Self-play champion** | **314.6** |

Read this next to the calibration section's honest number, not the
in-sample one: win-rate-calibration's *true* held-out performance (measured
by cross-validation) was 620.0 - worse than default. Self-play's 314.6 needed
no held-out correction in the first place, since it never touched the
target at any point - what you see is what you get, the same way the
default weights' 486.7 needs no correction. On that fair, apples-to-apples
basis (numbers that don't need a held-out asterisk), **self-play beats both
the defaults (486.7) and calibration's honest generalization performance
(620.0), using zero knowledge of what the real answer was.** It doesn't
close the gap to calibration's over-fit in-sample number, which is exactly
what should happen - that number was inflated by curve-fitting, not a
target self-play should be expected to reach.

This is a genuinely positive result for the hypothesis: skill, pursued for
its own sake, transfers to real-world predictive accuracy better than
fitting the target does once overfitting is accounted for - about a 35%
MSE reduction over the hand-tuned defaults from playing strength alone.
Skill-floor check (win rate vs. `RandomAction`, default -> champion): 4 of 6
archetypes held steady or improved to 100%, Burn Mage dipped trivially
(1.000 -> 0.983), Control Warrior dipped more (1.000 -> 0.817) - the same
archetype that was hardest to keep stable in the calibration attempt too,
suggestive of something Control-Warrior-specific being genuinely tricky for
a linear heuristic rather than an artifact of either training method.

One caveat stated plainly: the 6 representative decks are members of the
same 88-deck pool training sampled from, so it's not a strictly disjoint
held-out set the way the CV folds were - a specific representative deck may
have been mirror-matched a handful of times over 23 generations by chance.
Much milder than the calibration run's overfitting (nothing here ever saw
the actual target *numbers*, only game outcomes), but worth a fully disjoint
deck split in any follow-up.

Artifacts: `train_self_play_skill.py`, `evaluate_self_play_vs_real.py`,
`data/self_play_champion.json` (hall-of-fame + final weights),
`data/self_play_generations.csv` (promotion history), `data/self_play_vs_real.json`.

**Does search depth and evaluation quality compound?** Two independent
improvements had been found - guided MCTS (deeper search, hand-tuned
weights) took correlation from 0.366 to 0.607; self-play (shallow greedy
search, better weights) cut matching MSE from 486.7 to 314.6 - and nothing
had tested them *together*. `montecarlotreesearch.py`'s guided leaf
evaluation (`evaluate_position`) was a hardcoded copy of the hand-tuned
weights with no way to swap them; threaded `weights` through as a real
parameter instead of a module-level constant (`state_value` ->
`rollout` -> `best_action`, plus `MCTS.__init__`'s new `eval_weights` arg)
rather than monkeypatching the global - the calibration work already hit a
bug from mutable-global state not surviving into a separate worker process,
not repeating that here. Also extended `evaluate_position` with the same 6
features `GreedyActionSmart` gained, so the self-play champion's 27-weight
vector is actually compatible with it.

Re-ran the guided-MCTS S1 matchups (same 40 games/matchup, same dwail1/dwail2
split) with the self-play champion's weights as the leaf evaluator instead
of the hand-tuned defaults:

| | Spearman correlation | matching MSE |
|---|---|---|
| MCTS + hand-tuned weights (baseline) | 0.607 | 189.0 |
| MCTS + self-play champion weights | **0.629** | **227.7** |

A mixed result, reported as it is rather than rounded up or down: rank
correlation improved a little further (0.607 -> 0.629, a real but modest
gain next to the 0.366 -> 0.607 jump search depth alone provided), but
absolute calibration got worse (MSE 189.0 -> 227.7). Plausible reason: the
self-play champion was optimized purely to *win*, with no exposure to real
win-rate magnitudes - paired with deep search, it likely converts small
edges into more decisive (further from 50%) outcomes than real, imperfect
human play does, which can improve *ranking* (which side is favoured)
while hurting *calibration* (by how much) at the same time. The two
improvements don't stack as cleanly as either alone would suggest - search
depth is still carrying most of the weight, and the two aren't simply
additive.

Artifacts: `data/s1_mcts_selfplay_shard{0,1}.csv`, `data/s1_mcts_selfplay_matrix.csv`.

**Non-standard decks - a first step.** Every validation run above uses the
same 6 hand-picked archetype representatives. But the thesis's actual
mechanism (an agent traversing a MAP-Elites archive to predict metagame
shifts) means the agent needs to handle decks *between* metagames too - ones
outside the current 6 named archetypes. Rather than jump straight to fully
synthetic decks (random generation, or MAP-Elites archive output - both
available: `Deck.generate_random`/`generate_random_n_copies` in `zones.py`,
and saved archives under `dwailmeta_0_post_nerf/` and
`hunter_vs_15_300_x_5/` etc.), the first step used a safer middle ground:
the other **82 real HSReplay decks** in `constructible_decklists.csv` that
aren't one of the 6 signature-matched archetypes - still human-played, real
decklists, just ones no validation work had touched yet.

Unlike the pairwise vS matrix, HSReplay's own `win_rate` column is a deck's
win rate across the *whole field it was actually played in* - there's no
pairwise ground truth for these 82, so the right comparison is a full
internal round robin (every pair played once; `game.play_game()` already
randomises who goes first, so an unordered round robin isn't biased toward
whichever deck is passed as "player") rather than more archetype-vs-archetype
pairs. New code: `run_offarchetype_tournament.py` (round robin + early-
stopping matchup evaluation, same sequential-t-test shape as
`calibrate_greedy_weights.py`) + `tournament_remote_worker.py`, using the
same dill-over-SSH distribution pattern as everything else this session.

First pass, `GreedyActionSmart` (default weights) both sides, distributed
across dwail1/dwail2:

| decks | pairs | games | Spearman (real win_rate vs sim win_rate) | MSE (pct points^2) |
|---|---|---|---|---|
| 82 | 3321 | 37,551 | **0.639** | 258.7 |

Notably higher than S1's pairwise 0.366 - though these aren't the same
measurement (deck-level aggregate win rate across a large internal field vs.
one pairwise matchup ordinal against 5 others), so it isn't a clean
apples-to-apples improvement. A plausible reading: ranking a deck's overall
power against a broad field averages out matchup-specific noise that a
single pairwise comparison can't, so this may be an easier prediction task
by construction, not evidence the greedy heuristic got better at anything.
Artifacts: `data/offarchetype_greedy.csv`, `data/offarchetype_greedy.summary.json`.

**Does the search-depth lift hold here?** S1 showed guided MCTS lifting
pairwise correlation 0.366 -> 0.607. Natural next question: does the same
lift show up on this internal-round-robin task? The full 3321-pair round
robin is far too expensive at MCTS depth (deep guided search is roughly two
orders of magnitude slower per game than greedy), so this used a 24-deck
subsample - the off-archetype decks with the most real HSReplay
`total_games` (`--sort-by-games`), chosen for a more reliable real win_rate
to compare against rather than an arbitrary slice. `GreedyActionSmart` was
re-run on the *same* 24-deck subsample (not compared against the full-82
number above, to keep pool size and composition from confounding the
agent comparison) as the baseline. Agent under test: guided MCTS with the
self-play champion's weights as leaf evaluator - the best-performing
combination S1 found.

| agent | decks | pairs | games | Spearman | MSE (pct points^2) |
|---|---|---|---|---|---|
| GreedyActionSmart (default weights) | 24 | 276 | 3,091 | **0.534** | **269.9** |
| Guided MCTS + self-play champion weights | 24 | 276 | 3,215 | 0.309 | 324.6 |

The opposite of S1's result: here MCTS is worse on both rank correlation
and calibration, not better. Reported as found, not smoothed over. A
plausible reason this doesn't match S1: S1 compared *distinct archetypes*
against each other, where matchups have real structural power gaps for
deep search to find and exploit correctly; this task is decks *within the
same off-archetype pool* playing a broad round robin against decks of
similar overall quality (that's why they cleared HSReplay's win-rate bar in
the first place) - the signal search depth needs to exploit is weaker and
noisier here, and the self-play champion's bias toward decisive, winning
play (already flagged in the compounding result above as a driver of worse
calibration) may dominate more when matchups are closer to coin flips.
Consistent with, not contradicting, this session's running theme: search
depth and the self-play-trained evaluator are not a uniform improvement -
their effect depends on the structure of the matchups being evaluated.
Artifacts: `data/offarchetype_mcts.csv`, `data/offarchetype_greedy_sameN.csv`.

**Evolving genuinely non-standard decks.** The scoped follow-up: perturb/
evolve the 82-deck pool rather than just measuring it. User's choice among
three fitness options (power alone; power + MAP-Elites diversity; novelty-
as-objective) was **power + diversity**, to stay faithful to the thesis's
actual mechanism (an agent traversing a MAP-Elites archive), not just a
hill-climb toward the single strongest deck.

New code: `evolve_offarchetype_decks.py` + `evolve_remote_worker.py`, reusing
`map_elites.py`'s existing `Archive` (same phenotype axes as
`metaspace_generation/coevolution.py` - hand size x turns - and the same
bin-elite-selection loop shape) rather than building new archive machinery.
Differences from `coevolution.py`: only the DECK evolves, not the agent -
the agent is fixed to the self-play champion weights (the best validated
this session) via `GreedyActionSmart`, not MCTS, since an evolutionary loop
needs many cheap generations, not a few deep-search games. One archive per
class (decks are class-locked), seeded from that class's real off-archetype
decks (already legal, not a cold random start). Mutation swaps 0-3
individual card slots per generation for a same-class pool card, respecting
real copy-count legality (max 2, or 1 for legendaries via
`get_legendary_cards()`). Fitness = mean win rate vs a fixed 9-deck real
gauntlet (3 decks/class, most-played on HSReplay). Novelty (card-overlap
distance to the nearest *original* seed deck) is tracked per generation as
a diagnostic only - per the user's choice, it's not part of fitness/selection.

15 generations, population/selection count 20, distributed across
dwail1/dwail2:

| class | seed mean fitness | gen 14 mean fitness | gen 14 best fitness | gen 14 mean novelty (of 30) |
|---|---|---|---|---|
| Hunter | 0.537 (gen 0) | 0.592 | 0.774 | 5.2 |
| Mage | 0.362 (gen 0) | 0.496 | 0.704 | 5.2 |
| Warrior | 0.627 (gen 0) | 0.704 | 0.829 | 2.5 |

A clear cross-class pattern, not noise: Mage's real off-archetype decks
started weakest against the gauntlet and improved the most in relative
terms (0.362 -> 0.496, +37%); Warrior started strongest and drifted least
(novelty 2.5/30 vs Hunter/Mage's 5.2/30) - evolution found comparatively
little to change because a near-optimal deck was likely already in the
seed pool. Checked directly: the best Warrior deck found at generation 14
is a **verbatim match** (0 cards changed) to its nearest real seed deck -
mutation explored around it every generation but never beat it. Hunter and
Mage's best decks are small, plausible edits (3-4 card swaps) from their
best real seed - e.g. Hunter's fittest evolved deck (0.774) swaps out Leeroy
Jenkins, Hunter's Mark, and Ironbeak Owl for Bloodmage Thalnos, Oasis
Snapjaw, and Tauren Warrior versus its nearest real ancestor. Read narrowly:
this is a first, cheap demonstration that the pipeline can find real,
legal, incrementally-different decks that beat their real ancestors against
a fixed real-deck gauntlet - not evidence of large-scale, qualitatively
novel metagame drift (5/30 cards changed at 15 generations is a small
neighbourhood search, and fitness plateaued well before generation 14 in
two of three classes).

Artifacts: `data/evolve_offarchetype_{hunter,mage,warrior}_history.csv`,
`data/evolve_offarchetype_{hunter,mage,warrior}_generation{0..14}.json`.

Not yet done: run this for longer (fitness hadn't clearly converged for
Mage), widen the gauntlet beyond 9 decks so fitness isn't overfit to a
small fixed field, and re-evaluate the fittest evolved decks against the
full 82-deck pool (and eventually with guided MCTS) the same way the
un-evolved decks were - the honest test of whether evolution actually
produces more metagame-plausible decks, not just gauntlet specialists.

**S2 - Archetype emergence.** Card-overlap between MAP-Elites archive clusters and
real archetype cores. Report honestly: the mage archive collapsed deck-wise
(715 elites, 24 unique decks); hunter/warrior archives retained diversity (537/590).
Emergent elites are neutral-heavy tempo piles - partly attributable to the missing
legendary win conditions.

**S3 - Historical nerf response (headline).** Re-run the metagame pipeline with the
real September 22 2014 Starving Buzzard nerf (2-mana 2/1 -> 5-mana 3/2; card is in
the pool) and compare against the measured real response.

Ground truth is built: `buzzard_nerf_series.py` over 33,697 ranked 2014 decks
(Zenodo/HearthPwn), classes inferred from signature cards and normalised across
Mage/Hunter/Warrior only - the same 3-class world the simulator models.

| month | decks | hunter | mage | warrior | buzzard/hunter |
|---|---|---|---|---|---|
| 2014-06 |  841 | 31.2% | 39.0% | 29.8% | 61.1% |
| 2014-07 | 1188 | 30.4% | 39.2% | 30.4% | 76.2% |
| 2014-08 | 1247 | 27.5% | 38.5% | 34.0% | 74.6% |
| 2014-09 |  897 | 32.6% | 39.7% | 27.8% | 31.8% <- nerf (22nd) |
| 2014-10 |  821 | 35.0% | 34.2% | 30.8% | 19.2% |
| 2014-11 |  890 | 34.7% | 35.3% | 30.0% | 19.7% |
| 2014-12 | 1570 | 29.4% | 43.4% | 27.1% | 11.9% |

Two distinct predictions to test, and the interesting part is that they diverge:

1. **Card-level: collapse.** Buzzard adoption within Hunter decks falls 67.7% ->
   16.9% (pre/post monthly mean), visibly starting in the nerf month itself.
2. **Class-level: no collapse.** Hunter share is *flat to slightly up* (31.6% ->
   33.0%). The popular "Hunter died" narrative is not supported by submission
   share - players abandoned the card, not the class, and rebuilt around other
   packages.

A simulator that reproduces (1) is capturing card-level power; one that also
reproduces (2) is capturing genuine metagame adaptation. Confound to state
plainly: the real 2014 ladder ran Classic + Naxxramas, and the Hunter rebuild
leaned on Naxx cards (Undertaker, Haunted Creeper) the simulator cannot represent,
so (2) is the weaker of the two comparisons.

## Deck representability

Measured 2026-08-06 (before the legendaries pass): real 2021 Classic decks
fully constructible in the sim pool were 5/88. The entire gap was 15
legendaries (Alexstrasza 53 decks, Grommash 32, Ragnaros 30, Cairne 29,
Thalnos 27, Leeroy 24, Geddon 23, Sylvanas 23, Harrison 19, Antonidas 15,
Black Knight 6, Tinkmaster 6, Ysera 3, King Krush 1, Nat Pagle 1).

Re-measured 2026-08-06 (after): **88/88** - every real archived Classic
Mage/Hunter/Warrior deck in the HSReplay sample is now fully constructible
(`extract_hsreplay_decklists.py`, `data/hsreplay_classic/constructible_decklists.csv`).

## data/ contents

- `vs_classic/` - vS Classic Data Reaper report pages (HTML + extracted .txt),
  live-data page snapshots, Tableau matchup-matrix PNG (colors only; numeric
  crosstab TODO).
- `hsreplay_classic/` - Wayback captures of HSReplay list_decks_by_win_rate_v2
  for RANKED_CLASSIC (2021-05-04 is the substantive one; later captures are
  post-mortem). dbfId -> name mapping via HearthstoneJSON cards.collectible.json.
- `nerf_docs/` - Starving Buzzard wiki page, meta-history wiki, Warsong/BGH
  articles (qualitative nerf ground truth).
- `decks/` (gitignored, large) - Zenodo "Hearthstone Decks Dataset"
  (DOI 10.5281/zenodo.10198504, CC-BY 4.0): decks.csv 56MB (852k decks
  2013-2020, 75k dated 2014), cards.csv 564MB (deck -> card join). Re-download
  from the DOI if absent.
