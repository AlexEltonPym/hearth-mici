"""MCTS-leaf ladder: the decisive test of the value net.

Greedy-level parity (net_gen4 ~52% vs the linear champion) can understate a
better EVALUATOR: 1-ply greedy strength is dominated by the lookahead, while
guided MCTS quality is dominated by the leaf evaluation it searches over.
This ladders guided MCTS with the trained net as leaf eval against guided
MCTS with the linear features (and against the plain linear greedy, for
scale) on the same fixed real-deck matchups used during training evaluation.

Usage (from classic_sim/examples/metagame_analysis):
  python mcts_ladder.py --net data/value_net/value_net_best.npz --backend ssh
"""
import sys, argparse, json
from random import Random
from statistics import mean

sys.path.append('../../src')
import neural_eval as ne
from train_value_net import (dispatch, load_seeds, load_champion_weights, sample_pair,
                              build_ladder_items)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--net", default="data/value_net/value_net_best.npz")
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--cores", type=int, default=4)
  parser.add_argument("--pairs", type=int, default=24)
  parser.add_argument("--games", type=int, default=12)
  parser.add_argument("--iterations", type=int, default=150)
  parser.add_argument("--world", default="pre_naxx")
  parser.add_argument("--seed", type=int, default=777)  #same fixed pairs as training ladders
  args = parser.parse_args()

  net = ne.load_weights(args.net)
  champion = load_champion_weights()
  seeds = load_seeds()
  pairs = [sample_pair(seeds, Random(args.seed)) for _ in range(args.pairs)]

  #the linear leaf evaluator takes 26 weights - champion[1:] strips the
  #turn_passed weight (evaluate_position has no turn_passed feature; passing
  #all 27 misaligns every feature and cripples the search)
  linear_leaf = champion[1:]
  matches = {
    #net as PURE leaf eval (no rollout, AlphaZero-style) - the intended mode
    "mcts_net0_vs_mcts_linear": (("mcts", (net, args.iterations, 0)),
                                  ("mcts", (linear_leaf, args.iterations, 6))),
    "mcts_net0_vs_greedy_linear": (("mcts", (net, args.iterations, 0)), ("linear", champion)),
    #net leaf after 6 random rollout turns (OOD for the net - expected worse)
    "mcts_net6_vs_greedy_linear": (("mcts", (net, args.iterations, 6)), ("linear", champion)),
    #sanity anchor: must reproduce the ~0.95 benchmark result
    "mcts_linear_vs_greedy_linear": (("mcts", (linear_leaf, args.iterations, 6)), ("linear", champion)),
  }
  results = {}
  for index, (name, (spec_a, spec_b)) in enumerate(matches.items()):
    items = build_ladder_items(pairs, 10000 + index * 1000, spec_a, spec_b, args.world, args.games)
    summaries, _ = dispatch(items, f"mctsladder_{name}", args.backend, args.cores)
    results[name] = mean(summaries)
    print(f"{name}: {results[name]:.3f} ({len(items) * args.games} games)", flush=True)

  with open("data/value_net/mcts_ladder.json", "w", encoding="utf-8") as f:
    json.dump({"results": results, "pairs": args.pairs, "games": args.games,
               "iterations": args.iterations, "net": args.net}, f, indent=2)
  print("wrote data/value_net/mcts_ladder.json")


if __name__ == "__main__":
  main()
