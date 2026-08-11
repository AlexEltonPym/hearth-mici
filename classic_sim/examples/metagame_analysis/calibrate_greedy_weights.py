"""CMA-ES calibration of GreedyActionSmart's feature weights against real
Classic matchup win rates. See the plan this was scoped from (session notes,
Aug 2026) for the full design rationale - summary:

- Optimizer: CMA-ES (cma.CMAEvolutionStrategy). Not "because it's imported
  elsewhere" - the problem is a continuous ~27-dim vector, evaluated only
  through noisy game simulation (no gradient), with parameters at very
  different natural scales (health diffs ~O(30), taunt-count diffs ~O(3)).
  That's squarely CMA-ES's niche; Bayesian optimization wants far fewer,
  far more expensive evaluations than we have, and plain (isotropic)
  evolution strategies ignore exactly the cross-parameter correlation
  CMA-ES is built to adapt to.
- Objective is NOT pure win-rate matching. A bare
  minimize(|sim_winrate - real_winrate|) loss is gameable: an archetype that
  currently overperforms real players could "fix" that by deliberately
  playing worse, not by playing more realistically. skill_deficit(w) below
  is a one-sided penalty against exactly that - it never rewards being
  stronger than the current baseline, it only punishes being weaker.
- Feature representation: GreedyActionSmart's original 21 features plus 6
  additive ones defined in strategy.py (lethal margin both ways, weapon
  durability, fatigue proximity, hero power availability, unused mana).
  Default weights are the original 21 plus 6 zeros, so calibration starts
  from "today's heuristic, unchanged" and a positive/negative weight on a
  new feature is a genuine, evidenced finding, not an assumption.

Real ground truth (representative decklists + the vS matchup matrix) is
reused from run_s1_matchups.py - no new data collection needed here.
"""
import sys, csv, json, argparse, subprocess, ast
from itertools import permutations
from pathlib import Path
from statistics import mean

sys.path.append('../../src')
sys.path.append('../validation')
from game_manager import GameManager
from strategy import GreedyActionSmart, RandomAction
from zones import Deck
from enums import Classes, CardSets
from exceptions import TooManyActions

import cma
import dill
from scipy.stats import ttest_1samp
from joblib import Parallel, delayed

from run_s1_matchups import (pick_representatives, load_real_matrix, load_decks,
                              ARCHETYPE_CLASS, CLASS_ENUM, CARDSET_ENUM)

HERE = Path(__file__).parent
OUT_DIR = HERE / "data"

