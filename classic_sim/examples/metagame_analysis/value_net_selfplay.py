"""Self-play game generation with state sampling, for value-net training.

Shared by the local driver (train_value_net.py) and the dwail worker
(value_net_remote_worker.py). Work items are plain tuples so they survive the
dill-over-stdin round trip; the first element is the kind:

  ("generate", deck_a, class_a, deck_b, class_b, spec_a, spec_b, world,
   n_games, sample_rate, epsilon, seed)
      -> {"samples": {stacked padded arrays}, "games": n, "wins_a": n}
  ("ladder", deck_a, class_a, deck_b, class_b, spec_a, spec_b, world,
   n_games, seed)
      -> win rate for side a (float)

An agent spec is ("linear", weights_list) for GreedyActionSmart or
("net", weights_dict) for NeuralGreedy - specs, not strategy objects, so the
payload stays small and torch never has to exist on the workers.

Sampling design: a recorded sample is the acting player's view of the state
at a decision point (their own hand, opponent's counts - no oracle features),
and its training target is the game's final outcome for that player (+1/-1),
i.e. plain Monte Carlo value targets a la DouZero. Exploration comes from
epsilon-random actions (never epsilon on ladder games); aborted games
(action-cap/recursion) contribute no samples since they have no outcome.
"""
import sys
from pathlib import Path
from random import Random

sys.path.append('../../src')
import numpy as np

from game_manager import GameManager
from strategy import GreedyActionSmart, NeuralGreedy, MCTS
from zones import Deck
from enums import Classes, CardSets, Actions
from exceptions import PlayerDead, TooManyActions
from card_sets import SEPT_2014_NERF_PATCHES
import neural_eval as ne

CLASS_ENUM = {"HUNTER": Classes.HUNTER, "MAGE": Classes.MAGE, "WARRIOR": Classes.WARRIOR}
CLASSIC_SETS = {
  "HUNTER": [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER],
  "MAGE": [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE],
  "WARRIOR": [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR],
}
NAXX_SETS = {
  "HUNTER": [CardSets.CLASSIC_NEUTRAL, CardSets.NAXX_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.NAXX_HUNTER],
  "MAGE": [CardSets.CLASSIC_NEUTRAL, CardSets.NAXX_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.NAXX_MAGE],
  "WARRIOR": [CardSets.CLASSIC_NEUTRAL, CardSets.NAXX_NEUTRAL, CardSets.CLASSIC_WARRIOR, CardSets.NAXX_WARRIOR],
}
#world -> (per-class sets, patches): the training world for this phase is
#pre_naxx (user decision: Naxx cards stay unseen so the later integration
#step is a true generalization test); the other worlds exist for that step
WORLDS = {
  "pre_naxx": (CLASSIC_SETS, None),
  "naxx": (NAXX_SETS, None),
  "naxx_nerfed": (NAXX_SETS, SEPT_2014_NERF_PATCHES),
}

ACTION_CAP = 600  #per game; mirrors the engine's TooManyActions guard


def make_agent(spec):
  kind, payload = spec
  if kind == "linear":
    return GreedyActionSmart(list(payload))
  if kind == "net":
    return NeuralGreedy(payload)
  if kind == "mcts":
    #payload = (eval_weights, iterations[, rollout_turn_limit]); guided MCTS
    #with the net (dict) or linear features (26-long list - callers must strip
    #the turn_passed weight) as leaf evaluator. rollout_turn_limit=0 skips
    #rollouts entirely (AlphaZero-style pure leaf eval) - the right mode for
    #a trained net, whose training states never included random-rollout
    #futures. For ladder items only, ~60x the per-game cost of greedy.
    eval_weights, iterations = payload[0], payload[1]
    rollout_limit = payload[2] if len(payload) > 2 else 6
    return MCTS(iterations=iterations, guided=True, eval_weights=eval_weights,
                rollout_turn_limit=rollout_limit)
  raise ValueError(f"unknown agent spec kind {kind!r}")


