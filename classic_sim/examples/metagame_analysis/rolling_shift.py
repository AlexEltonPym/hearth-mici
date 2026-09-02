"""Rolling shock-trajectory prediction: instead of one evolution across each
shock (evolve_metagame_shift.py), step through the 2014 periods that the
archive actually resolves (rolling_periods.py: boundaries at the two patch
dates, periods sized for a ~3pp adoption SE) and predict each period's
adoption from the previous one.

Two modes:
  free      only p0 uses real decks; every later period is seeded from the
            model's own previous elite population - the true forward
            prediction of the whole trajectory
  anchored  each period is seeded from the REAL decks of the previous
            period - one-step predictions that diagnose where the free run
            drifts

The piloting agent is fixed throughout (self-play champion weights). Weight
retraining per period was considered and rejected: the S5 retrain in the
Naxx world stagnated with zero promotions (the 1-ply policy class is
saturated), so per-period retrains would add noise, not adaptation. The
adaptation this experiment measures lives in the decks.

Pool/patch state per period travels in the work items via the existing era
keys (naxx_launch = Naxx pool unpatched for p1/p2, buzzard_nerf = patched
for p3/p4), so shift_remote_worker.py serves this driver unchanged.

Usage (from classic_sim/examples/metagame_analysis):
  python rolling_shift.py --mode free --backend local --cores 4 --gens-per-period 2 --population 6   # smoke
  python rolling_shift.py --mode free --backend ssh --cores 24
  python rolling_shift.py --mode anchored --backend ssh --cores 24
"""
import sys, csv, json, argparse
from pathlib import Path
from random import Random
from statistics import mean

sys.path.append('../../src')
sys.path.append('../map_elites')

from evolve_metagame_shift import (CLASSES, GAUNTLET_PER_CLASS, GAUNTLET_REAL_ANCHORS,
                                     REFRESH_EVERY, mutate_deck, era_class_pool,
                                     load_eval_weights, run_matchups_local,
                                     run_matchups_ssh, adoption_shares, novelty)
from map_elites import Archive

HERE = Path(__file__).parent
OUT_DIR = HERE / "data"
SEEDS_DIR = HERE / ".." / "validation" / "data"

#(period predicted, era key for pool/patches, mutation-bias probe csv)
PERIOD_PLAN = [
  ("p1_naxx_early", "naxx_launch", "data/probe_naxx_launch.csv"),
  ("p2_naxx_late", "naxx_launch", "data/probe_naxx_launch.csv"),
  ("p3_postnerf_early", "buzzard_nerf", "data/probe_buzzard_nerf.csv"),
  ("p4_postnerf_late", "buzzard_nerf", "data/probe_buzzard_nerf.csv"),
]
#the period whose REAL decks seed the prediction of PERIOD_PLAN[k][0]
ANCHOR_SOURCE = {
  "p1_naxx_early": "p0_prenaxx",
  "p2_naxx_late": "p1_naxx_early",
  "p3_postnerf_early": "p2_naxx_late",
  "p4_postnerf_late": "p3_postnerf_early",
}


def load_period_seeds(period):
  with (SEEDS_DIR / f"rolling_seeds_{period}.json").open(encoding="utf-8") as f:
    return json.load(f)


def load_bias(path):
  bias = {c: {} for c in CLASSES}
  with open(path, encoding="utf-8") as f:
    for row in csv.DictReader(f):
      bias[row["class"]][row["card"]] = float(row["mean_delta_wr"])
  return bias


def sample_population(seed_base, population_size, rng):
  return {player_class: [list(deck) for deck in
                          (rng.sample(seed_base[player_class], population_size)
                           if len(seed_base[player_class]) >= population_size
                           else [rng.choice(seed_base[player_class]) for _ in range(population_size)])]
          for player_class in CLASSES}


