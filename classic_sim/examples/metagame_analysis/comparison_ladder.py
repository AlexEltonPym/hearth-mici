"""S5 grand comparison (M6): does the Tier-2 determinized-reply stage add
value on top of Tier-1 beam search, and how much does the hand-knowledge
model matter (the in-house Dockhorn gap)?

Configs (naxx world, naxx fine-tuned net as evaluator, linear champion as
the cheap reply-greedy):
  1. beam+reply(decklist) vs plain beam - marginal value of Tier 2
  2. beam+reply(decklist) vs beam+reply(class_prior) - the Dockhorn gap
  3. beam+reply(decklist) vs greedy(net) - the full stack vs its base

Usage (from classic_sim/examples/metagame_analysis):
  python comparison_ladder.py --backend ssh --cores 24 --seed 777 --out data/value_net_naxx/comparison_seed777.json
"""
import sys, csv, argparse, json
from pathlib import Path
from random import Random
from statistics import mean

sys.path.append('../../src')
import neural_eval as ne
from train_value_net import (dispatch, load_seeds, load_champion_weights, sample_pair,
                              build_ladder_items)

ADOPTION_CSV = Path("../validation/data/naxx_adoption_naxx_prenerf.csv")


def load_priors():
  #merged across classes (max share): class legality is enforced by the
  #opponent's own pool inside sample_class_prior_hand
  priors = {}
  with ADOPTION_CSV.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
      share = max(float(row["hunter_share"]), float(row["mage_share"]), float(row["warrior_share"]))
      priors[row["card"]] = share
  return priors


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--net", default="data/value_net_naxx/value_net_champion.npz")
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--cores", type=int, default=4)
  parser.add_argument("--pairs", type=int, default=24)
  parser.add_argument("--games", type=int, default=24)
  parser.add_argument("--beam-width", type=int, default=3)
  parser.add_argument("--depth", type=int, default=3)
  parser.add_argument("--reply-samples", type=int, default=3)
  parser.add_argument("--world", default="naxx")
  parser.add_argument("--seed", type=int, default=777)
  parser.add_argument("--out", default="data/value_net_naxx/comparison_ladder.json")
  args = parser.parse_args()

  net = ne.load_weights(args.net)
  champion = load_champion_weights()
  priors = load_priors()
  seeds = load_seeds()
  pairs = [sample_pair(seeds, Random(args.seed)) for _ in range(args.pairs)]

  beam_plain = ("beam", (net, args.beam_width, args.depth))
  beam_decklist = ("beam", (net, args.beam_width, args.depth, args.reply_samples,
                             "decklist", champion, None))
  beam_prior = ("beam", (net, args.beam_width, args.depth, args.reply_samples,
                          "class_prior", champion, priors))
  matches = {
    "reply_decklist_vs_beam_plain": (beam_decklist, beam_plain),
    "reply_decklist_vs_reply_classprior": (beam_decklist, beam_prior),
    "reply_decklist_vs_greedy_net": (beam_decklist, ("net", net)),
  }
  results = {}
  for index, (name, (spec_a, spec_b)) in enumerate(matches.items()):
    items = build_ladder_items(pairs, 30000 + index * 1000, spec_a, spec_b, args.world, args.games)
    summaries, _ = dispatch(items, f"cmpladder_{name}_{args.seed}", args.backend, args.cores)
    results[name] = mean(summaries)
    print(f"{name}: {results[name]:.3f} ({len(items) * args.games} games)", flush=True)

  with open(args.out, "w", encoding="utf-8") as f:
    json.dump({"results": results, "pairs": args.pairs, "games": args.games,
               "beam_width": args.beam_width, "depth": args.depth,
               "reply_samples": args.reply_samples, "net": args.net,
               "seed": args.seed}, f, indent=2)
  print(f"wrote {args.out}")


if __name__ == "__main__":
  main()
