#!/bin/bash
# Nine-class probe campaign on hearth-rs (blind protocol, era-matched blind
# champions, az3:200). One process per class so a failure costs one class
# and completed classes are skipped on rerun. Field = 3 real decks x 9
# classes = 27; --games 20 keeps 5 hosts x 27 x 20 = 2700 games/side per
# card, the same per-card noise as the three-class probes (5 x 9 x 60).
# Usage: probe9.sh naxx <CLASS...>   |   probe9.sh nerf <CLASS...>
cd ~/classic_sim/examples/metagame_analysis
source ~/.profile
pyenv activate venv
export HEARTH_BLIND=1
kind=$1; shift
case ${kind} in
  naxx) era=naxx_launch; net=/home/alex/hearth-rs/tests/data/az3_naxx_blind.json ;;
  nerf) era=buzzard_nerf; net=/home/alex/hearth-rs/tests/data/az3_postnerf_blind.json ;;
  *) echo "usage: probe9.sh naxx|nerf CLASS..."; exit 1 ;;
esac
for cls in "$@"; do
  out=data/probe9_${kind}_blind_${cls}.csv
  if [ -s ${out} ]; then echo "SKIP ${out}"; continue; fi
  for attempt in 1 2 3; do
    echo "=== ${out} attempt ${attempt} $(date -Is) ==="
    python probe_card_values.py --era ${era} --backend hearthrs \
      --agent-spec "az3:200@${net}" --hosts 5 --games 20 --seed 0 \
      --classes ${cls} --out ${out} && break
    echo "--- ${out} attempt ${attempt} failed, retrying in 60s ---"; sleep 60
  done
done
echo "=== probe9 ${kind} [$*] complete $(date -Is) ==="
