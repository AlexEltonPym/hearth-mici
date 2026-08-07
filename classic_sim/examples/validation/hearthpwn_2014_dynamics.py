"""S3-adjacent: does simulated deck power predict real metagame popularity shifts?

The HSReplay 2021 snapshot showed a deck's real win rate is nearly uncorrelated
with how much it was played (Spearman -0.03 across the 88 constructible decks),
so a static power number can't predict popularity by itself. The testable
hypothesis is dynamic instead: players gravitate toward what is currently
winning against the field they are actually facing, so an archetype's
FIELD-WEIGHTED win rate (its matchup row weighted by the current popularity
mix) should predict its next-month popularity CHANGE, replicator-style.

Ground truth: the Zenodo/HearthPwn archive (data/decks/, DOI
10.5281/zenodo.10198504), restricted to Ranked decks from 1 Jan - 21 Jul 2014,
the pre-Naxxramas window when the real ladder ran on exactly the simulator's
card pool (Basic + Classic). Popularity here means submission share among
classified Mage/Hunter/Warrior decks - deckbuilder interest, not games played
(the archive has no play counts) - a caveat carried through interpretation.
July is a partial month (Naxx landed 22 Jul).

Three stages, each skippable if its output already exists (--force to redo):
  A. classify every pre-Naxx ranked deck into the six S1 archetypes (same
     signature-card scoring as run_s1_matchups, plus a class-consistency
     check) -> data/hearthpwn_2014_archetype_series.csv, and build a
     2014-NATIVE representative deck per archetype from the cards those
     real decks actually ran -> data/hearthpwn_2014_representatives.json
  B. simulate the 6x6 matchup matrix between those representatives with the
     current engine (GreedyActionSmart + self-play champion weights, fixed
     GAMES games per pair - confirm-phase style, no early stopping)
     -> data/hearthpwn_2014_matrix.csv
  C. field-weighted win rates per month vs next-month share changes
     -> data/hearthpwn_2014_dynamics.csv + printed verdict

Usage (from classic_sim/examples/validation):
  python hearthpwn_2014_dynamics.py --cores 10
  python hearthpwn_2014_dynamics.py --agent mcts --backend ssh   #matrix via dwail1/dwail2
"""
import sys, csv, json, argparse, os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean

sys.path.append('../../src')
sys.path.append('../metagame_analysis')

from card_sets import (get_basic_cards, get_common_cards, get_rare_cards, get_epic_cards,
                        get_legendary_cards, get_hunter_cards, get_mage_cards, get_warrior_cards)
from run_s1_matchups import SIGNATURES, ARCHETYPE_CLASS, MIN_SCORE, spearman
from buzzard_nerf_series import CLASS_CARDS, MIN_SIGNATURE_HITS, parse_date

csv.field_size_limit(10 ** 7)
HERE = Path(__file__).parent
DECKS = HERE / "data" / "decks" / "zenodo_decks.csv"
CARDS = HERE / "data" / "decks" / "zenodo_cards.csv"
CHAMPION = HERE / ".." / "metagame_analysis" / "data" / "self_play_champion.json"
SERIES_OUT = HERE / "data" / "hearthpwn_2014_archetype_series.csv"
REPS_OUT = HERE / "data" / "hearthpwn_2014_representatives.json"

NAXX_LAUNCH = datetime(2014, 7, 22)
ARCHETYPES = list(SIGNATURES)
GAMES = 60
#each pair's fixed GAMES games are split into chunks this size so a slow agent
#(MCTS: ~15 pairs would otherwise each run 60 sequential games on one core)
#spreads across cores/hosts; equal-sized chunks mean a plain mean recombines them
CHUNK = 10


def matrix_path(agent):
  return HERE / "data" / ("hearthpwn_2014_matrix.csv" if agent == "greedy"
                           else f"hearthpwn_2014_matrix_{agent}.csv")


def dynamics_path(agent):
  return HERE / "data" / ("hearthpwn_2014_dynamics.csv" if agent == "greedy"
                           else f"hearthpwn_2014_dynamics_{agent}.csv")


#---------------------------------------------------------------- stage A

def legal_pools():
  """Class-legal card-name sets: neutrals (rarity getters) + own class cards."""
  neutrals = {card.name for card in (get_basic_cards() + get_common_cards() + get_rare_cards()
                                      + get_epic_cards() + get_legendary_cards())}
  class_cards = {"HUNTER": get_hunter_cards(), "MAGE": get_mage_cards(), "WARRIOR": get_warrior_cards()}
  return {player_class: neutrals | {card.name for card in cards}
          for player_class, cards in class_cards.items()}


def load_prenaxx_ranked_decks():
  decks = {}
  with DECKS.open(encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f, delimiter=";"):
      date = parse_date(row["Date"])
      if (date and date.year == 2014 and date < NAXX_LAUNCH
          and row["DeckType"].strip() == "Ranked Deck"):
        decks[row["idDeck"]] = date
  return decks


