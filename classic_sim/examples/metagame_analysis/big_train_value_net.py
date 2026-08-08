"""One-shot big training: all accumulated self-play shards, from scratch.

The per-generation loop showed retrains are data-hungry: strength tracked
window size (110k samples -> 0.38, 220k -> 0.45, 335k -> 0.47) and the best
net (gen 4 of run 1, 0.516) sat on a full window. This trains once on EVERY
shard on disk (~1M+ samples, mixed policies - DouZero-style) with a longer
patience, from scratch, as the alternative to per-generation churn.

Usage (from classic_sim/examples/metagame_analysis):
  python big_train_value_net.py [--epochs 30] [--out data/value_net/net_bigtrain.npz]
"""
import sys, argparse
from pathlib import Path

sys.path.append('../../src')
import neural_eval as ne
from train_value_net import train_net, SHARD_DIR

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--epochs", type=int, default=30)
  parser.add_argument("--learning-rate", type=float, default=1e-3)
  parser.add_argument("--seed", type=int, default=0)
  parser.add_argument("--init-net", default=None, help="optional warm start .npz")
  parser.add_argument("--out", default="data/value_net/net_bigtrain.npz")
  args = parser.parse_args()

  shards = sorted(SHARD_DIR.glob("gen*.npz"))
  if not shards:
    raise SystemExit(f"no shards found in {SHARD_DIR}")
  print(f"training on {len(shards)} shards...")
  previous = ne.load_weights(args.init_net) if args.init_net else None
  weights, val_mse, n = train_net(shards, previous, args.epochs, args.learning_rate, args.seed,
                                  batch_size=2048)
  ne.save_weights(weights, args.out)
  print(f"val_mse={val_mse:.4f} n_train={n}; wrote {args.out}")


if __name__ == "__main__":
  main()
