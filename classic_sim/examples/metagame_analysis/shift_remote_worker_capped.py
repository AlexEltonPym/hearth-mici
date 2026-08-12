"""shift_remote_worker.py with a core cap, so several evolution drivers can
share one host without each grabbing all 24 cores (joblib n_jobs=-1). The cap
comes from the SHIFT_WORKER_JOBS environment variable, which
evolve_metagame_shift.py's --remote-cores sets in the ssh command line.
Same dill-over-stdin protocol; the original worker is left untouched.
"""
import os
import sys

sys.path.append('../../src')
sys.path.append('../validation')
sys.path.append('../map_elites')
sys.path.append('.')

import dill
from joblib import Parallel, delayed

from evolve_metagame_shift import _run_one

if __name__ == "__main__":
  n_jobs = int(os.environ.get("SHIFT_WORKER_JOBS", "-1"))
  print(f"Starting capped shift remote worker (n_jobs={n_jobs})...")
  with Parallel(n_jobs=n_jobs) as parallel:
    work_items = dill.load(sys.stdin.buffer)
    print(f"Received {len(work_items)} work items...")
    results = parallel(delayed(_run_one)(item) for item in work_items)
    print(">>>" + str(results))
