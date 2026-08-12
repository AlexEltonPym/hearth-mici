"""Adoption readouts: how to turn a MAP-Elites archive into a population-level
card-adoption share, and which readout reproduces REAL adoption LEVELS.

Motivation. `evolve_metagame_shift.adoption_shares()` reads adoption off
`archive.get_elites(unique_only=True)` - by construction the fitness-ARGMAX
deck of every occupied niche. Real players are a DISTRIBUTION over deck
quality, so the argmax readout over-converges: it puts a good card in 100% of
decks where the real ladder ran it in 73-79%. Ranking is unaffected by this
(it is a monotone squash), levels are badly affected, and levels are what the
S3 write-up currently has to apologise for.

This module is PURE RE-ANALYSIS of the per-generation archives that
`evolve_metagame_shift.py` already saved (`data/<prefix>_<class>_generationN.json`).
It never re-runs the simulator and never writes into anything another script owns.

Readout families implemented
  a  final_unique          current behaviour (unique elites, uniform weight)
  b  final_bins            every occupied bin, duplicates included (a deck that
                           owns k niches counts k times)
  c  final_softmax[T]      final archive, deck weight ~ exp(fitness/T).
                           T->0 = single best deck, T->inf = uniform (= a on
                           unique decks). Bounded-rationality deck choice.
  d  pooled_lastK          union of the unique decks in the last K generation
                           snapshots (retrospective stand-in for "retain a
                           larger elite pool"; num_buckets cannot be changed
                           after the fact, but coarsen_N below tests the other
                           direction)
     coarsen_N             merge NxN blocks of bins keeping the block's fittest
                           deck - i.e. what a num_buckets/N archive would have
                           produced. Tests the buckets axis downward.
  e1 pooled_softmax[T]     softmax over every deck the run ever archived: the
                           full bounded-rationality readout (this is the one
                           the report recommends)
  e2 gen_mean              mean of the per-generation unique-elite shares
  f  inertia[alpha]        alpha*final_unique + (1-alpha)*real pre-shock shares.
                           NOT a model readout - the trivial shrink-toward-the-
                           no-change-baseline competitor, included so the real
                           readouts have to beat it.

Metrics (per class, vs the real target window)
  levels MAE       mean |predicted - real| over the scored card set
  over-pred rate   share of scored cards with predicted >= 0.95 while real < 0.90
  movers Spearman  rank correlation on cards whose REAL adoption moved >= 5pp
                   between the baseline and target windows
  direction hits   sign(pred - baseline) == sign(real - baseline) on those movers

Usage (from classic_sim/examples/metagame_analysis):
  python adoption_readout.py                      # both eras, full table
  python adoption_readout.py --era buzzard_nerf
  python adoption_readout.py --csv data/readout_comparison.csv
"""
import sys, csv, json, argparse, math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

sys.path.append('../../src')
sys.path.append('../map_elites')

from scipy.stats import spearmanr

from enums import CardSets
from card_sets import build_pool

#duplicated from evolve_metagame_shift.py rather than imported: that module is
#owned by another concurrent task and importing it couples this re-analysis to
#its mid-edit state. These two definitions are the only things needed here.
CLASSES = ["HUNTER", "MAGE", "WARRIOR"]
ERA_SETS = {
  "HUNTER": [CardSets.CLASSIC_NEUTRAL, CardSets.NAXX_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.NAXX_HUNTER],
  "MAGE": [CardSets.CLASSIC_NEUTRAL, CardSets.NAXX_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.NAXX_MAGE],
  "WARRIOR": [CardSets.CLASSIC_NEUTRAL, CardSets.NAXX_NEUTRAL, CardSets.CLASSIC_WARRIOR, CardSets.NAXX_WARRIOR],
}


def era_class_pool(player_class):
  return [card.name for card in build_pool(ERA_SETS[player_class], None)]

HERE = Path(__file__).parent
DATA = HERE / "data"
GT_DIR = HERE / ".." / "validation" / "data"

