#!/bin/bash
# Nine-class rolling shock-trajectory rerun on hearth-rs: blind protocol,
# era-matched blind champions, nine-class blind probe bias, bias-strength
# 10, 10 gens/period, population 16. Gauntlet 27 decks; --fixed-games 6
# keeps 27 x 6 = 162 games per deck evaluation (three-class: 9 x 16 = 144).
# Usage: paper_rolling9.sh <free|anchored> <seeds...>
cd ~/classic_sim/examples/metagame_analysis
source ~/.profile
pyenv activate venv
export HEARTH_BLIND=1
mode=$1; shift
NAXX=/home/alex/hearth-rs/tests/data/az3_naxx_blind.json
PN=/home/alex/hearth-rs/tests/data/az3_postnerf_blind.json
run () {
  seed=$1; out=data/rolling9_${mode}_s${seed}
  if [ -f ${out}_predicted_p4_postnerf_late.csv ]; then echo "SKIP ${out}"; return 0; fi
  for attempt in 1 2 3 4 5 6; do
    echo "=== ${out} attempt ${attempt} $(date -Is) ==="
    python rolling_shift.py --mode ${mode} --backend hearthrs \
      --agent-naxx "az3:200@${NAXX}" --agent-postnerf "az3:200@${PN}" \
      --bias-naxx data/probe9_naxx_blind.csv \
      --bias-nerf data/probe9_combined_nerf_blind.csv \
      --fixed-games 6 --bias-strength 10 --seed ${seed} --out ${out} --resume && return 0
    echo "--- ${out} attempt ${attempt} failed, retrying in 120s ---"; sleep 120
  done
  echo "!!! ${out} FAILED after 6 attempts"; return 1
}
for seed in "$@"; do run ${seed}; done
echo "=== rolling9 ${mode} [$*] complete $(date -Is) ==="
