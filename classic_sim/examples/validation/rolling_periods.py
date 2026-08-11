"""Ground truth for the rolling shock-trajectory experiment: per-PERIOD
card adoption and seed decklists, with period boundaries at the real patch
dates rather than calendar months (September straddles the nerf on the
22nd, so monthly cuts mix pre- and post-nerf decks).

Periods, sized so every one keeps enough decks for a ~3pp adoption SE:
  p0_prenaxx        2014-04-01 .. 07-21   seed only (the late pre-Naxx meta;
                                          a June-only window keeps too few
                                          decks because most were edited
                                          after Naxx and fail the Set-tag
                                          filter)
  p1_naxx_early     2014-07-22 .. 08-31   Naxx live
  p2_naxx_late      2014-09-01 .. 09-21   Naxx live, last pre-nerf weeks
  p3_postnerf_early 2014-09-22 .. 10-31   nerf live
  p4_postnerf_late  2014-11-01 .. 12-07   nerf live, pre-GvG

Reuses naxx_adoption_series.py's filtering wholesale: Ranked decks only,
date AND Set-tag both inside the period's patch era (the date-trap fix),
signature-card class inference, constructibility for seeds.

Outputs:
  data/rolling_adoption_{period}.csv   card, per-class inclusion share
  data/rolling_seeds_{period}.json     constructible 30-card decklists
  data/rolling_summary.json            deck counts per period

Usage (from classic_sim/examples/validation):
  python rolling_periods.py
"""
import csv, json
from collections import Counter
from datetime import datetime
from pathlib import Path

from buzzard_nerf_series import parse_date
from naxx_adoption_series import (CLASSES, SET_ALLOWLIST, era_pools, legendary_names,
                                    load_card_counts, infer_class, constructible, DECKS)

csv.field_size_limit(10 ** 7)
HERE = Path(__file__).parent
OUT_DIR = HERE / "data"

#period -> (start, end, era key into SET_ALLOWLIST / era_pools)
PERIODS = {
  "p0_prenaxx":        (datetime(2014, 4, 1),  datetime(2014, 7, 22),  "pre_naxx"),
  "p1_naxx_early":     (datetime(2014, 7, 22), datetime(2014, 9, 1),   "naxx_prenerf"),
  "p2_naxx_late":      (datetime(2014, 9, 1),  datetime(2014, 9, 22),  "naxx_prenerf"),
  "p3_postnerf_early": (datetime(2014, 9, 22), datetime(2014, 11, 1),  "post_nerf"),
  "p4_postnerf_late":  (datetime(2014, 11, 1), datetime(2014, 12, 8),  "post_nerf"),
}


def load_period_decks():
  decks = {}
  with DECKS.open(encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f, delimiter=";"):
      if row["DeckType"].strip() != "Ranked Deck":
        continue
      date = parse_date(row["Date"])
      if not date:
        continue
      for period, (start, end, era) in PERIODS.items():
        if start <= date < end and row["Set"].strip() in SET_ALLOWLIST[era]:
          decks[row["idDeck"]] = period
          break
  return decks


def main():
  deck_periods = load_period_decks()
  print(f"{len(deck_periods)} ranked decks across {len(PERIODS)} periods")
  card_counts = load_card_counts(set(deck_periods))
  legendaries = legendary_names()

  inclusion = {p: {c: Counter() for c in CLASSES} for p in PERIODS}
  n_decks = {p: Counter() for p in PERIODS}
  seeds = {p: {c: [] for c in CLASSES} for p in PERIODS}
  pools_by_period = {p: era_pools(era) for p, (_, _, era) in PERIODS.items()}

  for deck_id, period in deck_periods.items():
    counts = card_counts.get(deck_id)
    if not counts:
      continue
    player_class = infer_class(list(counts))
    if player_class is None:
      continue
    n_decks[period][player_class] += 1
    for card in counts:
      inclusion[period][player_class][card] += 1
    pool = pools_by_period[period][player_class]
    if constructible(counts, pool, legendaries):
      decklist = [card for card, copies in counts.items() for _ in range(copies)]
      seeds[period][player_class].append(decklist)

  summary = {}
  for period in PERIODS:
    rows = []
    all_cards = set()
    for player_class in CLASSES:
      all_cards |= set(inclusion[period][player_class])
    for card in sorted(all_cards):
      row = {"card": card}
      for player_class in CLASSES:
        n = n_decks[period][player_class]
        share = inclusion[period][player_class][card] / n if n else 0.0
        row[f"{player_class.lower()}_share"] = round(share, 4)
        row[f"{player_class.lower()}_decks"] = n
      rows.append(row)
    out_csv = OUT_DIR / f"rolling_adoption_{period}.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
      writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
      writer.writeheader()
      writer.writerows(rows)
    with (OUT_DIR / f"rolling_seeds_{period}.json").open("w", encoding="utf-8") as f:
      json.dump(seeds[period], f)
    summary[period] = {"n_decks": dict(n_decks[period]),
                       "n_seeds": {c: len(seeds[period][c]) for c in CLASSES}}
    print(f"{period}: decks={dict(n_decks[period])} seeds={summary[period]['n_seeds']}")

  with (OUT_DIR / "rolling_summary.json").open("w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
  print("wrote adoption CSVs, seed JSONs and rolling_summary.json")


if __name__ == "__main__":
  main()