#era -> saved archive prefix + which real windows bracket it
ERAS = {
  "naxx_launch": {"prefix": "shift_naxx_biased", "baseline": "pre_naxx", "target": "naxx_prenerf"},
  "buzzard_nerf": {"prefix": "shift_nerf_biased", "baseline": "naxx_prenerf", "target": "post_nerf"},
}
MIN_SHARE = 0.02          #same scored-card gate as evaluate_shift_prediction.py
MOVER_THRESHOLD = 0.05
OVERPRED_HI, OVERPRED_REAL = 0.95, 0.90
TEMPERATURES = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
POOL_KS = [1, 3, 5, 10, 25]
COARSEN = [3, 5]
ALPHAS = [0.3, 0.5, 0.7]
HEADLINE_CARD, HEADLINE_CLASS = "Starving Buzzard", "HUNTER"


# ---------------------------------------------------------------- loading

def load_snapshots(prefix, player_class):
  """[(generation, [(bin_x, bin_y, fitness, deck), ...]), ...] for every saved
  generation of one class. The archive is cumulative, so snapshot N holds the
  bin champions as of generation N - pooling snapshots recovers decks that were
  later overwritten, which is exactly the sub-argmax mass the readouts need."""
  snapshots = []
  generation = 0
  while True:
    path = DATA / f"{prefix}_{player_class.lower()}_generation{generation}.json"
    if not path.exists():
      break
    with path.open(encoding="utf-8") as f:
      bins = json.load(f)
    occupied = [(b["x_index"], b["y_index"], b["fitness"], tuple(b["sample"][1]))
                for b in bins if b["fitness"] is not None]
    snapshots.append((generation, occupied))
    generation += 1
  return snapshots


def load_real(window):
  path = GT_DIR / f"naxx_adoption_{window}.csv"
  shares = {c: {} for c in CLASSES}
  with path.open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
      for player_class in CLASSES:
        shares[player_class][row["card"]] = float(row[f"{player_class.lower()}_share"])
  return shares


# ---------------------------------------------------------------- readouts

def shares_from_weighted(decks_weights):
  """decks_weights: [(deck_tuple, weight)] -> {card: weighted inclusion share}."""
  total = sum(w for _, w in decks_weights)
  if total <= 0:
    return {}
  inclusion = Counter()
  for deck, weight in decks_weights:
    for card in set(deck):
      inclusion[card] += weight
  return {card: mass / total for card, mass in inclusion.items()}


def dedup(occupied):
  """unique decks, each keeping its best fitness across the niches it owns"""
  best = {}
  for _, _, fitness, deck in occupied:
    if deck not in best or fitness > best[deck]:
      best[deck] = fitness
  return list(best.items())


def softmax_weights(deck_fitness, temperature):
  fits = [f for _, f in deck_fitness]
  top = max(fits)
  return [(deck, math.exp((f - top) / temperature)) for deck, f in deck_fitness]


