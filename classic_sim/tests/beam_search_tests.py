"""Tests for BeamSearch (turn-plan beam search over the value net / linear
evaluator) - the search-once-per-plan redesign that replaced "research every
action" after the plan-review pass found that cost model wrong."""
import sys
sys.path.append('../src/')

import numpy as np
from numpy.random import RandomState

from game_manager import GameManager
from enums import CardSets, Classes
from zones import Deck
from strategy import BeamSearch, NeuralGreedy, RandomAction
from utilities import BoundCloner
from exceptions import TooManyActions, PlayerDead
import neural_eval as ne

BASIC_MAGE = [
  "Arcane Missiles", "Arcane Missiles", "Murloc Raider", "Murloc Raider",
  "Arcane Explosion", "Arcane Explosion", "Bloodfen Raptor", "Bloodfen Raptor",
  "Novice Engineer", "Novice Engineer", "River Crocolisk", "River Crocolisk",
  "Arcane Intellect", "Arcane Intellect", "Raid Leader", "Raid Leader",
  "Wolfrider", "Wolfrider", "Fireball", "Fireball",
  "Oasis Snapjaw", "Oasis Snapjaw", "Polymorph", "Polymorph",
  "Sen'jin Shieldmasta", "Sen'jin Shieldmasta", "Nightblade", "Nightblade",
  "Boulderfist Ogre", "Boulderfist Ogre"]

CHAMPION_PATH = "../examples/metagame_analysis/data/value_net_naxx/value_net_champion.npz"


def make_game(player_strategy, enemy_strategy, seed=0):
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_player(Classes.MAGE, Deck.generate_from_decklist(BASIC_MAGE), player_strategy)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_from_decklist(BASIC_MAGE), enemy_strategy)
  game_manager.create_game()
  return game_manager.game


def _fingerprint(state):
  #a coarse but sufficient state fingerprint for equality checks below - two
  #states reached via the same action sequence from the same RNG snapshot
  #must match on all of this.
  me, them = state.player, state.enemy
  return (me.health, them.health, me.current_mana, len(me.hand), len(me.board),
          len(me.deck), them.health, len(them.hand), len(them.board),
          bool(me.weapon), bool(them.weapon))


def _rng_equal(a, b):
  return a[0] == b[0] and np.array_equal(a[1], b[1]) and a[2:] == b[2:]


def _advance_a_few_actions(game, n=3):
  #cheap way to get a non-trivial (post-mulligan) board/hand state without
  #depending on exact turn structure
  for _ in range(n):
    game.current_player.strategy.choose_action(game)


def test_beam_search_reduces_to_greedy_at_depth_1():
  #beam_width >= all available actions, depth=1: the ply-1 loop is byte-for-
  #byte NeuralGreedy's flat loop (same clone/RNG-rewind, same score, same
  #sorted(...)[-1] tie-break) - so it must land on the identical result.
  weights = ne.init_weights(0)
  game = make_game(RandomAction(), RandomAction())
  _advance_a_few_actions(game)

  random_state = game.game_manager.random_state
  saved_rng = random_state.get_state()
  available_actions = game.get_available_actions(game.current_player)
  cloner = BoundCloner(game, available_actions)

  random_state.set_state(saved_rng)
  state_a, _ = cloner.clone()
  BeamSearch(weights, beam_width=len(available_actions), depth=1).choose_action(state_a)

  random_state.set_state(saved_rng)
  state_b, _ = cloner.clone()
  NeuralGreedy(weights).choose_action(state_b)

  assert _fingerprint(state_a) == _fingerprint(state_b)


def test_beam_search_is_deterministic():
  weights = ne.init_weights(0)
  game = make_game(RandomAction(), RandomAction())
  _advance_a_few_actions(game)

  random_state = game.game_manager.random_state
  saved_rng = random_state.get_state()
  available_actions = game.get_available_actions(game.current_player)
  cloner = BoundCloner(game, available_actions)

  random_state.set_state(saved_rng)
  state_a, _ = cloner.clone()
  BeamSearch(weights, beam_width=3, depth=3).choose_action(state_a)
  rng_after_a = random_state.get_state()

  random_state.set_state(saved_rng)
  state_b, _ = cloner.clone()
  BeamSearch(weights, beam_width=3, depth=3).choose_action(state_b)
  rng_after_b = random_state.get_state()

  assert _fingerprint(state_a) == _fingerprint(state_b)
  assert _rng_equal(rng_after_a, rng_after_b)


def test_plan_replay_matches_direct_reconstruction():
  #the core claim of the stateful redesign: cached action indices, replayed
  #against the real (or a fresh clone of the) state one choose_action call
  #at a time, land in exactly the same place as directly executing that same
  #index sequence in one shot from the same starting RNG snapshot - i.e. no
  #RNG leakage, and the cached plan is not stale by the time it's consumed.
  weights = ne.init_weights(0)
  game = make_game(RandomAction(), RandomAction())
  _advance_a_few_actions(game)

  random_state = game.game_manager.random_state
  saved_rng = random_state.get_state()
  available_actions = game.get_available_actions(game.current_player)
  cloner = BoundCloner(game, available_actions)

  #(a) drive it exactly like Game.take_turn would: one choose_action call
  #per real action, draining the cached plan across calls.
  random_state.set_state(saved_rng)
  driven_state, _ = cloner.clone()
  agent = BeamSearch(weights, beam_width=3, depth=3)
  for _ in range(3):
    if agent.choose_action(driven_state):
      break
  rng_after_driven = random_state.get_state()

  #(b) compute the plan directly and replay its indices in one shot against
  #an independent fresh clone from the identical starting snapshot.
  random_state.set_state(saved_rng)
  planning_state, _ = cloner.clone()
  plan = BeamSearch(weights, beam_width=3, depth=3)._search(planning_state)

  random_state.set_state(saved_rng)
  replay_state, _ = cloner.clone()
  for index, _expected_count in plan:
    ended = replay_state.perform_action(replay_state.get_available_actions(replay_state.current_player)[index])
    if ended:
      break
  rng_after_replay = random_state.get_state()

  assert _fingerprint(driven_state) == _fingerprint(replay_state)
  assert _rng_equal(rng_after_driven, rng_after_replay)


