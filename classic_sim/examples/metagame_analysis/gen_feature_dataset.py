"""Generate the heuristic-feature usefulness dataset: sampled decision
states (26 current + candidate features, heuristic_features.py) with Monte
Carlo outcome targets, from mixed-agent games in the naxx world.

Agent mixing (per pair, cycled): linear-champion mirror, naxx-net mirror,
net-vs-linear - plus epsilon-random injections in every game - so the state
distribution isn't tied to any single policy's play style.

Usage (from classic_sim/examples/metagame_analysis):
  python gen_feature_dataset.py --backend ssh --cores 24 --pairs 300 --games-per-pair 40
"""
import sys, argparse
from pathlib import Path
from random import Random

sys.path.append('../../src')
import numpy as np

import neural_eval as ne
from train_value_net import dispatch, load_seeds, load_champion_weights, sample_pair

OUT_PATH = Path("data/feature_study/feature_dataset.npz")


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--cores", type=int, default=4)
  parser.add_argument("--pairs", type=int, default=300)
  parser.add_argument("--games-per-pair", type=int, default=40)
  parser.add_argument("--sample-rate", type=float, default=0.15)
  parser.add_argument("--epsilon", type=float, default=0.15)
  parser.add_argument("--world", default="naxx")
  parser.add_argument("--net", default="data/value_net_naxx/value_net_champion.npz")
  parser.add_argument("--seed", type=int, default=0)
  parser.add_argument("--out", default=str(OUT_PATH))
  args = parser.parse_args()

  champion = load_champion_weights()
  net = ne.load_weights(args.net)
  seeds = load_seeds()
  rng = Random(args.seed)

  mixes = [
    (("linear", champion), ("linear", champion)),
    (("net", net), ("net", net)),
    (("net", net), ("linear", champion)),
  ]
  items = []
  for i in range(args.pairs):
    deck_a, class_a, deck_b, class_b = sample_pair(seeds, rng)
    spec_a, spec_b = mixes[i % len(mixes)]
    items.append(("features", deck_a, class_a, deck_b, class_b, spec_a, spec_b,
                  args.world, args.games_per_pair, args.sample_rate, args.epsilon,
                  args.seed * 100003 + i))

  summaries, shards = dispatch(items, "feature_dataset", args.backend, args.cores)
  games = sum(s["games"] for s in summaries)
  n_samples = sum(s["n_samples"] for s in summaries)
  print(f"{games} games, {n_samples} samples across {len(shards)} shards")

  #merge shards into the single dataset file the analysis script reads
  merged = {"features": [], "target": []}
  for shard in shards:
    with np.load(shard) as data:
      merged["features"].append(data["features"])
      merged["target"].append(data["target"])
  out = Path(args.out)
  out.parent.mkdir(parents=True, exist_ok=True)
  np.savez_compressed(out, features=np.concatenate(merged["features"]),
                      target=np.concatenate(merged["target"]))
  print(f"wrote {out}")


if __name__ == "__main__":
  main()
