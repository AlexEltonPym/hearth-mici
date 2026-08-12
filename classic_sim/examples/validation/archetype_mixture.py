"""Feasibility study: is pooled per-class card adoption a MIXTURE of archetypes?

The rolling S3 ground truth (rolling_adoption_p*.csv) is pooled over a whole
class, but a class is a mixture of archetypes (2014 Hunter = Face + Midrange
"Sunshine" + everything else). Two questions this answers with numbers:

  1. Does a pooled 60% mean "60% everywhere" or "100% inside an archetype that
     is 60% of the field"? If the latter, the pipeline's biggest measured error
     (levels over-convergence to ~100%) is partly a mixture artifact: the model
     predicts one dominant archetype's list while reality is a mixture.
  2. Does the archetype MIX itself move across the two 2014 shocks? Only then
     can an archetype-conditional prediction (predict per archetype, then mix)
     beat the pooled prediction.

Method. Decks, dates and class inference come from rolling_periods.py wholesale
(same Set-tag allowlist that fixes the HearthPwn creation-date trap), so the
pooled numbers here reproduce data/rolling_adoption_p*.csv exactly. Archetype
labels use hearthpwn_2014_dynamics.classify's signature-card scoring with the
class-consistency gate (SIGNATURES / MIN_SCORE from run_s1_matchups,
CLASS_CARDS / MIN_SIGNATURE_HITS from buzzard_nerf_series). Decks that clear
the class gate but no archetype signature land in OTHER_<class>, so the three
buckets per class partition the class exactly and pooled = sum_a w_a * p_a
holds identically.

CIRCULARITY GUARD. Two of the target cards are themselves signature cards
(Starving Buzzard -> Sunshine Hunter, Unleash the Hounds -> Face Hunter).
Measuring their per-archetype adoption under a classifier that scores them
would be circular, so every target card is measured under a LEAVE-CARD-OUT
classification: the card is stripped from all six signatures before decks are
labelled. For the ten non-signature cards this is a no-op; for the two
signature cards it is the honest number (the naive one is printed alongside).

Outputs (all new files):
  data/archetype_mixture_coverage.csv    classification coverage per period/class
  data/archetype_mixture_cards.csv       pooled vs per-archetype adoption
  data/archetype_mixture_mix.csv         archetype mix per period + binomial SE
  data/archetype_mixture_mix_shifts.csv  two-proportion z on every mix transition
  data/archetype_mixture_decomp.csv      mix-shift vs within-archetype change
  data/archetype_mixture_oracle_mix.csv  oracle-mix ceiling vs pooled persistence
  data/archetype_mixture_cache.json      ~1.8MB deck cache (delete to rebuild;
                                         the 564MB card scan takes minutes)

Usage (from classic_sim/examples/validation):
  python archetype_mixture.py
"""
import sys, csv, json, math
from collections import Counter, defaultdict
from pathlib import Path

sys.path.append('../../src')
sys.path.append('../metagame_analysis')

from rolling_periods import PERIODS, load_period_decks
from naxx_adoption_series import load_card_counts, infer_class, CLASSES
from run_s1_matchups import SIGNATURES, ARCHETYPE_CLASS, MIN_SCORE

csv.field_size_limit(10 ** 7)
HERE = Path(__file__).parent
OUT_DIR = HERE / "data"
CACHE = OUT_DIR / "archetype_mixture_cache.json"

PERIOD_ORDER = list(PERIODS)
ARCHETYPES_BY_CLASS = {
  "HUNTER": ["Face Hunter", "Sunshine Hunter", "OTHER_HUNTER"],
  "MAGE": ["Burn Mage", "Freeze Mage", "OTHER_MAGE"],
  "WARRIOR": ["Aggro Warrior", "Control Warrior", "OTHER_WARRIOR"],
}
TARGET_CARDS = {
  "HUNTER": ["Starving Buzzard", "Unleash the Hounds", "Webspinner", "Haunted Creeper",
             "Mad Scientist", "Sludge Belcher", "Undertaker"],
  "MAGE": ["Mad Scientist", "Duplicate"],
  "WARRIOR": ["Death's Bite", "Sludge Belcher", "Loatheb"],
}
#transitions of interest: the Naxx launch (p0->p1) and the Buzzard nerf (p2->p3),
#plus the two quiet within-era steps as a noise reference
TRANSITIONS = [("p0_prenaxx", "p1_naxx_early"), ("p1_naxx_early", "p2_naxx_late"),
               ("p2_naxx_late", "p3_postnerf_early"), ("p3_postnerf_early", "p4_postnerf_late")]