DEFAULT_WEIGHTS = [-1, 10, -10, 10, 10, 1, 1, 1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
NUM_FEATURES = len(DEFAULT_WEIGHTS)

#early-stopping matchup evaluation, adapted from metagame.py's
#play_games_till_stoppage (which early-stops on a health-differential
#t-test, for the MAP-Elites fitness signal) - here the quantity that
#matters is win rate, so the sequential test is against a fixed 0.5
#(i.e. "is this matchup no longer a coinflip") rather than a two-sample
#comparison. Looser alpha than a final report would use, since this drives
#a search loop where speed matters more than precision - see the
#confirm-phase full-fidelity re-run for the final numbers.
MIN_GAMES, MAX_GAMES, PVALUE_ALPHA, MIN_STREAK = 4, 16, 0.1, 2


def make_strategy(weights):
  return RandomAction() if weights is None else GreedyActionSmart(list(weights))


#naxx-world pool support (S5 heuristic retraining): same reasoning as
#min_games/max_games below - world must be a positional work-item field, not
#module state, to survive the dill round trip to the remote workers
NAXX_CARDSET_ENUM = {"HUNTER": CardSets.NAXX_HUNTER, "MAGE": CardSets.NAXX_MAGE,
                     "WARRIOR": CardSets.NAXX_WARRIOR}


def _pool_sets(player_class, world):
  if world == "naxx":
    return [CardSets.CLASSIC_NEUTRAL, CardSets.NAXX_NEUTRAL,
            CARDSET_ENUM[player_class], NAXX_CARDSET_ENUM[player_class]]
  return [CardSets.CLASSIC_NEUTRAL, CARDSET_ENUM[player_class]]


def play_matchup_till_stoppage(deck_a, class_a, weights_a, deck_b, class_b, weights_b,
                                min_games=MIN_GAMES, max_games=MAX_GAMES, world="classic"):
  """Returns (win_rate_for_a, games_played). weights_a/b=None -> RandomAction.
  min_games/max_games are parameters, not just module defaults, so a caller
  (e.g. the confirm-phase fixed-count re-run in analyze_calibration.py) can
  override them per work item - min_games/max_games baked into a *closure*
  instead would silently not propagate through the dill-over-stdin remote
  worker, since that reimports this module fresh on the other end."""
  game_manager = GameManager()
  game_manager.create_player_pool(_pool_sets(class_a, world))
  game_manager.create_enemy_pool(_pool_sets(class_b, world))
  game_manager.create_player(CLASS_ENUM[class_a], Deck.generate_from_decklist(deck_a), make_strategy(weights_a))
  game_manager.create_enemy(CLASS_ENUM[class_b], Deck.generate_from_decklist(deck_b), make_strategy(weights_b))
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
        pvalue = 0.0 #a constant sample has no variance for a t-test - a clean sweep is already decisive
      else:
        pvalue = ttest_1samp(wins, popmean=0.5).pvalue
      streak = streak + 1 if pvalue < PVALUE_ALPHA else 0
      if streak >= MIN_STREAK:
        break

  return (mean(wins) if wins else 0.5), len(wins)


def build_matchup_lists(reps, exclude_archetype=None):
  """exclude_archetype: leave-one-archetype-out CV support - drop every real
  matchup pair touching this archetype from the FITTING set (skill-floor
  checks still run for it - that's an independent, un-gameable measure and
  fine to keep). The excluded pairs are what analyze_calibration.py should
  then score the fitted result against, as the held-out generalization test."""
  real_matrix = load_real_matrix()
  real_pairs = [(hero, opponent) for hero, opponent in permutations(reps.keys(), 2) if (hero, opponent) in real_matrix]
  if exclude_archetype:
    real_pairs = [(hero, opponent) for hero, opponent in real_pairs if exclude_archetype not in (hero, opponent)]
  skill_archetypes = list(reps.keys())
  return real_pairs, skill_archetypes, real_matrix


def evaluate_generation(candidates, reps, real_pairs, real_matrix, skill_archetypes,
                         baseline_skill, w_default, lambda_reg, lambda_skill, cores, run_matchups):
  """candidates: list of weight vectors. Returns list of losses, same order.
  run_matchups(work_items) -> list of win_rate_for_a results, one per item,
  where a work item is (deck_a, class_a, weights_a, deck_b, class_b, weights_b)
  - the pluggable seam for local joblib vs. distributed SSH execution."""
  work = []
  for weights in candidates:
    for hero, opponent in real_pairs:
      work.append((reps[hero], ARCHETYPE_CLASS[hero], list(weights), reps[opponent], ARCHETYPE_CLASS[opponent], list(weights)))
    for archetype in skill_archetypes:
      work.append((reps[archetype], ARCHETYPE_CLASS[archetype], list(weights), reps[archetype], ARCHETYPE_CLASS[archetype], None))

  results = run_matchups(work, cores)

  losses = []
  idx = 0
  n_real, n_skill = len(real_pairs), len(skill_archetypes)
  for weights in candidates:
    real_results = results[idx: idx + n_real]; idx += n_real
    skill_results = results[idx: idx + n_skill]; idx += n_skill

    matching_loss = mean(
      (real_results[i] * 100 - real_matrix[real_pairs[i]][0]) ** 2 for i in range(n_real)
    )
    skill_deficit = sum(
      max(0.0, baseline_skill[skill_archetypes[i]] - skill_results[i]) for i in range(n_skill)
    )
    reg = sum((w - d) ** 2 for w, d in zip(weights, w_default))

    losses.append(matching_loss + lambda_reg * reg + lambda_skill * skill_deficit)
  return losses


def _run_one(work_item):
  return play_matchup_till_stoppage(*work_item)[0]


def run_matchups_local(work_items, cores):
  if cores == 1:
    return [_run_one(item) for item in work_items]
  return Parallel(n_jobs=cores)(delayed(_run_one)(item) for item in work_items)


#distributed backend, mirroring metagame.py's run_ssh_tournament/run_host
#(same dill-over-stdin protocol, same ">>>"-prefixed result line, same
#hardcoded ~/classic_sim/examples/metagame_analysis working directory,
#reused rather than reinvented since dwail1/dwail2 already have a working
#`venv` pyenv environment with every dependency this needs).
HOSTS = ["dwail1", "dwail2"]


def run_host(work_items, host):
  if not work_items:
    return []
  print(f"Starting host {host} with {len(work_items)} work items...", flush=True)
  serial_work = dill.dumps(work_items, fmode='wb')
  dir_ = "~/phd/hearth-mici/classic_sim/examples/metagame_analysis/" if host == "laptop" else "~/classic_sim/examples/metagame_analysis/"
  command = f'cd {dir_} && source ~/.profile && pyenv activate venv && python3 calibrate_remote_worker.py'
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
  #cores is unused here (kept for interface parity with run_matchups_local) -
  #parallelism comes from the number of hosts, each running its own local
  #joblib pool inside calibrate_remote_worker.py across all its own cores.
  n = len(HOSTS)
  chunks = [work_items[i::n] for i in range(n)] #round-robin split, so results can be re-interleaved back into original order
  host_results = Parallel(n_jobs=n, backend="threading")(delayed(run_host)(chunk, host) for chunk, host in zip(chunks, HOSTS))
  results = [None] * len(work_items)
  for host_index, this_host_results in enumerate(host_results):
    for offset, value in enumerate(this_host_results):
      results[host_index + offset * n] = value
  return results


def compute_baseline_skill(reps, skill_archetypes, cores, run_matchups):
  """Win rate of the DEFAULT weights vs RandomAction, per archetype - computed
  once, not per CMA-ES candidate, since it doesn't depend on the candidate."""
  work = [(reps[a], ARCHETYPE_CLASS[a], DEFAULT_WEIGHTS, reps[a], ARCHETYPE_CLASS[a], None) for a in skill_archetypes]
  results = run_matchups(work, cores)
  return {a: r for a, r in zip(skill_archetypes, results)}


def run_cma_es(reps, real_pairs, real_matrix, skill_archetypes, baseline_skill, w_default,
               lambda_reg, lambda_skill, cores, run_matchups, sigma0, max_generations, popsize, log_path):
  es = cma.CMAEvolutionStrategy(list(w_default), sigma0, {"popsize": popsize} if popsize else {})
  history = []
  generation = 0
  while not es.stop() and generation < max_generations:
    candidates = es.ask()
    losses = evaluate_generation(candidates, reps, real_pairs, real_matrix, skill_archetypes,
                                  baseline_skill, w_default, lambda_reg, lambda_skill, cores, run_matchups)
    es.tell(candidates, losses)
    generation += 1
    best_loss = min(losses)
    print(f"gen {generation}: best={best_loss:.3f} mean={mean(losses):.3f}", flush=True)
    history.append({"generation": generation, "best_loss": best_loss, "mean_loss": mean(losses)})

  if log_path:
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", newline="", encoding="utf-8") as f:
      writer = csv.DictWriter(f, fieldnames=["generation", "best_loss", "mean_loss"])
      writer.writeheader()
      writer.writerows(history)

  return list(es.result.xbest), es.result.fbest


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--cores", type=int, default=1)
  parser.add_argument("--popsize", type=int, default=0, help="0 = cma default (~4+3ln(D))")
  parser.add_argument("--max-generations", type=int, default=100)
  parser.add_argument("--sigma0", type=float, default=2.0)
  parser.add_argument("--lambda-reg", type=float, default=0.05)
  parser.add_argument("--lambda-skill", type=float, default=200.0, help="skill_deficit is a win-rate fraction (0-1 scale); this weights it against a %%^2 matching loss")
  parser.add_argument("--out", default=str(OUT_DIR / "calibrated_weights.json"))
  parser.add_argument("--log", default=str(OUT_DIR / "calibration_generations.csv"))
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--exclude-archetype", default=None,
                       help="leave-one-archetype-out CV: fit with this archetype's real matchups held out")
  args = parser.parse_args()

  decks = load_decks()
  reps, scores = pick_representatives(decks)
  real_pairs, skill_archetypes, real_matrix = build_matchup_lists(reps, args.exclude_archetype)
  print(f"{len(reps)} archetypes, {len(real_pairs)} real matchup pairs"
        + (f" (excluding {args.exclude_archetype})" if args.exclude_archetype else "")
        + f", {len(skill_archetypes)} skill-floor checks")

  run_matchups = run_matchups_ssh if args.backend == "ssh" else run_matchups_local
  baseline_skill = compute_baseline_skill(reps, skill_archetypes, args.cores, run_matchups)
  print("baseline (default weights) skill vs RandomAction:", baseline_skill)

  best_weights, best_loss = run_cma_es(
    reps, real_pairs, real_matrix, skill_archetypes, baseline_skill, DEFAULT_WEIGHTS,
    args.lambda_reg, args.lambda_skill, args.cores, run_matchups,
    args.sigma0, args.max_generations, args.popsize, args.log)

  OUT_DIR.mkdir(parents=True, exist_ok=True)
  with open(args.out, "w", encoding="utf-8") as f:
    json.dump({"weights": best_weights, "loss": best_loss, "default_weights": DEFAULT_WEIGHTS}, f, indent=2)
  print(f"best loss: {best_loss:.3f}")
  print(f"wrote {args.out}")


if __name__ == "__main__":
  main()
