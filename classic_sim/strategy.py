from random import choice, random
from copy import deepcopy


class GreedyAction():
  def mulligan_rule(card):
    return card.card_details['mana'] < 3
  
  def choose_action(state):
    available_actions = state.get_available_actions(state.current_player)
    possible_actions = []
    for action_index in range(len(available_actions)):
      possible_state = deepcopy(state)
      turn_passed = possible_state.perform_action(possible_state.get_available_actions(possible_state.current_player)[action_index])
      state_score = GreedyAction.get_score(possible_state, turn_passed) #must get before passing turn
      if turn_passed:
        possible_state.current_player = possible_state.current_player.other_player
      possible_actions.append((action_index, state_score, turn_passed))
    best_action = sorted(possible_actions, key=lambda x: x[1])[-1]
    print(available_actions[best_action[0]])
    state.perform_action(available_actions[best_action[0]])
    return best_action[2]

  def get_score(possible_state, turn_passed):
    if turn_passed:
      return -100
    hp = possible_state.current_player.card_details['health']
    enemy_hp = possible_state.current_player.other_player.card_details['health']
    return hp - enemy_hp

class RandomAction():
  def mulligan_rule(card):
    return card.card_details['mana'] < 3
  
  def choose_action(state):
    chosen_action = choice(state.get_available_actions(state.current_player))
    turn_passed = state.perform_action(chosen_action)
    # print(chosen_action)
    if turn_passed:
      state.current_player = state.current_player.other_player
    return turn_passed