# --------------------------------------------------------------- data loading

def build_cache():
  """[(period, class, [card names])] for every classified deck, cached because
  the 564MB card file takes minutes to scan."""
  deck_periods = load_period_decks()
  print(f"{len(deck_periods)} ranked decks across {len(PERIODS)} periods", flush=True)
  card_counts = load_card_counts(set(deck_periods))
  rows = []
  for deck_id, period in deck_periods.items():
    counts = card_counts.get(deck_id)
    if not counts:
      continue
    player_class = infer_class(list(counts))
    if player_class is None:
      continue
    rows.append([period, player_class, dict(counts)])
  with CACHE.open("w", encoding="utf-8") as f:
    json.dump(rows, f)
  return rows


def load_decks():
  if CACHE.exists():
    with CACHE.open(encoding="utf-8") as f:
      return json.load(f)
  return build_cache()


# --------------------------------------------------------- archetype labelling

def classify_archetype(counts, player_class, signatures):
  """Mirrors hearthpwn_2014_dynamics.classify, but the class gate is already
  applied and the signature dict is a parameter (for leave-card-out runs)."""
  best_archetype, best_score = None, 0
  for archetype, signature in signatures.items():
    if ARCHETYPE_CLASS[archetype] != player_class:
      continue
    score = sum(min(counts.get(card, 0), 2) for card in signature)
    if score > best_score:
      best_archetype, best_score = archetype, score
  if best_archetype and best_score >= MIN_SCORE:
    return best_archetype
  return f"OTHER_{player_class}"


def signatures_without(card):
  return {a: (sig - {card}) for a, sig in SIGNATURES.items()}


def label_all(decks, signatures):
  """(period, class, archetype) -> [deck card dicts]"""
  buckets = defaultdict(list)
  for period, player_class, counts in decks:
    archetype = classify_archetype(counts, player_class, signatures)
    buckets[(period, player_class, archetype)].append(counts)
  return buckets


# ------------------------------------------------------------------ statistics

def binom_se(p, n):
  return math.sqrt(p * (1 - p) / n) if n else float("nan")


def two_prop_z(p1, n1, p2, n2):
  if not n1 or not n2:
    return float("nan")
  se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
  return (p2 - p1) / se if se > 0 else float("nan")


def normal_sf(z):
  return 0.5 * math.erfc(abs(z) / math.sqrt(2)) * 2  #two-sided


# ------------------------------------------------------------------------ main

