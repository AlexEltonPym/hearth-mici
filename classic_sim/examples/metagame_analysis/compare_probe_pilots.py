"""Does a stronger PILOT fix the marginal-value probe's blind spots?

compare_finetuned_probe.py asks the same question across EVALUATORS (linear
vs value net); this asks it across AGENTS - 1-ply greedy vs turn-plan beam
search over the same net - and adds the replication control the earlier
comparison lacked (the same neural condition rerun, so a probe value's
run-to-run noise can be told apart from a real move).

Usage (from classic_sim/examples/metagame_analysis):
  python compare_probe_pilots.py
  python compare_probe_pilots.py --probe name=path.csv --probe other=path2.csv
"""
import csv, argparse, math
from pathlib import Path
from statistics import mean, pstdev, stdev

from scipy.stats import spearmanr

CLASSES = ["HUNTER", "MAGE", "WARRIOR"]
ADOPTION = "../validation/data/naxx_adoption_naxx_prenerf.csv"

DEFAULT_PROBES = [
  ("linear (baseline)", "data/probe_naxx_launch.csv"),
  ("net gen4 unseen", "data/probe_naxx_launch_neural.csv"),
  ("net naxx (committed)", "data/probe_naxx_launch_neural_finetuned.csv"),
  ("A: net naxx (rerun)", "data/probe_naxx_launch_netA.csv"),
  ("B: beam(net) 3x3", "data/probe_naxx_launch_beamnet.csv"),
]

#the two documented misses, plus the cards the report asks for
KEY_CARDS = [("WARRIOR", "Death's Bite"), ("MAGE", "Duplicate"),
             ("HUNTER", "Sludge Belcher"), ("HUNTER", "Mad Scientist"),
             ("HUNTER", "Webspinner"), ("HUNTER", "Haunted Creeper")]


def load_probe(path):
  rows = {}
  with open(path, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
      rows[(r["class"], r["card"])] = float(r["mean_delta_wr"])
  return rows


def load_host_deltas(path):
  """Per-card list of the 5 host deltas - their spread over hosts (each already
  an average of 9 opponents x 60 games) is the honest per-card error bar."""
  rows = {}
  with open(path, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
      rows[(r["class"], r["card"])] = [float(d) for d in r["host_deltas"].split("|")]
  return rows


def standard_error(deltas):
  return stdev(deltas) / math.sqrt(len(deltas)) if len(deltas) > 1 else float("nan")


def rho_ci(rho, n):
  """Fisher-z 95% interval - n=22 cards makes these intervals wide, which is
  the point: rank correlations this small are not separable by eye."""
  if abs(rho) >= 1 or n < 4:
    return float("nan"), float("nan")
  z, se = math.atanh(rho), 1 / math.sqrt(n - 3)
  return math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)


def load_adoption(path):
  rows = {}
  with open(path, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
      rows[r["card"]] = {c: float(r[f"{c.lower()}_share"]) for c in CLASSES}
  return rows


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--probe", action="append", default=None,
                       help="name=path.csv (repeatable); default = the five standard probes")
  parser.add_argument("--replication", nargs=2, default=["net naxx (committed)", "A: net naxx (rerun)"],
                       help="two probe names to difference as a noise estimate")
  args = parser.parse_args()

  specs = [tuple(p.split("=", 1)) for p in args.probe] if args.probe else DEFAULT_PROBES
  adoption = load_adoption(ADOPTION)
  probes, host_deltas = {}, {}
  for name, path in specs:
    if Path(path).exists():
      probes[name] = load_probe(path)
      host_deltas[name] = load_host_deltas(path)
    else:
      print(f"(skipping {name}: {path} not present)")

  print(f"\nSpearman rho (95% CI), probed mean_delta_wr vs real naxx_prenerf adoption, 22 cards/class")
  print(f"{'probe':<24}" + "".join(f"{c:>22}" for c in CLASSES) + f"{'mean':>8}")
  for name, data in probes.items():
    cors, cells = [], []
    for cls in CLASSES:
      cards = [c for (k, c) in data if k == cls and c in adoption]
      rho, _ = spearmanr([data[(cls, c)] for c in cards], [adoption[c][cls] for c in cards])
      low, high = rho_ci(rho, len(cards))
      cors.append(rho)
      cells.append(f"{rho:+.3f} ({low:+.2f},{high:+.2f})")
    print(f"{name:<24}" + "".join(f"{cell:>22}" for cell in cells) + f"{mean(cors):>8.3f}")

  print(f"\nKey cards: probed mean_delta_wr in pp, +-1 SE over the 5 host decks")
  print(f"{'card (class)':<26}{'real':>8}" + "".join(f"{n[:17]:>19}" for n in probes))
  for cls, card in KEY_CARDS:
    real = adoption.get(card, {}).get(cls, float("nan"))
    line = f"{card + ' (' + cls[:3] + ')':<26}{real * 100:>7.1f}%"
    for name, data in probes.items():
      v = data.get((cls, card))
      if v is None:
        line += f"{'-':>19}"
      else:
        se = standard_error(host_deltas[name][(cls, card)])
        line += f"{f'{v * 100:+.1f} +-{se * 100:.1f}':>19}"
    print(line)

  #replication control: the same condition run twice differs only by game
  #randomness, so the spread of those differences is the probe's noise floor
  a, b = args.replication
  if a in probes and b in probes:
    keys = sorted(set(probes[a]) & set(probes[b]))
    diffs = [probes[b][k] - probes[a][k] for k in keys]
    worst = max(keys, key=lambda k: abs(probes[b][k] - probes[a][k]))
    print(f"\nReplication noise ({b} minus {a}, n={len(keys)} card-classes):")
    print(f"  mean {mean(diffs) * 100:+.2f}pp  sd {pstdev(diffs) * 100:.2f}pp  "
          f"max |diff| {abs(probes[b][worst] - probes[a][worst]) * 100:.2f}pp ({worst[1]}, {worst[0]})")
    rho, _ = spearmanr([probes[a][k] for k in keys], [probes[b][k] for k in keys])
    print(f"  rank agreement between the two runs: rho {rho:.3f}")


if __name__ == "__main__":
  main()
