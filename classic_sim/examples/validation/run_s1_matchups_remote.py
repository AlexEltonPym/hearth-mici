"""Parameterised, distributable version of run_s1_matchups.py - lets the same
20 real-decklist matchup pairs be split across multiple machines and re-run
with a stronger (and much slower) piloting agent, to test whether S1's weak
Spearman correlation (0.366, GreedyActionSmart, see README) is a card/engine
fidelity problem or an agent-skill confound.

Usage (from classic_sim/examples/validation, PYTHONPATH=../../src):
  python run_s1_matchups_remote.py --agent mcts --games 30 --shard 0/2 --cores -1 --out data/s1_mcts_shard0.csv
  python run_s1_matchups_remote.py --agent mcts --games 30 --shard 1/2 --cores -1 --out data/s1_mcts_shard1.csv

--shard i/n runs only pairs where index % n == i, so running shard 0/2 and
1/2 on two machines covers every pair exactly once. --cores is passed
straight through to GameManager.simulate's parralel argument (-1 = all
cores via joblib).
"""
import sys, csv, argparse
from itertools import permutations
from pathlib import Path

sys.path.append('../../src')
from game_manager import GameManager
from strategy import GreedyActionSmart, MCTS
from zones import Deck
from enums import Classes, CardSets

from run_s1_matchups import (SIGNATURES, MIN_SCORE, ARCHETYPE_CLASS, CLASS_ENUM, CARDSET_ENUM,
                              load_decks, pick_representatives, load_real_matrix, spearman,
                              DECKLISTS, REAL_MATRIX)

HERE = Path(__file__).parent


def simulate_matchup(deck_a_list, class_a, deck_b_list, class_b, agent_factory, games, cores):
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CARDSET_ENUM[class_a]])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CARDSET_ENUM[class_b]])
  game_manager.create_player(CLASS_ENUM[class_a], Deck.generate_from_decklist(deck_a_list), agent_factory())
  game_manager.create_enemy(CLASS_ENUM[class_b], Deck.generate_from_decklist(deck_b_list), agent_factory())
  result = game_manager.simulate(games, silent=True, parralel=cores, rng=True)
  return result[0] if result else None


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--agent", choices=["greedy", "mcts"], default="greedy")
  parser.add_argument("--games", type=int, default=30)
  parser.add_argument("--shard", default="0/1", help="i/n - run only pairs where index%%n==i")
  parser.add_argument("--cores", type=int, default=1, help="passed to GameManager.simulate's parralel arg, -1 = all cores")
  parser.add_argument("--out", default=None)
  args = parser.parse_args()

  shard_index, shard_count = (int(x) for x in args.shard.split("/"))
  agent_factory = (lambda: MCTS(iterations=150, guided=True)) if args.agent == "mcts" else GreedyActionSmart
  out_path = Path(args.out) if args.out else HERE / f"data/s1_{args.agent}_shard{shard_index}.csv"

  decks = load_decks()
  reps, scores = pick_representatives(decks)
  real_matrix = load_real_matrix()

  all_pairs = [(hero, opponent) for hero, opponent in permutations(reps.keys(), 2) if (hero, opponent) in real_matrix]
  my_pairs = [pair for i, pair in enumerate(all_pairs) if i % shard_count == shard_index]
  print(f"shard {shard_index}/{shard_count}: {len(my_pairs)}/{len(all_pairs)} pairs, agent={args.agent}, games={args.games}, cores={args.cores}")

  rows = []
  for hero, opponent in my_pairs:
    sim_winrate = simulate_matchup(reps[hero], ARCHETYPE_CLASS[hero], reps[opponent], ARCHETYPE_CLASS[opponent],
                                    agent_factory, args.games, args.cores)
    if sim_winrate is None:
      continue
    real_pct, real_ordinal = real_matrix[(hero, opponent)]
    rows.append({"hero": hero, "opponent": opponent, "sim_winrate_pct": round(sim_winrate * 100, 1),
                 "real_winrate_band_pct": real_pct, "real_ordinal": real_ordinal})
    print(f"[{hero} vs {opponent}] sim={sim_winrate*100:.1f}% real_band={real_pct:.1f}% (ordinal {real_ordinal})", flush=True)

  out_path.parent.mkdir(parents=True, exist_ok=True)
  with out_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["hero", "opponent", "sim_winrate_pct", "real_winrate_band_pct", "real_ordinal"])
    writer.writeheader()
    writer.writerows(rows)
  print(f"wrote {out_path}")


if __name__ == "__main__":
  main()
