"""S1-adjacent but for the 82 real HSReplay decks that AREN'T one of the 6
named archetypes (run_s1_matchups.py's SIGNATURES) - the middle ground the
user asked for between "real, established archetype" and "fully synthetic
MAP-Elites/random deck": still human-played, real decklists, but ones our
validation work hasn't touched at all. This is a first step toward
training/evaluating on non-standard decks, before moving on to perturbing
and evolving this pool.

Unlike run_s1_matchups.py (which compares each PAIRWISE win rate against
vS's pairwise matrix), HSReplay's own win_rate column is a deck's win rate
across the *whole field it was actually played in* - there's no equivalent
pairwise ground truth for these 82. So the right analogue is a full internal
round robin: play every pair once (game.play_game() already randomizes who
goes first, so an unordered round robin is not biased toward whichever deck
is passed as "player"), then compare each deck's mean simulated win rate
across all its opponents against its real HSReplay win_rate.

Usage (from classic_sim/examples/metagame_analysis, PYTHONPATH src+validation
already appended below):
  python run_offarchetype_tournament.py --backend local --agent greedy --limit-decks 8 --out data/tournament_smoke.csv
  python run_offarchetype_tournament.py --backend ssh --agent greedy --out data/tournament_greedy.csv
"""
import sys, csv, json, argparse, subprocess, ast
from itertools import combinations
from pathlib import Path
from statistics import mean

sys.path.append('../../src')
sys.path.append('../validation')
from game_manager import GameManager
from strategy import GreedyActionSmart, MCTS
from zones import Deck
from enums import Classes, CardSets
from exceptions import TooManyActions

import dill
from scipy.stats import ttest_1samp
from joblib import Parallel, delayed

from run_s1_matchups import load_decks, pick_representatives, spearman

HERE = Path(__file__).parent
OUT_DIR = HERE / "data"
CLASS_ENUM = {"HUNTER": Classes.HUNTER, "MAGE": Classes.MAGE, "WARRIOR": Classes.WARRIOR}
CARDSET_ENUM = {"HUNTER": CardSets.CLASSIC_HUNTER, "MAGE": CardSets.CLASSIC_MAGE, "WARRIOR": CardSets.CLASSIC_WARRIOR}

#same early-stopping shape as calibrate_greedy_weights.py's
#play_matchup_till_stoppage - a sequential t-test against a fixed 0.5,
#looser alpha than a final report would use, since 3321 pairs at a fixed
#high game count would be needlessly expensive for a first "how does this
#pool look" pass.
MIN_GAMES, MAX_GAMES, PVALUE_ALPHA, MIN_STREAK = 4, 16, 0.1, 2


def make_strategy(agent_name):
  if agent_name == "greedy":
    return GreedyActionSmart()
  if agent_name == "mcts":
    return MCTS(iterations=150, guided=True)
  raise ValueError(f"unknown agent {agent_name!r}")


def play_matchup_till_stoppage(deck_a, class_a, deck_b, class_b, agent_name,
                                min_games=MIN_GAMES, max_games=MAX_GAMES):
  """Returns (win_rate_for_a, games_played). min_games/max_games are real
  parameters (not module globals) for the same reason calibrate_greedy_weights
  uses them that way - they must survive dill-over-stdin into a remote worker
  that reimports this module fresh."""
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CARDSET_ENUM[class_a]])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CARDSET_ENUM[class_b]])
  game_manager.create_player(CLASS_ENUM[class_a], Deck.generate_from_decklist(deck_a), make_strategy(agent_name))
  game_manager.create_enemy(CLASS_ENUM[class_b], Deck.generate_from_decklist(deck_b), make_strategy(agent_name))
  game_manager.create_game()

  wins = []
  streak = 0
  while len(wins) < max_games:
    try:
      result = game_manager.game.play_game()
      wins.append(1 if result[0] == 1 else 0)
    except (TooManyActions, RecursionError):
      pass
    game_manager.game.reset_game()
    game_manager.game.start_game()

    if len(wins) >= min_games:
      win_rate = mean(wins)
      if win_rate in (0.0, 1.0):
        pvalue = 0.0
      else:
        pvalue = ttest_1samp(wins, popmean=0.5).pvalue
      streak = streak + 1 if pvalue < PVALUE_ALPHA else 0
      if streak >= MIN_STREAK:
        break

  return (mean(wins) if wins else 0.5), len(wins)


def _run_one(work_item):
  return play_matchup_till_stoppage(*work_item)


def run_matchups_local(work_items, cores):
  if cores == 1:
    return [_run_one(item) for item in work_items]
  return Parallel(n_jobs=cores)(delayed(_run_one)(item) for item in work_items)


#SSH distribution, mirroring calibrate_greedy_weights.py's run_host/run_matchups_ssh
#exactly (same protocol, same hardcoded working directory both hosts already
#expect) - a separate remote worker script (tournament_remote_worker.py) since
#the work-item shape here (agent name, not weights vector) differs.
HOSTS = ["dwail1", "dwail2"]