def main():
  decks = load_decks()
  print(f"{len(decks)} class-inferred decks in cache")

  # ---- A. coverage, under the unmodified signatures
  base = label_all(decks, SIGNATURES)
  coverage_rows = []
  mix = {}          # (period, class) -> {archetype: (n, share)}
  class_n = {}      # (period, class) -> n
  for period in PERIOD_ORDER:
    for player_class in CLASSES:
      archs = ARCHETYPES_BY_CLASS[player_class]
      counts = {a: len(base.get((period, player_class, a), [])) for a in archs}
      total = sum(counts.values())
      class_n[(period, player_class)] = total
      named = total - counts[f"OTHER_{player_class}"]
      mix[(period, player_class)] = {a: (counts[a], counts[a] / total if total else 0.0)
                                     for a in archs}
      coverage_rows.append({"period": period, "class": player_class, "decks": total,
                            "named_archetype": named,
                            "coverage": round(named / total, 4) if total else 0.0,
                            "a1_name": archs[0], "a1_n": counts[archs[0]],
                            "a2_name": archs[1], "a2_n": counts[archs[1]],
                            "other_n": counts[archs[2]]})

  print("\n=== A. CLASSIFICATION COVERAGE (six named archetypes vs OTHER) ===")
  print(f"{'period':20}{'class':9}{'decks':>7}{'named':>8}{'coverage':>10}   breakdown")
  for row in coverage_rows:
    archs = ARCHETYPES_BY_CLASS[row["class"]]
    detail = "  ".join(f"{a}={n}" for a, n in
                       zip(archs, (row["a1_n"], row["a2_n"], row["other_n"])))
    print(f"{row['period']:20}{row['class']:9}{row['decks']:>7}{row['named_archetype']:>8}"
          f"{row['coverage']:>10.1%}   {detail}")

  # ---- C. mix per period + noise bounds
  print("\n=== C. ARCHETYPE MIX PER PERIOD (share +/- binomial SE) ===")
  mix_rows = []
  for player_class in CLASSES:
    print(f"\n{player_class}")
    archs = ARCHETYPES_BY_CLASS[player_class]
    header = "".join(f"{a:>22}" for a in archs)
    print(f"{'period':20}{'n':>6}{header}")
    for period in PERIOD_ORDER:
      n = class_n[(period, player_class)]
      cells = []
      for a in archs:
        _, share = mix[(period, player_class)][a]
        se = binom_se(share, n)
        cells.append(f"{share:>15.1%}+-{se:.1%}")
        mix_rows.append({"period": period, "class": player_class, "archetype": a,
                         "n_class": n, "n_archetype": mix[(period, player_class)][a][0],
                         "share": round(share, 4), "se": round(se, 4)})
      print(f"{period:20}{n:>6}{''.join(cells)}")

  print("\nmix shifts across transitions (two-proportion z, |z|>1.96 = beyond sampling noise)")
  print(f"{'transition':40}{'class':9}{'archetype':18}{'from':>8}{'to':>8}{'delta':>9}{'z':>8}{'p':>9}")
  mix_shift_rows = []
  for a_period, b_period in TRANSITIONS:
    for player_class in CLASSES:
      n1, n2 = class_n[(a_period, player_class)], class_n[(b_period, player_class)]
      for a in ARCHETYPES_BY_CLASS[player_class]:
        p1 = mix[(a_period, player_class)][a][1]
        p2 = mix[(b_period, player_class)][a][1]
        z = two_prop_z(p1, n1, p2, n2)
        p_value = normal_sf(z) if z == z else float("nan")
        label = f"{a_period}->{b_period}"
        print(f"{label:40}{player_class:9}{a:18}{p1:>8.1%}{p2:>8.1%}"
              f"{p2 - p1:>+9.1%}{z:>8.2f}{p_value:>9.4f}")
        mix_shift_rows.append({"transition": label, "class": player_class, "archetype": a,
                               "share_from": round(p1, 4), "share_to": round(p2, 4),
                               "delta": round(p2 - p1, 4), "z": round(z, 3),
                               "p_value": round(p_value, 5)})

  # ---- B. per-card pooled vs per-archetype, leave-card-out classification
  print("\n=== B. POOLED vs PER-ARCHETYPE ADOPTION (leave-card-out classification) ===")
  card_rows = []
  for player_class in CLASSES:
    archs = ARCHETYPES_BY_CLASS[player_class]
    for card in TARGET_CARDS[player_class]:
      in_signature = [a for a, sig in SIGNATURES.items() if card in sig]
      buckets = label_all(decks, signatures_without(card)) if in_signature else base
      note = f"   [signature card of {', '.join(in_signature)} - removed from signatures]" if in_signature else ""
      print(f"\n{player_class} :: {card}{note}")
      print(f"{'period':20}{'pooled':>9}{'n':>7}" +
            "".join(f"{a[:16]:>26}" for a in archs) + f"{'R2_arch':>9}{'max_arch':>10}")
      for period in PERIOD_ORDER:
        n_total, hits_total = 0, 0
        per_arch = {}
        for a in archs:
          decks_a = buckets.get((period, player_class, a), [])
          n_a = len(decks_a)
          hits_a = sum(1 for d in decks_a if card in d)
          per_arch[a] = (n_a, hits_a / n_a if n_a else 0.0)
          n_total += n_a
          hits_total += hits_a
        pooled = hits_total / n_total if n_total else 0.0
        #variance decomposition: between-archetype share of the Bernoulli variance
        between = sum((n_a / n_total) * (p_a - pooled) ** 2
                      for n_a, p_a in per_arch.values()) if n_total else 0.0
        total_var = pooled * (1 - pooled)
        r2 = between / total_var if total_var > 0 else 0.0
        max_arch = max((p for _, p in per_arch.values()), default=0.0)
        cells = "".join(f"{p_a:>18.1%} (n={n_a:<4})" for n_a, p_a in
                        (per_arch[a] for a in archs))
        print(f"{period:20}{pooled:>9.1%}{n_total:>7}{cells}{r2:>9.2f}{max_arch:>10.1%}")
        row = {"class": player_class, "card": card, "period": period,
               "pooled_share": round(pooled, 4), "n_class": n_total,
               "r2_archetype": round(r2, 4), "max_archetype_share": round(max_arch, 4)}
        for slot, a in zip(("a1", "a2", "other"), archs):
          n_a, p_a = per_arch[a]
          row[f"{slot}_name"] = a
          row[f"{slot}_n"] = n_a
          row[f"{slot}_share"] = round(p_a, 4)
          row[f"{slot}_weight"] = round(n_a / n_total, 4) if n_total else 0.0
        row["_archs"] = archs
        card_rows.append(row)

      if in_signature:  #show the circular number for contrast
        naive = []
        for period in PERIOD_ORDER:
          parts = []
          for a in archs:
            decks_a = base.get((period, player_class, a), [])
            share = (sum(1 for d in decks_a if card in d) / len(decks_a)) if decks_a else 0.0
            parts.append(f"{a[:12]}={share:.0%}")
          naive.append(f"{period[:2]} " + "/".join(parts))
        print("  naive (card left IN signatures, circular): " + " | ".join(naive))

  # ---- D. change decomposition: mix shift vs within-archetype change
  print("\n=== D. CHANGE DECOMPOSITION: how much of the pooled move is mix vs within? ===")
  print("delta_pooled = sum_a delta_w_a * mean_p_a  +  sum_a mean_w_a * delta_p_a")
  print(f"{'class':9}{'card':22}{'transition':38}{'d_pooled':>10}{'mix_part':>10}{'within_part':>13}{'mix%':>8}")
  decomp_rows = []
  by_key = {(r["class"], r["card"], r["period"]): r for r in card_rows}
  for player_class in CLASSES:
    archs = ARCHETYPES_BY_CLASS[player_class]
    for card in TARGET_CARDS[player_class]:
      for a_period, b_period in TRANSITIONS:
        r1 = by_key[(player_class, card, a_period)]
        r2 = by_key[(player_class, card, b_period)]
        mix_part = within_part = 0.0
        for slot in ("a1", "a2", "other"):
          w1, w2 = r1[f"{slot}_weight"], r2[f"{slot}_weight"]
          p1, p2 = r1[f"{slot}_share"], r2[f"{slot}_share"]
          mix_part += (w2 - w1) * (p1 + p2) / 2
          within_part += (w1 + w2) / 2 * (p2 - p1)
        d_pooled = r2["pooled_share"] - r1["pooled_share"]
        denom = abs(mix_part) + abs(within_part)
        mix_frac = abs(mix_part) / denom if denom > 0 else 0.0
        label = f"{a_period}->{b_period}"
        print(f"{player_class:9}{card:22}{label:38}{d_pooled:>+10.1%}{mix_part:>+10.1%}"
              f"{within_part:>+13.1%}{mix_frac:>8.0%}")
        decomp_rows.append({"class": player_class, "card": card, "transition": label,
                            "delta_pooled": round(d_pooled, 4),
                            "mix_component": round(mix_part, 4),
                            "within_component": round(within_part, 4),
                            "mix_fraction": round(mix_frac, 4)})

  # ---- E. is the Hunter mix shift real, or classifier drift?
  #Starving Buzzard is a Sunshine Hunter signature card and MIN_SCORE is 3, so
  #the nerf removing Buzzard from decks could mechanically demote Sunshine decks
  #to Face without any real composition change. Two independent checks.
  print("\n=== E. ROBUSTNESS: is the Hunter mix shift a classification artifact? ===")
  print("mix recomputed with the nerfed/declining cards stripped from all signatures")
  variants = {
    "full signatures": SIGNATURES,
    "minus Starving Buzzard": signatures_without("Starving Buzzard"),
    "minus Buzzard+UTH": {a: sig - {"Starving Buzzard", "Unleash the Hounds"}
                          for a, sig in SIGNATURES.items()},
  }
  print(f"{'variant':26}{'period':20}{'Face':>10}{'Sunshine':>12}{'OTHER':>9}")
  for name, sigs in variants.items():
    buckets = label_all(decks, sigs)
    for period in PERIOD_ORDER:
      counts = {a: len(buckets.get((period, "HUNTER", a), []))
                for a in ARCHETYPES_BY_CLASS["HUNTER"]}
      total = sum(counts.values())
      shares = [counts[a] / total if total else 0.0 for a in ARCHETYPES_BY_CLASS["HUNTER"]]
      print(f"{name:26}{period:20}{shares[0]:>10.1%}{shares[1]:>12.1%}{shares[2]:>9.1%}")

  print("\nindependent check - pooled Hunter adoption of Buzzard-free archetype markers")
  markers = ["Savannah Highmane", "Houndmaster", "Animal Companion", "Scavenging Hyena",
             "Timber Wolf", "Tundra Rhino", "Leper Gnome", "Wolfrider", "Argent Squire",
             "Worgen Infiltrator", "Abusive Sergeant", "Leeroy Jenkins"]
  hunter_by_period = defaultdict(list)
  for period, player_class, counts in decks:
    if player_class == "HUNTER":
      hunter_by_period[period].append(counts)
  print(f"{'card':22}" + "".join(f"{p[:2]:>9}" for p in PERIOD_ORDER))
  for card in markers:
    cells = []
    for period in PERIOD_ORDER:
      pool = hunter_by_period[period]
      cells.append(f"{sum(1 for d in pool if card in d) / len(pool):>9.1%}" if pool else f"{'-':>9}")
    print(f"{card:22}" + "".join(cells))

  # ---- F. does mixture explain the over-convergence error?
  print("\n=== F. OVER-CONVERGENCE REFRAME: how much of a 100%-prediction error "
        "does the dominant archetype explain? ===")
  print("(dominant = largest-weight named archetype; 'explained' = "
        "(p_dominant - pooled) / (1 - pooled))")
  print(f"{'class':9}{'card':22}{'period':20}{'pooled':>9}{'dominant':>22}"
        f"{'p_dom':>8}{'explained':>11}")
  explained_rows = []
  for r in card_rows:
    slots = [(r[f"{s}_weight"], r[f"{s}_share"], r[f"{s}_name"]) for s in ("a1", "a2")]
    w_dom, p_dom, name_dom = max(slots)
    pooled = r["pooled_share"]
    frac = (p_dom - pooled) / (1 - pooled) if pooled < 1 else 0.0
    explained_rows.append(frac)
    print(f"{r['class']:9}{r['card']:22}{r['period']:20}{pooled:>9.1%}"
          f"{name_dom + f' (w={w_dom:.0%})':>22}{p_dom:>8.1%}{frac:>11.1%}")
  print(f"mean fraction of a 100%-prediction error explained by picking the "
        f"dominant archetype: {sum(explained_rows) / len(explained_rows):.1%}")

  # ---- G. ORACLE-MIX CEILING (the decisive test for D)
  #Best case an archetype-conditional model could ever reach on the mixture
  #channel alone: keep each archetype's period-t adoption, but hand it the TRUE
  #period-t+1 archetype mix. If that barely beats plain pooled persistence, the
  #mixture channel has nothing to give, whatever model sits on top of it.
  print("\n=== G. ORACLE-MIX CEILING: pooled persistence vs archetype-conditional "
        "with the true next mix ===")
  print("all cards at >=5% pooled share in either period; MAE in percentage points")
  print(f"{'class':9}{'transition':38}{'cards':>7}{'MAE pooled':>12}{'MAE oracle-mix':>16}{'gain':>8}")
  oracle_rows = []
  for player_class in CLASSES:
    archs = ARCHETYPES_BY_CLASS[player_class]
    for a_period, b_period in TRANSITIONS:
      stats = {}
      for period in (a_period, b_period):
        per_arch, n_total, incl = {}, 0, Counter()
        for a in archs:
          decks_a = base.get((period, player_class, a), [])
          c = Counter()
          for d in decks_a:
            c.update(set(d))
          per_arch[a] = (len(decks_a), c)
          n_total += len(decks_a)
          incl.update(c)
        stats[period] = (per_arch, n_total, incl)
      per1, n1, incl1 = stats[a_period]
      per2, n2, incl2 = stats[b_period]
      cards = {c for c in set(incl1) | set(incl2)
               if incl1[c] / n1 >= 0.05 or incl2[c] / n2 >= 0.05}
      err_pooled, err_oracle = [], []
      for card in cards:
        p1 = incl1[card] / n1
        p2 = incl2[card] / n2
        oracle = sum((per2[a][0] / n2) * (per1[a][1][card] / per1[a][0] if per1[a][0] else 0.0)
                     for a in archs)
        err_pooled.append(abs(p2 - p1))
        err_oracle.append(abs(p2 - oracle))
      mae_p = sum(err_pooled) / len(err_pooled)
      mae_o = sum(err_oracle) / len(err_oracle)
      label = f"{a_period}->{b_period}"
      print(f"{player_class:9}{label:38}{len(cards):>7}{mae_p:>12.2%}{mae_o:>16.2%}"
            f"{mae_p - mae_o:>+8.2%}")
      oracle_rows.append({"class": player_class, "transition": label, "n_cards": len(cards),
                          "mae_pooled_persistence": round(mae_p, 4),
                          "mae_oracle_mix": round(mae_o, 4),
                          "gain_pp": round((mae_p - mae_o) * 100, 3)})
  total_p = sum(r["mae_pooled_persistence"] * r["n_cards"] for r in oracle_rows)
  total_o = sum(r["mae_oracle_mix"] * r["n_cards"] for r in oracle_rows)
  total_n = sum(r["n_cards"] for r in oracle_rows)
  print(f"OVERALL ({total_n} card-transitions): pooled persistence MAE {total_p / total_n:.2%}, "
        f"oracle-mix MAE {total_o / total_n:.2%} "
        f"-> ceiling on the mixture channel = {(total_p - total_o) / total_p:+.1%} relative")

  # ---- summary numbers for the verdict
  print("\n=== SUMMARY ===")
  r2s = [r["r2_archetype"] for r in card_rows]
  print(f"archetype R^2 on card inclusion: median {sorted(r2s)[len(r2s) // 2]:.3f}, "
        f"max {max(r2s):.3f} over {len(r2s)} (card, period) cells")
  big = [r for r in card_rows if r["r2_archetype"] >= 0.10]
  print(f"cells where archetype explains >=10% of inclusion variance: {len(big)}/{len(r2s)}")
  for r in sorted(big, key=lambda r: -r["r2_archetype"])[:12]:
    print(f"   {r['class']:8}{r['card']:22}{r['period']:20}pooled={r['pooled_share']:.1%} "
          f"max_arch={r['max_archetype_share']:.1%} R2={r['r2_archetype']:.2f}")
  shock = [r for r in decomp_rows if r["transition"].startswith(("p0", "p2"))]
  mean_mix = sum(abs(r["mix_component"]) for r in shock) / len(shock)
  mean_within = sum(abs(r["within_component"]) for r in shock) / len(shock)
  print(f"\nacross the two SHOCK transitions ({len(shock)} card-transitions): "
        f"mean |mix component| {mean_mix:.1%} vs mean |within component| {mean_within:.1%} "
        f"({mean_mix / (mean_mix + mean_within):.0%} of the movement is mix)")
  print("mix vs within by (class, transition):")
  print(f"{'class':9}{'transition':38}{'mean|mix|':>11}{'mean|within|':>14}{'mix share':>11}")
  for player_class in CLASSES:
    for a_period, b_period in TRANSITIONS:
      label = f"{a_period}->{b_period}"
      cells = [r for r in decomp_rows if r["class"] == player_class and r["transition"] == label]
      m = sum(abs(r["mix_component"]) for r in cells) / len(cells)
      w = sum(abs(r["within_component"]) for r in cells) / len(cells)
      print(f"{player_class:9}{label:38}{m:>11.1%}{w:>14.1%}"
            f"{m / (m + w) if m + w else 0:>11.0%}")
  sig_shifts = [r for r in mix_shift_rows
                if abs(r["z"]) > 1.96 and r["transition"].startswith(("p0", "p2"))]
  print(f"archetype-mix shifts beyond sampling noise at the two shocks: "
        f"{len(sig_shifts)}/{sum(1 for r in mix_shift_rows if r['transition'].startswith(('p0', 'p2')))}")

  # ---- write CSVs
  def write(name, rows):
    path = OUT_DIR / name
    with path.open("w", newline="", encoding="utf-8") as f:
      writer = csv.DictWriter(f, fieldnames=list(rows[0]))
      writer.writeheader()
      writer.writerows(rows)
    print(f"wrote {path.name}")

  write("archetype_mixture_coverage.csv", coverage_rows)
  write("archetype_mixture_mix.csv", mix_rows)
  write("archetype_mixture_mix_shifts.csv", mix_shift_rows)
  write("archetype_mixture_cards.csv", [{k: v for k, v in r.items() if k != "_archs"}
                                        for r in card_rows])
  write("archetype_mixture_decomp.csv", decomp_rows)
  write("archetype_mixture_oracle_mix.csv", oracle_rows)


if __name__ == "__main__":
  main()