def make_game(deck_a, class_a, deck_b, class_b, world, spec_a, spec_b):
  sets, patches = WORLDS[world]
  game_manager = GameManager()
  game_manager.create_player_pool(sets[class_a], card_patches=patches)
  game_manager.create_enemy_pool(sets[class_b], card_patches=patches)
  game_manager.create_player(CLASS_ENUM[class_a], Deck.generate_from_decklist(deck_a), make_agent(spec_a))
  game_manager.create_enemy(CLASS_ENUM[class_b], Deck.generate_from_decklist(deck_b), make_agent(spec_b))
  game_manager.create_game()
  return game_manager.game


def play_recorded_game(game, rng, sample_rate, epsilon):
  """Play one game with the players' own strategies, optionally recording
  sampled decision states. Returns (winner_name_or_None, pending) where
  pending is [(padded_blocks, acting_player_name)]. winner None = aborted."""
  pending = []
  actions_taken = 0
  try:
    while True:
      if actions_taken >= ACTION_CAP:
        return None, []
      me = game.current_player
      if sample_rate and rng.random() < sample_rate:
        pending.append((ne.encode_state_padded(game, me), me.name))
      if epsilon and rng.random() < epsilon:
        available = game.get_available_actions(me)
        non_end = [a for a in available if a.action_type != Actions.END_TURN]
        chosen = non_end[rng.randrange(len(non_end))] if non_end else available[-1]
        turn_passed = game.perform_action(chosen)
      else:
        turn_passed = me.strategy.choose_action(game)
      actions_taken += 1
      if turn_passed:
        game.end_turn()
        game.untap()
  except (TooManyActions, RecursionError):
    return None, []
  except PlayerDead:
    if game.player.health <= 0 and game.enemy.health <= 0:
      return None, []
    winner = "player" if game.enemy.health <= 0 else "enemy"
    return winner, pending


def generate_games(deck_a, class_a, deck_b, class_b, spec_a, spec_b, world,
                   n_games, sample_rate, epsilon, seed):
  game = make_game(deck_a, class_a, deck_b, class_b, world, spec_a, spec_b)
  rng = Random(seed)
  blocks = {"my_board": [], "their_board": [], "hand": [], "globals": [], "counts": [], "target": []}
  games_completed, wins_a = 0, 0
  for _ in range(n_games):
    winner, pending = play_recorded_game(game, rng, sample_rate, epsilon)
    if winner is not None:
      games_completed += 1
      wins_a += 1 if winner == "player" else 0
      for (my_board, their_board, hand, globals_vec, counts), side in pending:
        blocks["my_board"].append(my_board)
        blocks["their_board"].append(their_board)
        blocks["hand"].append(hand)
        blocks["globals"].append(globals_vec)
        blocks["counts"].append(counts)
        blocks["target"].append(1.0 if side == winner else -1.0)
    game.reset_game()
    game.start_game()

  samples = None
  if blocks["target"]:
    samples = {
      "my_board": np.stack(blocks["my_board"]),
      "their_board": np.stack(blocks["their_board"]),
      "hand": np.stack(blocks["hand"]),
      "globals": np.stack(blocks["globals"]),
      "counts": np.stack(blocks["counts"]),
      "target": np.array(blocks["target"], dtype=np.float32),
    }
  return {"samples": samples, "games": games_completed, "wins_a": wins_a}


def play_ladder_matchup(deck_a, class_a, deck_b, class_b, spec_a, spec_b, world, n_games, seed):
  game = make_game(deck_a, class_a, deck_b, class_b, world, spec_a, spec_b)
  rng = Random(seed)
  wins, played = 0, 0
  for _ in range(n_games):
    winner, _ = play_recorded_game(game, rng, sample_rate=0.0, epsilon=0.0)
    if winner is not None:
      played += 1
      wins += 1 if winner == "player" else 0
    game.reset_game()
    game.start_game()
  return wins / played if played else 0.5


def run_item(item):
  kind = item[0]
  if kind == "generate":
    return generate_games(*item[1:])
  if kind == "ladder":
    return play_ladder_matchup(*item[1:])
  raise ValueError(f"unknown work item kind {kind!r}")


def concatenate_samples(results):
  """Merge the sample dicts from many generate-results into one array bundle
  (or None if nothing was recorded)."""
  bundles = [r["samples"] for r in results if r.get("samples")]
  if not bundles:
    return None
  return {key: np.concatenate([bundle[key] for bundle in bundles]) for key in bundles[0]}