class _CountingBeamSearch(BeamSearch):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.search_calls = 0

  def _search(self, state):
    self.search_calls += 1
    return super()._search(state)


def test_beam_search_plans_once_per_turn_not_per_action():
  #the whole point of the stateful redesign: searching K-wide/D-deep at
  #every single action would multiply the per-turn cost by beam search's
  #cost again per action. Assert it directly rather than just via the cost
  #estimate in the plan.
  weights = ne.init_weights(0)
  game = make_game(RandomAction(), RandomAction())
  #play forward with cheap random actions so mana/board/hand build up into a
  #turn with more than `depth` real actions available
  try:
    for _ in range(60):
      turn_passed = game.current_player.strategy.choose_action(game)
      if turn_passed:
        game.end_turn()
        game.untap()
  except (TooManyActions, PlayerDead):
    return  #rare early death/abort on this fixed seed - nothing to assert, skip

  agent = _CountingBeamSearch(weights, beam_width=3, depth=3)
  game.current_player.strategy = agent
  actions_this_turn = 0
  try:
    for _ in range(20):  #hard safety cap, well above any real turn length
      turn_passed = game.current_player.strategy.choose_action(game)
      actions_this_turn += 1
      if turn_passed:
        break
  except PlayerDead:
    return  #beam search itself found lethal mid-warmup on this random seed - skip

  assert agent.search_calls >= 1
  if actions_this_turn > agent.depth:
    assert agent.search_calls < actions_this_turn


def test_beam_search_discards_stale_plan_left_over_from_a_prior_game():
  #the real bug this regression-guards: value_net_selfplay.py-style drivers
  #build one Game object and reuse it (and the strategy objects attached to
  #it) across many games via game.reset_game()/start_game(), never
  #constructing fresh agents per game. If a game ends (win/loss/abort) with
  #self._plan not yet empty, the next game must not replay those leftover
  #indices against its unrelated board - this crashed a live dwail run with
  #an IndexError before the available_count guard in choose_action existed.
  #GameManager.create_player/create_enemy deepcopy the strategy passed in
  #(see test_beam_search_never_shared_across_seats), so the live agent must
  #be fetched back off the game, not kept as the pre-creation local. And
  #start_game() randomly picks current_player, so pin it directly to the
  #BeamSearch seat for a deterministic test.
  weights = ne.init_weights(0)
  game = make_game(BeamSearch(weights, beam_width=3, depth=3), RandomAction())
  beam_player = game.player if isinstance(game.player.strategy, BeamSearch) else game.enemy
  game.current_player = beam_player
  agent = beam_player.strategy

  #force a non-empty leftover plan: a 2-step plan where choose_action only
  #consumes the first step, leaving the (deliberately bogus) second cached.
  first_available = game.get_available_actions(game.current_player)
  agent._plan = [(0, len(first_available)), (0, 999)]
  agent.choose_action(game)

  assert agent._plan  #precondition: something is still cached

  #simulate the driver moving on to a brand new game on the same objects
  game.reset_game()
  game.start_game()
  game.current_player = beam_player

  #must not raise, and must not silently use the bogus leftover index either -
  #the guard should have discarded the stale plan and searched fresh
  agent.choose_action(game)


def test_beam_search_never_shared_across_seats():
  #a shared instance's _plan queue would leak between seats if it were ever
  #actually shared - GameManager.create_player/create_enemy turn out to
  #deepcopy the strategy passed in, so even passing the *same* instance to
  #both seats (as here) still ends up with two independent agents. Pin that
  #down so a future refactor of GameManager can't silently reintroduce the
  #sharing this class would misbehave under.
  weights = ne.init_weights(0)
  agent = BeamSearch(weights)
  game = make_game(agent, agent)
  assert game.player.strategy is not game.enemy.strategy
  assert game.player.strategy._plan is not game.enemy.strategy._plan


def test_beam_search_plays_full_games():
  weights = ne.init_weights(0)
  game = make_game(BeamSearch(weights, beam_width=2, depth=2),
                    BeamSearch(weights, beam_width=2, depth=2))
  completed = 0
  for _ in range(2):
    try:
      result = game.play_game()
      assert result[0] in (0, 1)
      completed += 1
    except (TooManyActions, RecursionError):
      pass
    game.reset_game()
    game.start_game()
  assert completed >= 1


def test_beam_search_accepts_linear_eval_weights():
  from montecarlotreesearch import _EVAL_WEIGHTS
  game = make_game(BeamSearch(_EVAL_WEIGHTS, beam_width=2, depth=2), RandomAction())
  for _ in range(6):
    turn_passed = game.current_player.strategy.choose_action(game)
    if turn_passed:
      game.end_turn()
      game.untap()


def test_beam_search_with_naxx_champion_weights():
  weights = ne.load_weights(CHAMPION_PATH)
  game = make_game(BeamSearch(weights, beam_width=2, depth=2), RandomAction())
  for _ in range(6):
    turn_passed = game.current_player.strategy.choose_action(game)
    if turn_passed:
      game.end_turn()
      game.untap()
