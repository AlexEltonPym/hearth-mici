#!/bin/bash
# Paper-grade evolution reruns v2: fixed hearth-rs engine, BLIND protocol,
# blind-probe mutation bias at the sweep-v2 winner (bias-strength 10),
# original headline config otherwise (25 generations, population 20,
# 24 fixed games/eval), 3 seeds per era. One era per host:
#   dwail1: naxx_launch  (pilot az3_naxx_blind, bias probe_naxx_blind.csv)
#   dwail2: buzzard_nerf (pilot az3_postnerf_blind, bias probe_combined_nerf_blind.csv)
# Usage: paper_sweep_v2.sh <era>   -- run on the matching host via nohup.
# Checkpoint/resume-safe: retry loop passes --resume; completed runs skipped.
cd ~/classic_sim/examples/metagame_analysis
source ~/.profile
pyenv activate venv
export HEARTH_BLIND=1

era=$1
case ${era} in
  naxx_launch)
    bias=data/probe_naxx_blind.csv
    net=/home/alex/hearth-rs/tests/data/az3_naxx_blind.json ;;
  buzzard_nerf)
    bias=data/probe_combined_nerf_blind.csv
    net=/home/alex/hearth-rs/tests/data/az3_postnerf_blind.json ;;
  *) echo "usage: paper_sweep_v2.sh naxx_launch|buzzard_nerf"; exit 1 ;;
esac

run () {
  seed=$1; out=data/paper2_${era}_s${seed}
  if [ -f ${out}_population_adoption.csv ]; then
    echo "SKIP ${out} (already complete)"
    return 0
  fi
  for attempt in 1 2 3 4 5 6 7 8; do
    echo "=== ${out} attempt ${attempt} $(date -Is) ==="
    python evolve_metagame_shift.py --era ${era} --backend hearthrs \
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
echo "=== paper2 ${era} sweep complete $(date -Is) ==="
