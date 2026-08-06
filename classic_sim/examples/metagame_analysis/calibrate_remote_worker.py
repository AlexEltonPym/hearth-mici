"""Remote worker for calibrate_greedy_weights.py's --backend ssh, following
the exact dill-over-stdin protocol remote_simulator.py already established:
receive a batch of work items, run them across all local cores, print the
results as a single ">>>"-prefixed line (parsed back by run_host()).
"""
import sys

sys.path.append('../../src')
sys.path.append('../validation')
sys.path.append('.')

import dill
from joblib import Parallel, delayed

from calibrate_greedy_weights import _run_one

if __name__ == "__main__":
  print("Starting calibration remote worker...")
  with Parallel(n_jobs=-1) as parallel:
    work_items = dill.load(sys.stdin.buffer)
    print(f"Received {len(work_items)} work items...")
    results = parallel(delayed(_run_one)(item) for item in work_items)
    print(">>>" + str(results))
