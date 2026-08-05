# Wish for the perfect card: Exploring Computational Metagame Design for Competetive Strategy Games

Consolidated PhD codebase (thesis conferred 2026). The thesis itself (LaTeX source,
final PDF, examiner corrections) lives outside this repo at `../thesis`.

## CardLab

The user interface prototype we built for this thesis, hosted at:

http://hearth-mici.web.app

`node_modules` is not kept; `npm install` restores it from the committed lockfiles.

## classic_sim

The Hearthstone Classic simulation engine prototype (Mage/Hunter/Warrior, ~200 cards).

- `src/` — the engine. Strategies in `strategy.py` (random, greedy 1-ply variants,
  UCT MCTS in `montecarlotreesearch.py`).
- `tests/` — run from `tests/` with `PYTHONPATH=../src`; `mcts_benchmark.py` is an
  agent-vs-agent harness with mirror decks.
- `examples/metaspace_generation` — MAP-Elites metaspace generation (coevolution.py):
  40x40 archives of (hand size x game length), elites are (21-weight policy, 30-card deck).
  Data in `data/` and `data_archive/` (local-only, gitignored).
- `examples/metagame_analysis` — metagame prediction: CMA-ES agents traverse the class
  archives (`metagame.py`), archetypes are HDBSCAN clusters, output is archetype share
  over generations (`history_viewer/`). The six final pre/post-nerf class archives are
  committed under `compare/`.
- `dwailmeta_*/` — the eight thesis metagame runs (pre/post Fireblast nerf). Each run's
  `agent_history.csv` (the archetype time-series behind the thesis figures) is committed;
  the bulky gifs/pickles/input copies in those dirs are local-only.
- `examples/archive/` — MAP-Elites generation runs and ablations (local-only, ~2GB).

## deck_evolution

Deep surrogate-assisted MAP-Elites deck building (`deck_evolver_spellsource.py` online
version, `offline_surrogate_mapelites.py` final offline version). Training data
snapshotted from the original Google Sheets into `data/surrogate_*.csv`.

## reports

Report generation code and the qualitative user study of CardLab (`study/` — participant
notes are committed; session recordings and `results.zip` are local-only, gitignored).

## SabberStone

A fork of the SabberStone project, used as simulator for CardLab
