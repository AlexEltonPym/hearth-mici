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
