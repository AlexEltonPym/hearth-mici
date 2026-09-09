#!/bin/bash
# Nine-class paper-grade evolution reruns on hearth-rs: blind protocol,
# era-matched blind champions, nine-class blind probe bias (bias-strength
# 10, carried over from the three-class sweep), 25 gens, population 20.
# Gauntlet is 3 real/elite decks x 9 classes = 27 opponents; --fixed-games 8
# keeps 27 x 8 = 216 games per deck evaluation, the same per-deck noise as
# the three-class runs (9 x 24). Usage: paper_sweep9.sh <era> <seeds...>
cd ~/classic_sim/examples/metagame_analysis
source ~/.profile
pyenv activate venv
export HEARTH_BLIND=1
era=$1; shift
case ${era} in
  naxx_launch)  bias=data/probe9_naxx_blind.csv;          net=/home/alex/hearth-rs/tests/data/az3_naxx_blind.json ;;
  buzzard_nerf) bias=data/probe9_combined_nerf_blind.csv; net=/home/alex/hearth-rs/tests/data/az3_postnerf_blind.json ;;
  *) echo "usage: paper_sweep9.sh naxx_launch|buzzard_nerf SEED..."; exit 1 ;;
esac
run () {
  seed=$1; out=data/paper9_${era}_s${seed}
  if [ -f ${out}_population_adoption.csv ]; then echo "SKIP ${out}"; return 0; fi
  for attempt in 1 2 3 4 5 6; do
    echo "=== ${out} attempt ${attempt} $(date -Is) ==="
    python evolve_metagame_shift.py --era ${era} --backend hearthrs \
      --agent-spec "az3:200@${net}" --generations 25 --population 20 \
      --fixed-games 8 --seed ${seed} --mutation-bias ${bias} \
      --bias-strength 10 --out ${out} --resume && return 0
    echo "--- ${out} attempt ${attempt} failed, retrying in 120s ---"; sleep 120
  done
  echo "!!! ${out} FAILED after 6 attempts"; return 1
}
for seed in "$@"; do run ${seed}; done
echo "=== paper9 ${era} [$*] complete $(date -Is) ==="