def load_card_counts(deck_ids):
  """Counter of card name -> copies per deck (the archive repeats a row per copy)."""
  counts = defaultdict(Counter)
  with CARDS.open(encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f, delimiter=";")
    next(reader)
    for row in reader:
      if len(row) >= 2 and row[0] in deck_ids:
        counts[row[0]][row[1].strip()] += 1
  return counts


def infer_class(deck_cards):
  hits = {name: len(set(deck_cards) & signature) for name, signature in CLASS_CARDS.items()}
  best = max(hits, key=hits.get)
  return best if hits[best] >= MIN_SIGNATURE_HITS else None


def classify(deck_cards):
  """(label, player_class): one of the six S1 archetypes, or OTHER_<class>.
  Signature scoring mirrors run_s1_matchups.pick_representatives, but with an
  extra class-consistency gate - several signatures contain neutrals
  (Doomsayer, Alexstrasza...), so an off-class deck could otherwise sneak
  over MIN_SCORE."""
  player_class = infer_class(deck_cards)
  if not player_class:
    return None, None
  best_archetype, best_score = None, 0
  for archetype, signature in SIGNATURES.items():
    if ARCHETYPE_CLASS[archetype] != player_class:
      continue
    score = sum(min(deck_cards.get(card, 0), 2) for card in signature)
    if score > best_score:
      best_archetype, best_score = archetype, score
  if best_archetype and best_score >= MIN_SCORE:
    return best_archetype, player_class
  return f"OTHER_{player_class}", player_class


def build_representative(deck_counters, player_class, pools, legendary_names):
  """30-card decklist from what the archetype's real decks actually ran:
  cards ranked by inclusion frequency; 2 copies when the majority of
  including decks ran 2 (legendaries capped at 1)."""
  include, two_of = Counter(), Counter()
  for counter in deck_counters:
    for card, copies in counter.items():
      if card in pools[player_class]:
        include[card] += 1
        if copies >= 2:
          two_of[card] += 1

  deck = []
  for card, freq in include.most_common():
    if len(deck) >= 30:
      break
    max_copies = 1 if card in legendary_names else 2
    copies = 2 if (max_copies == 2 and two_of[card] * 2 >= freq) else 1
    deck.extend([card] * min(copies, 30 - len(deck)))
  #under-filled only if the archetype ran very few distinct constructible
  #cards - upgrade the most-included 1-ofs to 2 before giving up
  if len(deck) < 30:
    for card, _ in include.most_common():
      if len(deck) >= 30:
        break
      if deck.count(card) == 1 and card not in legendary_names:
        deck.append(card)
  return sorted(deck)


def stage_a():
  print("stage A: classifying pre-Naxx 2014 ranked decks...", flush=True)
  decks = load_prenaxx_ranked_decks()
  cards = load_card_counts(set(decks))
  print(f"  {len(decks)} ranked pre-Naxx decks, {len(cards)} with card lists")

  pools = legal_pools()
  legendary_names = {card.name for card in get_legendary_cards()}
  months = defaultdict(Counter)
  by_archetype = defaultdict(list)
  for deck_id, date in decks.items():
    deck_cards = cards.get(deck_id)
    if not deck_cards:
      continue
    label, player_class = classify(deck_cards)
    if not label:
      continue
    months[f"{date.year}-{date.month:02d}"][label] += 1
    if label in SIGNATURES:
      by_archetype[label].append(deck_cards)

  labels = ARCHETYPES + [f"OTHER_{c}" for c in ("HUNTER", "MAGE", "WARRIOR")]
  rows = []
  for month in sorted(months):
    counts = months[month]
    total = sum(counts[label] for label in labels)
    row = {"month": month, "classified_decks": total}
    for label in labels:
      row[label] = counts[label]
      row[f"{label}_share"] = counts[label] / total if total else 0.0
    rows.append(row)
  with SERIES_OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
  print(f"  wrote {SERIES_OUT}")

  reps = {}
  for archetype in ARCHETYPES:
    deck_counters = by_archetype[archetype]
    if len(deck_counters) < 10:
      print(f"  WARNING: only {len(deck_counters)} decks for {archetype} - representative will be thin")
    reps[archetype] = {"class": ARCHETYPE_CLASS[archetype], "n_source_decks": len(deck_counters),
                        "deck": build_representative(deck_counters, ARCHETYPE_CLASS[archetype],
                                                     pools, legendary_names)}
  with REPS_OUT.open("w", encoding="utf-8") as f:
    json.dump(reps, f, indent=2)
  print(f"  wrote {REPS_OUT}")
  for archetype, rep in reps.items():
    print(f"  {archetype}: {rep['n_source_decks']} source decks, {len(rep['deck'])} cards")


#---------------------------------------------------------------- stage B

