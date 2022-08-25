from random import choice, random
from copy import deepcopy


class GreedyAction():
  def mulligan_rule(card):
    return card.card_details['mana'] < 3
  
  def choose_action(state):
    available_actions = state.get_available_actions(state.current_player)
    possible_stats = []
    for next_action in range(len(available_actions)):
      possible_state = deepcopy(state)
      turn_passed = possible_state.perform_action(possible_state.get_available_actions(possible_state.current_player)[next_action])
      state_score = GreedyAction.get_score(possible_state)
      possible_stats.append((possible_state, state_score, turn_passed))
    new_state = sorted(possible_stats, key=lambda x: x[1])[0]
    return new_state[0], new_state[2]

  def get_score(possible_state):
    hp = possible_state.current_player.card_details['health']
    enemy_hp = possible_state.current_player.other_player.card_details['health']
    return hp - enemy_hp

class RandomAction():
  def mulligan_rule(card):
    return card.card_details['mana'] < 3
  
  def choose_action(actions):
    return choice(actions)