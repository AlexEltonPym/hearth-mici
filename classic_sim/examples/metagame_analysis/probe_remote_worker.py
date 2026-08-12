"""Remote worker for probe_card_values.py's --backend ssh. Same
dill-over-stdin protocol as shift_remote_worker.py; the only difference is
that work items are run through probe_pilots._run_probe, which widens the
eval_weights slot to accept an agent spec tuple (beam search included).
"""
import sys

sys.path.append('../../src')
sys.path.append('../validation')
sys.path.append('../map_elites')
sys.path.append('.')

import dill
from joblib import Parallel, delayed

from probe_pilots import _run_probe

if __name__ == "__main__":
  print("Starting probe remote worker...")
  with Parallel(n_jobs=-1) as parallel:
    work_items = dill.load(sys.stdin.buffer)
    print(f"Received {len(work_items)} work items...")
    results = parallel(delayed(_run_probe)(item) for item in work_items)
    print(">>>" + str(results))
