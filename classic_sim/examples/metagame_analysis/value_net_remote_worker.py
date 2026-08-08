"""Dill-over-stdin worker for value-net self-play generation and ladder
evaluation. Payload: {"tag": str, "cores": int, "items": [work items]}.

Generate-item samples are far too large for the >>> result line, so they are
written to a local compressed shard (data/value_net_shards/{tag}.npz) that
the driver scps back; the >>> line carries only per-item summaries (aligned
with the item list) and the shard path.
"""
import sys
from pathlib import Path

sys.path.append('../../src')
import dill
import numpy as np
from joblib import Parallel, delayed

from value_net_selfplay import run_item, concatenate_samples

SHARD_DIR = Path(__file__).parent / "data" / "value_net_shards"


def main():
  payload = dill.load(sys.stdin.buffer)
  tag, items = payload["tag"], payload["items"]
  cores = payload.get("cores", -1)
  print(f"Starting value net worker: {len(items)} items on {cores} cores...", flush=True)

  results = Parallel(n_jobs=cores)(delayed(run_item)(item) for item in items)

  shard_path = None
  generate_results = [r for r in results if isinstance(r, dict)]
  samples = concatenate_samples(generate_results)
  if samples is not None:
    SHARD_DIR.mkdir(parents=True, exist_ok=True)
    shard_path = SHARD_DIR / f"{tag}.npz"
    np.savez_compressed(shard_path, **samples)

  summaries = []
  for result in results:
    if isinstance(result, dict):
      summaries.append({"games": result["games"], "wins_a": result["wins_a"],
                        "n_samples": int(len(result["samples"]["target"])) if result["samples"] else 0})
    else:
      summaries.append(float(result))

  print(">>>" + repr({"shard": str(shard_path) if shard_path else None,
                      "summaries": summaries}), flush=True)


if __name__ == "__main__":
  main()
