from random import choice, random
from copy import deepcopy
from enums import Actions
import time
import _pickle as cPickle

class GreedyAction():
  def mulligan_rule(card):
    return card.mana < 3
  
  def choose_action(state):
    available_actions = state.get_available_actions(state.current_player)
    # print(available_actions)
    possible_actions = []
    for action_index in range(len(available_actions)):
      possible_state = cPickle.loads(cPickle.dumps(state, -1))
      # possible_state = deepcopy(state)
      turn_passed = possible_state.perform_action(possible_state.get_available_actions(possible_state.current_player)[action_index])

      state_score = GreedyAction.get_score(possible_state, turn_passed) #must get before passing turn
      possible_actions.append((action_index, state_score, turn_passed))
    best_action = sorted(possible_actions, key=lambda x: x[1])[-1]

    state.perform_action(available_actions[best_action[0]])
    return best_action[2]

  def get_score(possible_state, turn_passed):
    if turn_passed:
      return -100
    hp = possible_state.current_player.health
    enemy_hp = possible_state.current_player.other_player.health
    return hp - enemy_hp

class RandomAction():
  def mulligan_rule(card):
    return card.mana < 3
  
  def choose_action(state):
    chosen_action = choice(state.get_available_actions(state.current_player))
    turn_passed = state.perform_action(chosen_action)
    if turn_passed:
      state.current_player = state.current_player.other_player
    return turn_passed

class RandomNoEarlyPassing():
  def mulligan_rule(card):
    return card.mana < 3
  
  def choose_action(state):
    all_available_actions = state.get_available_actions(state.current_player)

    available_actions_without_ending = list(filter(lambda x: x.action_type != Actions.END_TURN, all_available_actions))

    if len(available_actions_without_ending) > 0:
      chosen_action = choice(available_actions_without_ending)
    else:
      chosen_action = all_available_actions[0]

    turn_passed = state.perform_action(chosen_action)
    if turn_passed:
      state.current_player = state.current_player.other_player
    return turn_passed