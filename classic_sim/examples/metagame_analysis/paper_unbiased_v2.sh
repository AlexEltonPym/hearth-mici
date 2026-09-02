#!/bin/bash
# Unbiased control for the paper-grade v2 naxx_launch runs: identical to
# paper_sweep_v2.sh naxx_launch (blind, az3_naxx_blind, 25 gens, pop 20,
# 24 fixed games) with NO probe bias. Usage: paper_unbiased_v2.sh <seeds...>
cd ~/classic_sim/examples/metagame_analysis
source ~/.profile
pyenv activate venv
export HEARTH_BLIND=1
net=/home/alex/hearth-rs/tests/data/az3_naxx_blind.json
run () {
  seed=$1; out=data/paper2u_naxx_launch_s${seed}
  if [ -f ${out}_population_adoption.csv ]; then
    echo "SKIP ${out} (already complete)"; return 0
  fi
  for attempt in 1 2 3 4 5 6; do
    echo "=== ${out} attempt ${attempt} $(date -Is) ==="
    python evolve_metagame_shift.py --era naxx_launch --backend hearthrs \
      --agent-spec "az3:200@${net}" --generations 25 --population 20 \
      --fixed-games 24 --seed ${seed} --out ${out} --resume && return 0
    echo "--- ${out} attempt ${attempt} failed, retrying in 120s ---"; sleep 120
  done
  echo "!!! ${out} FAILED after 6 attempts"; return 1
}
for seed in "$@"; do run ${seed}; done
echo "=== paper2u sweep complete $(date -Is) ==="
