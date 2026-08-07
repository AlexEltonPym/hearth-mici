"""Does deck evolution actually beat the real decks it started from?

evolve_offarchetype_decks.py's own fitness signal (win rate vs a fixed
9-deck gauntlet) already showed evolved decks improving generation over
generation, but that's a narrow, fixed field - exactly the kind of thing
that can overfit to. This is the honest follow-up test flagged in the
README: take the fittest evolved deck per class, and its nearest real
ancestor (by card overlap), and play BOTH against the full 82-deck real
off-archetype pool - a much wider field neither was directly selected
against - under the same fixed agent (self-play champion weights via
GreedyActionSmart) used throughout evolution. If evolution generalizes,
the evolved deck's win rate against this wider field should be >= its
ancestor's; if it only overfit the small gauntlet, it won't be.

Usage (from classic_sim/examples/metagame_analysis):
  python evaluate_evolved_vs_pool.py --backend ssh --out data/evolved_vs_pool.csv
  python evaluate_evolved_vs_pool.py --backend ssh --games 60 --out data/evolved_vs_pool_confirm.csv

--games N: confirm-phase mode - plays exactly N games per matchup (min_games
== max_games == N, so early stopping can't cut a matchup short) instead of
the exploratory ~4-12 early-stopped default. The first pass at this
(default settings, ~9 games/matchup average) turned out to have a noise
floor (6.3pp, measured via the Warrior identical-deck control below) as
large as the effect it was trying to measure - not a confident answer.
"""
import sys, csv, json, argparse
from pathlib import Path
from statistics import mean
from collections import Counter

sys.path.append('../../src')
sys.path.append('../validation')

from run_offarchetype_tournament import load_offarchetype_decks
from evolve_offarchetype_decks import play_matchup_till_stoppage, run_matchups_local, run_matchups_ssh, _run_one

HERE = Path(__file__).parent
OUT_DIR = HERE / "data"
CLASSES = ["HUNTER", "MAGE", "WARRIOR"]


def load_champion_weights():
  with open(OUT_DIR / "self_play_champion.json", encoding="utf-8") as f:
    loaded = json.load(f)
  return loaded.get("champion_weights") or loaded["weights"]


def best_evolved_deck(player_class):
  with open(OUT_DIR / f"evolve_offarchetype_{player_class.lower()}_generation14.json", encoding="utf-8") as f:
    archive = json.load(f)
  elites = [e for e in archive if e["fitness"] is not None]
  best = max(elites, key=lambda e: e["fitness"])
  return best["sample"][1], best["fitness"]


def nearest_real_seed(deck, seeds):
  deck_counts = Counter(deck)
  best_overlap, nearest = -1, None
  for seed in seeds:
    shared = sum((deck_counts & Counter(seed)).values())
    if shared > best_overlap:
      best_overlap, nearest = shared, seed
  return nearest, best_overlap


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--cores", type=int, default=1)
  parser.add_argument("--games", type=int, default=None,
                       help="fixed games/matchup (min_games=max_games=N, no early stopping). "
                            "Omit to use the exploratory early-stopping defaults.")
  parser.add_argument("--out", default=str(OUT_DIR / "evolved_vs_pool.csv"))
  args = parser.parse_args()

  eval_weights = load_champion_weights()
  pool = load_offarchetype_decks(sort_by_games=True)

  #build the test set: {evolved, nearest real ancestor} per class, deduped
  #(Warrior's evolved deck was found to be a verbatim match to its ancestor -
  #keep both entries anyway, as a same-deck sanity check on simulation noise).
  test_decks = []
  for player_class in CLASSES:
    evolved, evolved_fitness = best_evolved_deck(player_class)
    seeds = [d["card_list"].split("|") for d in pool if d["class"] == player_class][:20]
    ancestor, overlap = nearest_real_seed(evolved, seeds)
    test_decks.append({"label": f"{player_class}_evolved", "class": player_class, "deck": evolved,
                        "gauntlet_fitness": evolved_fitness, "overlap_with_ancestor": overlap})
    test_decks.append({"label": f"{player_class}_ancestor", "class": player_class, "deck": ancestor,
                        "gauntlet_fitness": None, "overlap_with_ancestor": 30})

  print(f"{len(test_decks)} test decks (evolved + nearest ancestor per class) vs {len(pool)}-deck real pool")

  #each test deck plays the FULL real pool of its opponents' own class-agnostic
  #field (the same 82-deck pool used throughout, all classes) - not just same
  #class - matching how the original off-archetype tournament measured decks.
  if args.games:
    work_items = [
      (t["deck"], t["class"], opp["card_list"].split("|"), opp["class"], eval_weights, args.games, args.games)
      for t in test_decks for opp in pool
    ]
  else:
    work_items = [
      (t["deck"], t["class"], opp["card_list"].split("|"), opp["class"], eval_weights)
      for t in test_decks for opp in pool
    ]
  print(f"{len(work_items)} matchup pairs" + (f", fixed {args.games} games/matchup" if args.games else ""))

  run_matchups = run_matchups_ssh if args.backend == "ssh" else run_matchups_local
  results = run_matchups(work_items, args.cores)

  n = len(pool)
  rows = []
  for i, t in enumerate(test_decks):
    matchup_results = results[i * n: (i + 1) * n]
    win_rates = [r[0] for r in matchup_results]
    games = sum(r[3] for r in matchup_results)
    rows.append({"label": t["label"], "class": t["class"], "pool_win_rate_pct": round(mean(win_rates) * 100, 1),
                 "gauntlet_fitness": t["gauntlet_fitness"], "overlap_with_ancestor": t["overlap_with_ancestor"],
                 "games": games})
    print(f"[{t['label']}] win rate vs 82-deck pool: {mean(win_rates)*100:.1f}%")

  out_path = Path(args.out)
  out_path.parent.mkdir(parents=True, exist_ok=True)
  with out_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["label", "class", "pool_win_rate_pct", "gauntlet_fitness", "overlap_with_ancestor", "games"])
    writer.writeheader()
    writer.writerows(rows)
  print(f"\nwrote {out_path}")


if __name__ == "__main__":
  main()
