#!/bin/bash
# Paper 1 headline rerun under the new defaults: probe-biased evolution with
# the pair-bias 2-of mutation fix (4.0), 2 eras x 3 seeds, original headline
# config otherwise (25 generations, population 20, 24 fixed games/eval).
# Runs detached on dwail1 as master, fanning matchups to dwail1+dwail2.
# Every run checkpoints per generation; the retry loop passes --resume so a
# VPN drop, crash, or reboot continues instead of restarting. Re-running this
# whole script is also safe: completed runs are skipped by artifact check.
cd ~/classic_sim/examples/metagame_analysis
source ~/.profile
pyenv activate venv

run () {
  era=$1; seed=$2; bias=$3; out=data/paper_${era}_s${seed}
  if [ -f ${out}_population_adoption.csv ]; then
    echo "SKIP ${out} (already complete)"
    return 0
  fi
  for attempt in 1 2 3 4 5 6 7 8; do
    echo "=== ${out} attempt ${attempt} $(date -Is) ==="
    python evolve_metagame_shift.py --era ${era} --backend ssh \
      --hosts dwail1,dwail2 --generations 25 --population 20 \
      --fixed-games 24 --seed ${seed} --mutation-bias ${bias} \
      --out ${out} --resume && return 0
    echo "--- ${out} attempt ${attempt} failed, retrying in 120s ---"
    sleep 120
  done
  echo "!!! ${out} FAILED after 8 attempts, moving on"
  return 1
}

# nerf first (the paper's headline table), then naxx launch
for seed in 0 1 2; do
  run buzzard_nerf ${seed} data/probe_combined_nerf.csv
done
for seed in 0 1 2; do
  run naxx_launch ${seed} data/probe_naxx_launch.csv
done
echo "=== sweep complete $(date -Is) ==="
