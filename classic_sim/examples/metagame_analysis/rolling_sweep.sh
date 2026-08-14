#!/bin/bash
# Rerun the rolling shock-trajectory experiment (both modes) under the
# pair-bias 4.0 mutation default, so Fig 1 of the paper uses the same
# operator as the one-shot headline runs. Same config as the original
# rolling runs otherwise (10 gens/period, population 16, 16 fixed games,
# seed 0). rolling_shift.py has no per-generation checkpoint, so the retry
# here restarts a failed mode from scratch - acceptable at ~9h/mode given
# the paper sweep saw zero dispatch failures in 25h.
cd ~/classic_sim/examples/metagame_analysis
source ~/.profile
pyenv activate venv

run_mode () {
  mode=$1; out=data/rolling2_${mode}
  if [ -f ${out}_predicted_p4_postnerf_late.csv ]; then
    echo "SKIP ${out} (already complete)"
    return 0
  fi
  for attempt in 1 2 3; do
    echo "=== ${out} attempt ${attempt} $(date -Is) ==="
    python rolling_shift.py --mode ${mode} --backend ssh --out ${out} && return 0
    echo "--- ${out} attempt ${attempt} failed, retrying in 120s ---"
    sleep 120
  done
  echo "!!! ${out} FAILED after 3 attempts"
  return 1
}

run_mode anchored
run_mode free
echo "=== rolling sweep complete $(date -Is) ==="
