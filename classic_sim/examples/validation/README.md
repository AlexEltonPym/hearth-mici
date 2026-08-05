# Validation study: simulator vs real Classic metagame data

Validates the classic_sim metagame-prediction pipeline against real-world archives.
Data secured Aug 2026 (several sources are archival-fragile; local copies in `data/`).

## Studies

**S1 - Matchup-structure fidelity (primary).** Inject real archived Classic decklists
into the simulator and compare simulated matchup outcomes against real data.
Ground truth: Vicious Syndicate Classic Data Reaper #1/#2 (2021 Classic format =
exact June-2014 card pool, ~90k games) with a full archetype matchup matrix
including our six in-scope archetypes: Freeze Mage, Burn Mage, Face Hunter,
Sunshine (Midrange) Hunter, Aggro Warrior, Control Warrior. Directional prose
claims already extracted (e.g. Control Warrior dominates Face Hunter; Freeze Mage
loses badly to Control Warrior). Numeric matrix pending Tableau crosstab extraction
(workbook: ClassicDataReaper2-MatchupWinRates on Tableau Public).
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