def coarsen(occupied, factor):
  """what this run's archive would look like at num_buckets/factor: keep the
  fittest deck of every factor x factor block of niches"""
  best = {}
  for x, y, fitness, deck in occupied:
    key = (x // factor, y // factor)
    if key not in best or fitness > best[key][0]:
      best[key] = (fitness, deck)
  return [(0, 0, f, d) for f, d in best.values()]


def quantile_match(prediction, reference, pool):
  """Monotone recalibration: keep the prediction's ORDER over the card pool, but
  give it the reference window's SHARE DISTRIBUTION. The shape of a real
  adoption distribution (a handful of staples near 1, a long tail near 0) is a
  stable property of the ladder that pre-shock data already measures, so this
  imports no target-window information. Spearman and top-N are invariant."""
  cards = sorted(pool)
  values = sorted((reference.get(c, 0.0) for c in cards), reverse=True)
  order = sorted(cards, key=lambda c: -prediction.get(c, 0.0))
  matched, i = {}, 0
  while i < len(order):
    j = i
    while j + 1 < len(order) and prediction.get(order[j + 1], 0.0) == prediction.get(order[i], 0.0):
      j += 1
    tied_value = mean(values[i:j + 1])          #ties share the block's mean level
    for k in range(i, j + 1):
      matched[order[k]] = tied_value
    i = j + 1
  return matched


def mass_match(prediction, reference, pool, n_decks):
  """Ranking-preserving level correction that imports ONE scalar, not a shape.

  Two things are wrong with the raw elite readout's levels, and this fixes both:
  1. finite-sample ceiling - k/k out of 18-40 elites is read as exactly 100%.
     Jeffreys posterior mean (k+0.5)/(n+1) is the honest point estimate, so a
     card in all 18 elites reads 97.4%, not 100%.
  2. mass inflation - inclusion shares must sum to the mean number of DISTINCT
     cards per deck. Real 2014 decks average 17.5-18.9 distinct cards (heavy
     2-of play); the evolved elites average 19-23, so EVERY share is inflated
     ~15-25% before any ranking question is asked. A single logit shift delta,
     solved by bisection so the predicted mass matches the pre-shock real mass,
     removes it.

  Monotone in the raw share, so Spearman and top-N are exactly preserved."""
  target_mass = sum(reference.get(c, 0.0) for c in pool)
  cards = sorted(pool)
  smoothed = []
  for card in cards:
    share = prediction.get(card, 0.0)
    k = share * n_decks
    smoothed.append(min(1 - 1e-9, max(1e-9, (k + 0.5) / (n_decks + 1))))
  logits = [math.log(p / (1 - p)) for p in smoothed]

  def mass(delta):
    return sum(1 / (1 + math.exp(-(z + delta))) for z in logits)

  lo, hi = -20.0, 20.0
  for _ in range(80):
    mid = (lo + hi) / 2
    if mass(mid) < target_mass:
      lo = mid
    else:
      hi = mid
  delta = (lo + hi) / 2
  return {c: 1 / (1 + math.exp(-(z + delta))) for c, z in zip(cards, logits)}


def build_readouts(snapshots, real_baseline, pool):
  """{readout_name: {card: share}} for one class"""
  final_gen, final_occupied = snapshots[-1]
  final_unique = dedup(final_occupied)
  pooled_all = dedup([entry for _, occ in snapshots for entry in occ])

  out = {}
  #(a) current behaviour
  out["a_final_unique"] = shares_from_weighted([(d, 1.0) for d, _ in final_unique])
  #(b) bin multiplicity
  out["b_final_bins"] = shares_from_weighted([(deck, 1.0) for _, _, _, deck in final_occupied])
  #(c) fitness-temperature over the final archive
  for temperature in TEMPERATURES:
    out[f"c_final_softmax_T{temperature}"] = shares_from_weighted(
      softmax_weights(final_unique, temperature))
  #(d) larger retained pool / coarser archive
  for k in POOL_KS:
    window = snapshots[-k:] if k <= len(snapshots) else snapshots
    decks = dedup([entry for _, occ in window for entry in occ])
    out[f"d_pooled_last{k}"] = shares_from_weighted([(d, 1.0) for d, _ in decks])
  for factor in COARSEN:
    out[f"d_coarsen{factor}"] = shares_from_weighted(
      [(d, 1.0) for d, _ in dedup(coarsen(final_occupied, factor))])
  #(e1) the full bounded-rationality readout
  for temperature in TEMPERATURES:
    out[f"e1_pooled_softmax_T{temperature}"] = shares_from_weighted(
      softmax_weights(pooled_all, temperature))
  #(e2) mean of per-generation shares
  per_gen = [shares_from_weighted([(d, 1.0) for d, _ in dedup(occ)]) for _, occ in snapshots]
  cards = set().union(*per_gen)
  out["e2_gen_mean"] = {c: mean(g.get(c, 0.0) for g in per_gen) for c in cards}
  #(e3) rank-preserving quantile match onto the PRE-shock real share distribution
  #(uses only pre-shock data - the same information the no-change baseline has -
  #and is a monotone map, so Spearman/top-10 are preserved exactly)
  out["e3_quantile_final"] = quantile_match(out["a_final_unique"], real_baseline, pool)
  out["e3_quantile_pooled25"] = quantile_match(out["d_pooled_last25"], real_baseline, pool)
  #(e5) Jeffreys + mass-match: same ranking guarantee, imports one scalar only
  out["e5_massmatch_final"] = mass_match(out["a_final_unique"], real_baseline, pool,
                                          len(final_unique))
  out["e5_massmatch_pooled25"] = mass_match(out["d_pooled_last25"], real_baseline, pool,
                                             len(pooled_all))
  #(e4) pooled archive + adopter-fraction mixture (the recommended combination)
  for alpha in ALPHAS:
    cards = set(out["d_pooled_last25"]) | set(real_baseline)
    out[f"e4_pooled25_inertia_a{alpha}"] = {
      c: alpha * out["d_pooled_last25"].get(c, 0.0) + (1 - alpha) * real_baseline.get(c, 0.0)
      for c in cards}
  #(f) trivial shrink toward the no-change baseline
  base = out["a_final_unique"]
  for alpha in ALPHAS:
    cards = set(base) | set(real_baseline)
    out[f"f_inertia_a{alpha}"] = {
      c: alpha * base.get(c, 0.0) + (1 - alpha) * real_baseline.get(c, 0.0) for c in cards}
  return out


# ---------------------------------------------------------------- scoring

def score(prediction, baseline, target, pool):
  cards = [c for c in pool
           if target.get(c, 0) >= MIN_SHARE
           or prediction.get(c, 0) >= MIN_SHARE
           or baseline.get(c, 0) >= MIN_SHARE]
  errors = [abs(prediction.get(c, 0.0) - target.get(c, 0.0)) for c in cards]
  overpred = [c for c in cards
              if prediction.get(c, 0.0) >= OVERPRED_HI and target.get(c, 0.0) < OVERPRED_REAL]
  high = [c for c in cards if prediction.get(c, 0.0) >= OVERPRED_HI]
  ceiling = [c for c in cards if prediction.get(c, 0.0) >= 0.999]

  movers = [c for c in pool if abs(target.get(c, 0) - baseline.get(c, 0)) >= MOVER_THRESHOLD]
  mover_errors = [abs(prediction.get(c, 0.0) - target.get(c, 0.0)) for c in movers]
  staples = [c for c in cards if target.get(c, 0.0) >= 0.5 or prediction.get(c, 0.0) >= 0.5]
  staple_errors = [abs(prediction.get(c, 0.0) - target.get(c, 0.0)) for c in staples]
  if len(movers) > 2:
    rho = spearmanr([prediction.get(c, 0.0) for c in movers],
                    [target.get(c, 0.0) for c in movers]).statistic
  else:
    rho = float("nan")
  hits = sum(1 for c in movers
             if (prediction.get(c, 0.0) - baseline.get(c, 0)) * (target.get(c, 0) - baseline.get(c, 0)) > 0)
  overall = spearmanr([prediction.get(c, 0.0) for c in cards],
                      [target.get(c, 0.0) for c in cards]).statistic
  return {
    "n_scored": len(cards),
    "levels_mae": mean(errors) if errors else float("nan"),
    "max_abs_err": max(errors) if errors else float("nan"),
    "n_overpred": len(overpred),
    "overpred_rate": len(overpred) / len(cards) if cards else float("nan"),
    "n_pred_ge95": len(high),
    "overpred_precision": len(overpred) / len(high) if high else 0.0,
    "n_at_ceiling": len(ceiling),
    "movers_mae": mean(mover_errors) if mover_errors else float("nan"),
    "staples_mae": mean(staple_errors) if staple_errors else float("nan"),
    "n_staples": len(staples),
    "movers_spearman": rho,
    "n_movers": len(movers),
    "direction_hits": hits,
    "direction_rate": hits / len(movers) if movers else float("nan"),
    "overall_spearman": overall,
  }


ROLLING_PERIODS = ["p0_prenaxx", "p1_naxx_early", "p2_naxx_late",
                   "p3_postnerf_early", "p4_postnerf_late"]


def load_rolling_truth(period):
  shares = {c: {} for c in CLASSES}
  with (GT_DIR / f"rolling_adoption_{period}.csv").open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
      for player_class in CLASSES:
        shares[player_class][row["card"]] = float(row[f"{player_class.lower()}_share"])
  return shares


def load_rolling_prediction(mode, period):
  path = DATA / f"rolling_{mode}_predicted_{period}.csv"
  if not path.exists():
    return None, None
  shares = {c: {} for c in CLASSES}
  n_elites = {}
  with path.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
      for player_class in CLASSES:
        shares[player_class][row["card"]] = float(row[f"{player_class.lower()}_share"])
        n_elites[player_class] = int(row[f"{player_class.lower()}_n_elites"])
  return shares, n_elites


def run_rolling(modes):
  """The corrections need only the predicted shares + the elite count, both of
  which the saved rolling_*_predicted_p*.csv already carry - so the rolling
  runs can be re-read without re-running them (they save no archives)."""
  truth = {p: load_rolling_truth(p) for p in ROLLING_PERIODS}
  rows = []
  for mode in modes:
    for index, period in enumerate(ROLLING_PERIODS[1:], start=1):
      prediction, n_elites = load_rolling_prediction(mode, period)
      if prediction is None:
        continue
      previous, target = truth[ROLLING_PERIODS[index - 1]], truth[period]
      #reference distribution: what the mode is actually given. FREE only ever
      #sees p0; ANCHORED is re-seeded from the previous period's real decks.
      reference = truth["p0_prenaxx"] if mode == "free" else previous
      for player_class in CLASSES:
        pool = set(era_class_pool(player_class))
        variants = {
          "raw": prediction[player_class],
          "massmatch": mass_match(prediction[player_class], reference[player_class], pool,
                                   n_elites[player_class]),
          "quantile": quantile_match(prediction[player_class], reference[player_class], pool),
        }
        for name, shares in variants.items():
          metrics = score(shares, previous[player_class], target[player_class], pool)
          rows.append({"mode": mode, "period": period, "class": player_class, "variant": name,
                       "buzzard": round(shares.get("Starving Buzzard", 0.0), 4),
                       "real_buzzard": round(target[player_class].get("Starving Buzzard", 0.0), 4),
                       **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in metrics.items()}})

  print(f"\n{'mode':<9}{'period':<19}{'class':<9}{'variant':<11}{'MAE':>8}{'movMAE':>8}"
        f"{'nCeil':>6}{'nOver':>6}{'movRho':>8}{'dir':>9}{'Buzz':>8}{'real':>8}")
  for row in rows:
    print(f"{row['mode']:<9}{row['period']:<19}{row['class']:<9}{row['variant']:<11}"
          f"{row['levels_mae']:>8.4f}{row['movers_mae']:>8.4f}{row['n_at_ceiling']:>6}"
          f"{row['n_overpred']:>6}{row['movers_spearman']:>8.3f}"
          f"{str(row['direction_hits']) + '/' + str(row['n_movers']):>9}"
          f"{row['buzzard']:>8.1%}{row['real_buzzard']:>8.1%}")

  out = DATA / "readout_rolling.csv"
  with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
  print(f"\nwrote {out}")

  print(f"\n--- mean over all (mode, period, class) cells ---")
  print(f"{'variant':<11}{'MAE':>8}{'movMAE':>8}{'over%':>8}{'nCeil':>7}{'nOver':>7}{'movRho':>8}{'dirRate':>9}")
  for name in ("raw", "massmatch", "quantile"):
    cells = [r for r in rows if r["variant"] == name]
    print(f"{name:<11}{mean(c['levels_mae'] for c in cells):>8.4f}"
          f"{mean(c['movers_mae'] for c in cells):>8.4f}"
          f"{mean(c['overpred_rate'] for c in cells):>8.4f}"
          f"{sum(c['n_at_ceiling'] for c in cells):>7}{sum(c['n_overpred'] for c in cells):>7}"
          f"{mean(c['movers_spearman'] for c in cells):>8.3f}"
          f"{mean(c['direction_rate'] for c in cells):>9.3f}")


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--era", choices=list(ERAS), nargs="+", default=list(ERAS))
  parser.add_argument("--rolling", action="store_true",
                       help="re-score the saved rolling_*_predicted_p*.csv instead of the archives")
  parser.add_argument("--csv", default=str(DATA / "readout_comparison.csv"))
  parser.add_argument("--json", default=str(DATA / "readout_comparison.json"))
  parser.add_argument("--detail", nargs="*", default=None,
                       help="readout names to print a per-headline-card table for")
  args = parser.parse_args()

  if args.rolling:
    run_rolling(["anchored", "free"])
    return

  rows, blob = [], {}
  for era in args.era:
    cfg = ERAS[era]
    baseline_real, target_real = load_real(cfg["baseline"]), load_real(cfg["target"])
    per_class_readouts, per_class_pool = {}, {}
    for player_class in CLASSES:
      snapshots = load_snapshots(cfg["prefix"], player_class)
      if not snapshots:
        print(f"!! no archives for {cfg['prefix']} {player_class}")
        continue
      per_class_pool[player_class] = set(era_class_pool(player_class))
      per_class_readouts[player_class] = build_readouts(snapshots, baseline_real[player_class],
                                                        per_class_pool[player_class])
      print(f"{era} {player_class}: {len(snapshots)} generation snapshots, "
            f"{len(dedup(snapshots[-1][1]))} unique final elites, "
            f"{len(dedup([e for _, occ in snapshots for e in occ]))} unique decks pooled")

    if args.detail is not None:
      wanted = args.detail or ["a_final_unique", "b_final_bins", "c_final_softmax_T0.1",
                               "d_pooled_last25", "e1_pooled_softmax_T0.5", "e2_gen_mean",
                               "e3_quantile_final", "e3_quantile_pooled25", "e4_pooled25_inertia_a0.5"]
      for player_class in CLASSES:
        headline = sorted({c for c in per_class_pool[player_class]
                           if abs(target_real[player_class].get(c, 0) - baseline_real[player_class].get(c, 0)) >= 0.15},
                          key=lambda c: -target_real[player_class].get(c, 0))[:10]
        print(f"\n--- {era} {player_class}: biggest real movers (>=15pp) ---")
        print(f"{'card':<24}{'pre':>7}{'real':>7}" + "".join(f"{n.split('_', 1)[1][:9]:>10}" for n in wanted))
        for card in headline:
          print(f"{card:<24}{baseline_real[player_class].get(card, 0):>7.1%}"
                f"{target_real[player_class].get(card, 0):>7.1%}"
                + "".join(f"{per_class_readouts[player_class][n].get(card, 0.0):>10.1%}" for n in wanted))

    names = list(next(iter(per_class_readouts.values())))
    blob[era] = {}
    for name in names:
      per_class = {}
      for player_class, readouts in per_class_readouts.items():
        per_class[player_class] = score(readouts[name], baseline_real[player_class],
                                        target_real[player_class], per_class_pool[player_class])
      agg = {k: mean(per_class[c][k] for c in per_class)
             for k in ("levels_mae", "movers_mae", "staples_mae", "overpred_rate",
                       "movers_spearman", "direction_rate", "overall_spearman")}
      agg["n_overpred_total"] = sum(per_class[c]["n_overpred"] for c in per_class)
      agg["n_ceiling_total"] = sum(per_class[c]["n_at_ceiling"] for c in per_class)
      headline = per_class_readouts[HEADLINE_CLASS][name].get(HEADLINE_CARD, 0.0)
      blob[era][name] = {"per_class": per_class, "mean": agg, "buzzard_hunter": headline}
      rows.append({"era": era, "readout": name, **{k: round(v, 4) for k, v in agg.items()},
                   "buzzard_hunter": round(headline, 4)})

  with open(args.csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
  with open(args.json, "w", encoding="utf-8") as f:
    json.dump(blob, f, indent=2)

  for era in args.era:
    if era not in blob:
      continue
    real_target = load_real(ERAS[era]["target"])[HEADLINE_CLASS].get(HEADLINE_CARD, 0.0)
    print(f"\n=== {era} (mean over HUNTER/MAGE/WARRIOR; real Buzzard/Hunter = {real_target:.1%}) ===")
    print(f"{'readout':<28}{'MAE':>7}{'movMAE':>8}{'stpMAE':>8}{'over%':>7}{'nOvr':>5}{'nCeil':>6}"
          f"{'movRho':>8}{'dirHit':>8}{'allRho':>8}{'Buzz':>8}")
    for name, res in sorted(blob[era].items(), key=lambda kv: kv[1]["mean"]["movers_mae"]):
      m = res["mean"]
      print(f"{name:<28}{m['levels_mae']:>7.4f}{m['movers_mae']:>8.4f}{m['staples_mae']:>8.4f}"
            f"{m['overpred_rate']:>7.3f}{m['n_overpred_total']:>5}{m['n_ceiling_total']:>6}"
            f"{m['movers_spearman']:>8.3f}{m['direction_rate']:>8.3f}{m['overall_spearman']:>8.3f}"
            f"{res['buzzard_hunter']:>8.1%}")
  print(f"\nwrote {args.csv} and {args.json}")


if __name__ == "__main__":
  main()
