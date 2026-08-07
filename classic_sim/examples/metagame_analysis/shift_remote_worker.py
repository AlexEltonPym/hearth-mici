"""Remote worker for evolve_metagame_shift.py's --backend ssh, same
dill-over-stdin protocol as the other *_remote_worker.py scripts. Separate
worker because the work-item shape carries an era (pool sets + patches).
"""
import sys

sys.path.append('../../src')
sys.path.append('../validation')
sys.path.append('../map_elites')
sys.path.append('.')

import dill
from joblib import Parallel, delayed

from evolve_metagame_shift import _run_one

if __name__ == "__main__":
  print("Starting shift remote worker...")
  with Parallel(n_jobs=-1) as parallel:
    work_items = dill.load(sys.stdin.buffer)
    print(f"Received {len(work_items)} work items...")
    results = parallel(delayed(_run_one)(item) for item in work_items)
    print(">>>" + str(results))