def stage_b(cores, agent, backend):
  from run_offarchetype_tournament import run_matchups_local, run_matchups_ssh

  print(f"stage B: simulating 6x6 matrix, agent={agent}, backend={backend}, "
        f"fixed {GAMES} games/pair in {CHUNK}-game chunks...", flush=True)
  with REPS_OUT.open(encoding="utf-8") as f:
    reps = json.load(f)
  with CHAMPION.open(encoding="utf-8") as f:
    loaded = json.load(f)
  full_weights = loaded.get("champion_weights") or loaded["weights"]
  #same convention as run_offarchetype_tournament: greedy takes the full
  #vector, MCTS's evaluate_position has no turn_passed feature
  eval_weights = full_weights if agent == "greedy" else full_weights[1:]

  pairs = [(a, b) for i, a in enumerate(ARCHETYPES) for b in ARCHETYPES[i + 1:]]
  chunks_per_pair = GAMES // CHUNK
  work_items = [
    (reps[a]["deck"], reps[a]["class"], reps[b]["deck"], reps[b]["class"],
     agent, eval_weights, CHUNK, CHUNK)
    for a, b in pairs for _ in range(chunks_per_pair)
  ]
  run_matchups = run_matchups_ssh if backend == "ssh" else run_matchups_local
  results = run_matchups(work_items, cores)

  matrix = {a: {a: 0.5} for a in ARCHETYPES}
  for i, (a, b) in enumerate(pairs):
    chunk_results = results[i * chunks_per_pair: (i + 1) * chunks_per_pair]
    win_rate = mean(r[0] for r in chunk_results)
    matrix[a][b] = win_rate
    matrix[b][a] = 1 - win_rate
  out = matrix_path(agent)
  with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["archetype"] + ARCHETYPES)
    writer.writeheader()
    for a in ARCHETYPES:
      writer.writerow({"archetype": a, **{b: round(matrix[a][b], 3) for b in ARCHETYPES}})
  print(f"  wrote {out}")
  return matrix


#---------------------------------------------------------------- stage C

def stage_c(agent):
  print(f"stage C: field-weighted win rate vs next-month popularity shift (agent={agent})", flush=True)
  with SERIES_OUT.open(encoding="utf-8") as f:
    series = list(csv.DictReader(f))
  with matrix_path(agent).open(encoding="utf-8") as f:
    matrix = {row["archetype"]: {a: float(row[a]) for a in ARCHETYPES}
              for row in csv.DictReader(f)}

  #popularity mix over the six tracked archetypes only (the matrix says
  #nothing about OTHER_* decks), renormalised per month
  shares = []
  for row in series:
    counts = {a: int(row[a]) for a in ARCHETYPES}
    total = sum(counts.values())
    shares.append({"month": row["month"], **{a: counts[a] / total for a in ARCHETYPES}})

  rows, weighted_points, rowmean_points, momentum_points = [], [], [], []
  row_means = {a: mean(matrix[a][b] for b in ARCHETYPES if b != a) for a in ARCHETYPES}
  for t in range(len(shares) - 1):
    now, nxt = shares[t], shares[t + 1]
    for a in ARCHETYPES:
      weighted = sum(now[b] * matrix[a][b] for b in ARCHETYPES)
      change = nxt[a] - now[a]
      rows.append({"month": now["month"], "archetype": a, "share": round(now[a], 4),
                   "field_weighted_wr": round(weighted, 4), "row_mean_wr": round(row_means[a], 4),
                   "next_share_change": round(change, 4)})
      weighted_points.append((weighted, change))
      rowmean_points.append((row_means[a], change))
      if t > 0:
        momentum_points.append((now[a] - shares[t - 1][a], change))

  with dynamics_path(agent).open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
  print(f"  wrote {dynamics_path(agent)}\n")

  print(f"{'month':9}{'archetype':18}{'share':>8}{'field_wr':>10}{'next_change':>13}")
  for row in rows:
    print(f"{row['month']:9}{row['archetype']:18}{row['share']:>8.1%}"
          f"{row['field_weighted_wr']:>10.3f}{row['next_share_change']:>+13.1%}")

  n = len(weighted_points)
  print(f"\n{n} (archetype, month) points, {len(shares)} months")
  print(f"Spearman(field-weighted win rate -> next-month share change): "
        f"{spearman(weighted_points):.3f}")
  print(f"Spearman(static row-mean win rate -> next-month share change): "
        f"{spearman(rowmean_points):.3f}  (baseline: power alone, no field weighting)")
  print(f"Spearman(this-month share change -> next-month share change):  "
        f"{spearman(momentum_points):.3f}  (baseline: pure momentum, no simulation)")


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--agent", choices=["greedy", "mcts"], default="greedy")
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--cores", type=int, default=max(1, (os.cpu_count() or 2) - 2))
  parser.add_argument("--force", action="store_true", help="redo stages whose outputs already exist")
  args = parser.parse_args()

  if args.force or not (SERIES_OUT.exists() and REPS_OUT.exists()):
    stage_a()
  else:
    print(f"stage A: outputs exist, skipping (--force to redo)")
  if args.force or not matrix_path(args.agent).exists():
    stage_b(args.cores, args.agent, args.backend)
  else:
    print(f"stage B: {matrix_path(args.agent).name} exists, skipping (--force to redo)")
  stage_c(args.agent)


if __name__ == "__main__":
  main()
