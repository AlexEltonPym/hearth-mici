#!/bin/bash
# Face-up comparability arm for the paper-grade v2 reruns: identical config
# to paper_sweep_v2.sh naxx_launch (25 gens, pop 20, 24 fixed games,
# bias-strength 10) but perfect-information protocol (no HEARTH_BLIND),
# face-up champion pilot, and face-up probe bias. The blind runs are the
# paper primary; this arm measures how much honest hidden information
# changes evolution-level adoption predictions.
cd ~/classic_sim/examples/metagame_analysis
source ~/.profile
pyenv activate venv
unset HEARTH_BLIND

bias=data/probe_naxx_fx.csv
net=/home/alex/hearth-rs/tests/data/az3_naxx_fx.json

run () {
  seed=$1; out=data/paper2fx_naxx_launch_s${seed}
  if [ -f ${out}_population_adoption.csv ]; then
    echo "SKIP ${out} (already complete)"
    return 0
  fi
  for attempt in 1 2 3 4 5 6 7 8; do
    echo "=== ${out} attempt ${attempt} $(date -Is) ==="
    python evolve_metagame_shift.py --era naxx_launch --backend hearthrs \
      --agent-spec "az3:200@${net}" --generations 25 --population 20 \
      --fixed-games 24 --seed ${seed} --mutation-bias ${bias} \
      --bias-strength 10 --out ${out} --resume && return 0
    echo "--- ${out} attempt ${attempt} failed, retrying in 120s ---"
    sleep 120
  done
  echo "!!! ${out} FAILED after 8 attempts, moving on"
  return 1
}

for seed in 0 1 2; do
  run ${seed}
done
echo "=== paper2fx naxx_launch sweep complete $(date -Is) ==="
