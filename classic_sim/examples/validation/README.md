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

**S2 - Archetype emergence.** Card-overlap between MAP-Elites archive clusters and
real archetype cores. Report honestly: the mage archive collapsed deck-wise
(715 elites, 24 unique decks); hunter/warrior archives retained diversity (537/590).
Emergent elites are neutral-heavy tempo piles - partly attributable to the missing
legendary win conditions.

**S3 - Historical nerf response (headline).** Re-run the metagame pipeline with the
real September 22 2014 Starving Buzzard nerf (2-mana 2/1 -> 5-mana 3/2; card is in
the pool) and compare predicted Hunter archetype-share shift against the documented
real collapse ("Hunter dead" era). Quantitative real signal: Hunter deck-submission
share around the nerf date from the Zenodo/HearthPwn deck dataset (75k decks dated
2014). Note the sim's fixed 3-class world vs the real 9-class meta when interpreting.

## Deck representability (measured 2026-08-06)

Real 2021 Classic decks fully constructible in the current sim pool: 5/88.
The entire gap is 15 legendaries (Alexstrasza 53 decks, Grommash 32, Ragnaros 30,
Cairne 29, Thalnos 27, Leeroy 24, Geddon 23, Sylvanas 23, Harrison 19, Antonidas 15,
Black Knight 6, Tinkmaster 6, Ysera 3, King Krush 1, Nat Pagle 1). Implementing
these unlocks near-total decklist fidelity. Nozdormu/Cho/ETC/Millhouse: unused by
real decks, intentionally skipped.

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
