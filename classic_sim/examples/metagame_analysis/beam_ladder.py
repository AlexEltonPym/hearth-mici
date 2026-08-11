"""Turn-plan beam search ladder: the decisive test of Tier 1 (see the
research report and examples/validation/README.md S4). Vanilla-UCT MCTS
already lost to 1-ply greedy at every iteration budget tested, because a
Hearthstone turn is a sequence, not a single decision - this searches whole
turn-continuations instead (strategy.BeamSearch) and asks the same question
again with the right unit of search.

Usage (from classic_sim/examples/metagame_analysis):
  python beam_ladder.py --net data/value_net_naxx/value_net_champion.npz --backend ssh
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
  parser.add_argument("--net", default="data/value_net_naxx/value_net_champion.npz")
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--cores", type=int, default=4)
  parser.add_argument("--pairs", type=int, default=24)
  parser.add_argument("--games", type=int, default=24)
  parser.add_argument("--beam-width", type=int, default=3)
  parser.add_argument("--depth", type=int, default=3)
  parser.add_argument("--world", default="naxx")
  parser.add_argument("--seed", type=int, default=777)  #same fixed pairs as training ladders
  args = parser.parse_args()

  net = ne.load_weights(args.net)
  champion = load_champion_weights()
  #the linear leaf evaluator takes 26 weights - champion[1:] strips the
  #turn_passed weight (evaluate_position has no turn_passed feature; passing
  #all 27 misaligns every feature - see mcts_ladder.py for the same trap)
  linear_leaf = champion[1:]
  seeds = load_seeds()
  pairs = [sample_pair(seeds, Random(args.seed)) for _ in range(args.pairs)]

  beam = ("beam", (net, args.beam_width, args.depth))
  beam_linear = ("beam", (linear_leaf, args.beam_width, args.depth))
  matches = {
    #the critical test: does search add value on top of the SAME net's
    #plain greedy, now that vanilla MCTS is ruled out at this task?
    "beam_net_vs_greedy_net": (beam, ("net", net)),
    "beam_net_vs_greedy_linear": (beam, ("linear", champion)),
    #does beam help even the older linear evaluator?
    "beam_linear_vs_greedy_linear": (beam_linear, ("linear", champion)),
  }
  results = {}
  for index, (name, (spec_a, spec_b)) in enumerate(matches.items()):
    items = build_ladder_items(pairs, 20000 + index * 1000, spec_a, spec_b, args.world, args.games)
    summaries, _ = dispatch(items, f"beamladder_{name}", args.backend, args.cores)
    results[name] = mean(summaries)
    print(f"{name}: {results[name]:.3f} ({len(items) * args.games} games)", flush=True)

  with open("data/value_net_naxx/beam_ladder.json", "w", encoding="utf-8") as f:
    json.dump({"results": results, "pairs": args.pairs, "games": args.games,
               "beam_width": args.beam_width, "depth": args.depth, "net": args.net}, f, indent=2)
  print("wrote data/value_net_naxx/beam_ladder.json")


if __name__ == "__main__":
  main()