def build_gauntlet(seed_base, archives, rng):
  """1 anchor from the current seed base + elites where available."""
  gauntlet = []
  for player_class in CLASSES:
    entries = [{"class": player_class, "deck": list(rng.choice(seed_base[player_class]))}
               for _ in range(GAUNTLET_REAL_ANCHORS)]
    elites = archives[player_class].get_elites(unique_only=True) if archives else []
    wanted = GAUNTLET_PER_CLASS - GAUNTLET_REAL_ANCHORS
    picks = rng.sample(elites, wanted) if len(elites) >= wanted else elites
    entries.extend({"class": player_class, "deck": list(e["sample"][1])} for e in picks)
    while len(entries) < GAUNTLET_PER_CLASS:
      entries.append({"class": player_class, "deck": list(rng.choice(seed_base[player_class]))})
    gauntlet.extend(entries)
  return gauntlet


def evolve_period(period, era, bias, seed_base, args, eval_weights, run_matchups, rng, log):
  """One period of adaptation: evolve from seed_base under the period's
  pool/patch state. Returns (per-class adoption shares, per-class unique
  elite decks for free-running carry-forward)."""
  populations = sample_population(seed_base, args.population, rng)
  pools = {player_class: era_class_pool(player_class) for player_class in CLASSES}
  archives = {player_class: Archive("Hand size", "Turns", x_range=(1, 9), y_range=(9, 35),
                                     num_buckets=args.num_buckets,
                                     archive_name=f"{player_class} {period}")
              for player_class in CLASSES}
  gauntlet = build_gauntlet(seed_base, None, rng)

  for generation in range(args.gens_per_period):
    if generation > 0 and generation % REFRESH_EVERY == 0:
      gauntlet = build_gauntlet(seed_base, archives, rng)

    for player_class in CLASSES:
      populations[player_class] = [mutate_deck(deck, pools[player_class],
                                                bias[player_class], args.bias_strength)
                                   for deck in populations[player_class]]
    work, spans = [], {}
    for player_class in CLASSES:
      start = len(work)
      for deck in populations[player_class]:
        for opponent in gauntlet:
          work.append((deck, player_class, opponent["deck"], opponent["class"], era,
                       eval_weights, args.fixed_games, args.fixed_games))
      spans[player_class] = (start, len(work))
    results = run_matchups(work, args.cores)

    n = len(gauntlet)
    for player_class in CLASSES:
      start, end = spans[player_class]
      class_results = results[start:end]
      archive = archives[player_class]
      for i, deck in enumerate(populations[player_class]):
        matchup_results = class_results[i * n: (i + 1) * n]
        archive.add_sample(mean(r[1] for r in matchup_results), mean(r[2] for r in matchup_results),
                           fitness=mean(r[0] for r in matchup_results), sample=([], deck))
      elites = archive.get_elites(args.population, unique_only=True)
      populations[player_class] = [rng.choice(elites)["sample"][1] for _ in range(args.population)] \
        if len(elites) < args.population else [e["sample"][1] for e in elites[:args.population]]
      log.writerow([period, generation, player_class, len(elites),
                    round(mean(e["fitness"] for e in elites), 4)])
    print(f"  [{period}] gen {generation}: "
          + " ".join(f"{c}:{len(archives[c].get_elites(unique_only=True))}el" for c in CLASSES),
          flush=True)

  shares = {}
  elite_decks = {}
  for player_class in CLASSES:
    shares[player_class] = adoption_shares(archives[player_class])
    elites = archives[player_class].get_elites(unique_only=True)
    elite_decks[player_class] = [list(e["sample"][1]) for e in elites]
  return shares, elite_decks


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--mode", choices=["free", "anchored"], required=True)
  parser.add_argument("--backend", choices=["local", "ssh", "hearthrs"], default="local")
  parser.add_argument("--agent-naxx", default=None,
                      help="hearthrs backend: agent spec piloting naxx_launch-era periods")
  parser.add_argument("--agent-postnerf", default=None,
                      help="hearthrs backend: agent spec piloting buzzard_nerf-era periods")
  parser.add_argument("--bias-naxx", default=None,
                      help="override mutation-bias CSV for naxx_launch-era periods")
  parser.add_argument("--bias-nerf", default=None,
                      help="override mutation-bias CSV for buzzard_nerf-era periods")
  parser.add_argument("--cores", type=int, default=1)
  parser.add_argument("--gens-per-period", type=int, default=10)
  parser.add_argument("--population", type=int, default=16)
  parser.add_argument("--num-buckets", type=int, default=15)
  parser.add_argument("--fixed-games", type=int, default=16)
  parser.add_argument("--bias-strength", type=float, default=10.0)
  parser.add_argument("--seed", type=int, default=0)
  parser.add_argument("--eval-weights", default=str(OUT_DIR / "self_play_champion.json"))
  parser.add_argument("--out", default=None, help="output prefix (default data/rolling_<mode>)")
  parser.add_argument("--resume", action="store_true",
                      help="skip periods whose prediction + elites are already on disk")
  args = parser.parse_args()

  out_prefix = Path(args.out or f"data/rolling_{args.mode}").name
  rng = Random(args.seed)   #re-seeded per period below so resume is exact
  if args.backend == "hearthrs":
    import hearthrs_backend
    hearthrs_backend.configure(base_seed=args.seed)
    eval_weights = None   #hearth agents carry their own evaluators
    run_matchups = hearthrs_backend.run_matchups_hearthrs
    agent_by_era = {"naxx_launch": args.agent_naxx, "buzzard_nerf": args.agent_postnerf}
    missing = [era for era, spec in agent_by_era.items() if not spec]
    if missing:
      raise SystemExit(f"--backend hearthrs needs agent specs for eras {missing}")
  else:
    eval_weights = load_eval_weights(args.eval_weights)
    run_matchups = run_matchups_ssh if args.backend == "ssh" else run_matchups_local
    agent_by_era = None
  bias_override = {"naxx_launch": args.bias_naxx, "buzzard_nerf": args.bias_nerf}

  history_path = OUT_DIR / f"{out_prefix}_history.csv"
  fresh = not (args.resume and history_path.exists())
  with history_path.open("w" if fresh else "a", newline="", encoding="utf-8") as history_file:
    log = csv.writer(history_file)
    if fresh:
      log.writerow(["period", "generation", "class", "n_elites", "mean_fitness"])

    seed_base = load_period_seeds("p0_prenaxx")
    for period, era, bias_csv in PERIOD_PLAN:
      if args.mode == "anchored":
        seed_base = load_period_seeds(ANCHOR_SOURCE[period])
      rng = Random(args.seed * 1000 + PERIOD_PLAN.index((period, era, bias_csv)))
      out_csv = OUT_DIR / f"{out_prefix}_predicted_{period}.csv"
      elites_json = OUT_DIR / f"{out_prefix}_elites_{period}.json"
      if args.resume and out_csv.exists() and elites_json.exists():
        #per-period resume: the period's prediction is on disk; reload the
        #elite decks so free-running carry-forward continues unchanged
        with elites_json.open(encoding="utf-8") as f:
          elite_decks = json.load(f)
        print(f"resume: {period} already predicted, skipping", flush=True)
      else:
        bias = load_bias(bias_override[era] or bias_csv)
        if agent_by_era is not None:
          hearthrs_backend.configure(agent_spec=agent_by_era[era])
        print(f"predicting {period} (era={era}, mode={args.mode}, "
              f"seeds={ {c: len(seed_base[c]) for c in CLASSES} })", flush=True)
        shares, elite_decks = evolve_period(period, era, bias, seed_base, args,
                                             eval_weights, run_matchups, rng, log)
        history_file.flush()
        write_prediction(out_csv, shares)
        with elites_json.open("w", encoding="utf-8") as f:
          json.dump(elite_decks, f)
      if args.mode == "free":
        #next period starts from what the model itself predicts people play,
        #falling back to the previous base if a class archive came up empty
        seed_base = {c: (elite_decks[c] if elite_decks[c] else seed_base[c]) for c in CLASSES}


def write_prediction(out_csv, shares):
  all_cards = sorted(set().union(*(shares[c][0] for c in CLASSES)))
  with out_csv.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["card"] + [f"{c.lower()}_share" for c in CLASSES]
                    + [f"{c.lower()}_n_elites" for c in CLASSES])
    for card in all_cards:
      writer.writerow([card] + [round(shares[c][0].get(card, 0.0), 4) for c in CLASSES]
                      + [shares[c][1] for c in CLASSES])
  print(f"wrote {out_csv}", flush=True)


if __name__ == "__main__":
  main()
