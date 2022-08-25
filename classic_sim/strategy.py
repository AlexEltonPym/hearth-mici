from random import choice
from copy import deepcopy


class GreedyAction():
  def mulligan_rule(card):
    return card.card_details['mana'] < 3
  
  def choose_action(state):
    new_state = deepcopy(state)
    available_actions = new_state.get_available_actions(new_state.current_player)
    next_action = choice(available_actions)
    # print(next_action)
    new_state, turn_passed = new_state.perform_action(next_action)
    return new_state, turn_passed

class RandomAction():
  def mulligan_rule(card):
    return card.card_details['mana'] < 3
  
  def choose_action(actions):
    return choice(actions)