def run_host(work_items, host):
  if not work_items:
    return []
  print(f"Starting host {host} with {len(work_items)} work items...", flush=True)
  serial_work = dill.dumps(work_items, fmode='wb')
  dir_ = "~/phd/hearth-mici/classic_sim/examples/metagame_analysis/" if host == "laptop" else "~/classic_sim/examples/metagame_analysis/"
  command = f'cd {dir_} && source ~/.profile && pyenv activate venv && python3 tournament_remote_worker.py'
  ssh = subprocess.Popen(["ssh", host, command], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
  result, err = ssh.communicate(input=serial_work)
  if err:
    print(f"{host} error: {err.decode(errors='replace')}")

  for line in result.decode(errors="replace").splitlines():
    if line[:3] == ">>>":
      print(f"Closing host {host}.", flush=True)
      return ast.literal_eval(line[3:])
    else:
      print(f"{host}> {line}")
  raise RuntimeError(f"{host} never returned a >>> result line")


def run_matchups_ssh(work_items, cores):
  n = len(HOSTS)
  chunks = [work_items[i::n] for i in range(n)]
  host_results = Parallel(n_jobs=n, backend="threading")(delayed(run_host)(chunk, host) for chunk, host in zip(chunks, HOSTS))
  results = [None] * len(work_items)
  for host_index, this_host_results in enumerate(host_results):
    for offset, value in enumerate(this_host_results):
      results[host_index + offset * n] = value
  return results


def load_offarchetype_decks(limit_decks=None):
  """The 82 real decks that aren't one of the 6 named-archetype representatives
  already used throughout S1 validation."""
  decks = load_decks()
  reps, _ = pick_representatives(decks)
  rep_card_lists = {"|".join(cards) for cards in reps.values()}
  pool = [d for d in decks if d["card_list"] not in rep_card_lists]
  if limit_decks:
    pool = pool[:limit_decks]
  return pool


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--agent", choices=["greedy", "mcts"], default="greedy")
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--cores", type=int, default=1, help="local backend only")
  parser.add_argument("--limit-decks", type=int, default=None, help="smoke-test with only the first N decks")
  parser.add_argument("--out", default=str(OUT_DIR / "offarchetype_tournament.csv"))
  args = parser.parse_args()

  pool = load_offarchetype_decks(args.limit_decks)
  print(f"{len(pool)} off-archetype decks, agent={args.agent}, backend={args.backend}")

  pairs = list(combinations(range(len(pool)), 2))
  print(f"{len(pairs)} round-robin pairs")

  work_items = [
    (pool[i]["card_list"].split("|"), pool[i]["class"], pool[j]["card_list"].split("|"), pool[j]["class"], args.agent)
    for i, j in pairs
  ]

  run_matchups = run_matchups_ssh if args.backend == "ssh" else run_matchups_local
  results = run_matchups(work_items, args.cores)

  #each pair contributes one win rate for i (a-side) and its complement for j
  deck_win_rates = {idx: [] for idx in range(len(pool))}
  deck_games = {idx: 0 for idx in range(len(pool))}
  for (i, j), (win_rate_i, games) in zip(pairs, results):
    deck_win_rates[i].append(win_rate_i)
    deck_win_rates[j].append(1 - win_rate_i)
    deck_games[i] += games
    deck_games[j] += games

  rows = []
  comparison = []
  for idx, deck in enumerate(pool):
    sim_win_rate = mean(deck_win_rates[idx]) if deck_win_rates[idx] else float("nan")
    real_win_rate = float(deck["win_rate"])
    rows.append({
      "deck_id": deck["deck_id"], "class": deck["class"],
      "real_win_rate_pct": real_win_rate, "sim_win_rate_pct": round(sim_win_rate * 100, 1),
      "opponents_played": len(deck_win_rates[idx]), "total_games": deck_games[idx],
    })
    comparison.append((real_win_rate, sim_win_rate * 100))

  out_path = Path(args.out)
  out_path.parent.mkdir(parents=True, exist_ok=True)
  with out_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["deck_id", "class", "real_win_rate_pct", "sim_win_rate_pct", "opponents_played", "total_games"])
    writer.writeheader()
    writer.writerows(rows)

  rho = spearman(comparison)
  mse = mean((r - s) ** 2 for r, s in comparison)
  print(f"\n{len(pool)} decks, {len(pairs)} pairs, {sum(deck_games.values()) // 2} games total")
  print(f"Spearman rank correlation (real HSReplay win rate vs simulated round-robin win rate): {rho:.3f}")
  print(f"MSE (percentage points^2): {mse:.1f}")
  print(f"wrote {out_path}")

  summary_path = out_path.with_suffix(".summary.json")
  with summary_path.open("w", encoding="utf-8") as f:
    json.dump({"agent": args.agent, "n_decks": len(pool), "n_pairs": len(pairs),
               "spearman": rho, "mse": mse}, f, indent=2)
  print(f"wrote {summary_path}")


if __name__ == "__main__":
  main()
