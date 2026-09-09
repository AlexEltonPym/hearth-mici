#!/bin/bash
# Nine-class unbiased control (naxx_launch): paper_sweep9 config, no probe bias.
cd ~/classic_sim/examples/metagame_analysis
source ~/.profile
pyenv activate venv
export HEARTH_BLIND=1
net=/home/alex/hearth-rs/tests/data/az3_naxx_blind.json
run () {
  seed=$1; out=data/paper9u_naxx_launch_s${seed}
  if [ -f ${out}_population_adoption.csv ]; then echo "SKIP ${out}"; return 0; fi
  for attempt in 1 2 3 4 5 6; do
    echo "=== ${out} attempt ${attempt} $(date -Is) ==="
    python evolve_metagame_shift.py --era naxx_launch --backend hearthrs \
      --agent-spec "az3:200@${net}" --generations 25 --population 20 \
      --fixed-games 8 --seed ${seed} --out ${out} --resume && return 0
    echo "--- ${out} attempt ${attempt} failed, retrying in 120s ---"; sleep 120
  done
  echo "!!! ${out} FAILED after 6 attempts"; return 1
}
for seed in "$@"; do run ${seed}; done
echo "=== paper9u [$*] complete $(date -Is) ==="
