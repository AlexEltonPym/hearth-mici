"""Remote worker for run_offarchetype_tournament.py's --backend ssh, same
dill-over-stdin protocol as calibrate_remote_worker.py / remote_simulator.py.
"""
import sys

sys.path.append('../../src')
sys.path.append('../validation')
sys.path.append('.')

import dill
from joblib import Parallel, delayed

from run_offarchetype_tournament import _run_one

if __name__ == "__main__":
  print("Starting tournament remote worker...")
  with Parallel(n_jobs=-1) as parallel:
    work_items = dill.load(sys.stdin.buffer)
    print(f"Received {len(work_items)} work items...")
    results = parallel(delayed(_run_one)(item) for item in work_items)
    print(">>>" + str(results))
