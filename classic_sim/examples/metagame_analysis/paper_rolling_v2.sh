#!/bin/bash
# Rolling shock-trajectory rerun v2 (the paper's Fig 1) on hearth-rs:
# blind protocol, era-matched blind champions, blind probe bias
# (naxx additions for p1/p2; naxx additions + negated nerf removals for
# p3/p4), bias-strength 10 as selected by the one-shot sweep. Same
# evolution config as the original rolling runs (10 gens/period,
# population 16, 16 fixed games), now at 3 seeds per mode.
# Usage: paper_rolling_v2.sh <free|anchored>
cd ~/classic_sim/examples/metagame_analysis
source ~/.profile
pyenv activate venv
export HEARTH_BLIND=1
mode=$1
NAXX=/home/alex/hearth-rs/tests/data/az3_naxx_blind.json
PN=/home/alex/hearth-rs/tests/data/az3_postnerf_blind.json

run () {
  seed=$1; out=data/rolling3_${mode}_s${seed}
  if [ -f ${out}_predicted_p4_postnerf_late.csv ]; then
    echo "SKIP ${out} (already complete)"; return 0
  fi
  for attempt in 1 2 3 4 5 6; do
    echo "=== ${out} attempt ${attempt} $(date -Is) ==="
    python rolling_shift.py --mode ${mode} --backend hearthrs \
      --agent-naxx "az3:200@${NAXX}" --agent-postnerf "az3:200@${PN}" \
      --bias-naxx data/probe_naxx_blind.csv \
      --bias-nerf data/probe_combined_nerf_blind.csv \
      --bias-strength 10 --seed ${seed} --out ${out} --resume && return 0
    echo "--- ${out} attempt ${attempt} failed, retrying in 120s ---"; sleep 120
  done
  echo "!!! ${out} FAILED after 6 attempts"; return 1
}
for seed in 0 1 2; do run ${seed}; done
echo "=== rolling3 ${mode} sweep complete $(date -Is) ==="
