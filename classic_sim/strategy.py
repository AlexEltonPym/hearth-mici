from copy import deepcopy
from enums import Actions
import time
import _pickle as cPickle
from game import PlayerDead

class GreedyAction():
  def mulligan_rule(card):
    return card.get_manacost() < 4
  def choose_action(state):
    available_actions = state.get_available_actions(state.current_player)
    possible_actions = []
    for action_index in range(len(available_actions)):
      possible_state = cPickle.loads(cPickle.dumps(state, -1))
      try:
        turn_passed = possible_state.perform_action(possible_state.get_available_actions(possible_state.current_player)[action_index])
        game_state = 0
      except PlayerDead:
        turn_passed = 0
        if possible_state.current_player.health <= 0:
          game_state = -1
        else:
          game_state = 1

      state_score = GreedyAction.get_score(possible_state, turn_passed, game_state) #must get before passing turn

      possible_actions.append((action_index, state_score, turn_passed))
    best_action = sorted(possible_actions, key=lambda x: x[1])[-1]
    state.perform_action(available_actions[best_action[0]])


    return best_action[2]

  def get_score(possible_state, turn_passed, game_state):
    if game_state == -1:
      return -1000
    elif game_state == 1:
      return 1000
    if turn_passed:
      return -100
    hp = possible_state.current_player.health
    enemy_hp = possible_state.current_player.other_player.health
    return hp - enemy_hp

class GreedyActionSmart():
  def mulligan_rule(card):
    return card.get_manacost() < 4
  def choose_action(state):
    available_actions = state.get_available_actions(state.current_player)
    possible_actions = []
    for action_index in range(len(available_actions)):
      possible_state = cPickle.loads(cPickle.dumps(state, -1))
      try:
        turn_passed = possible_state.perform_action(possible_state.get_available_actions(possible_state.current_player)[action_index])
        game_state = 0
      except PlayerDead:
        turn_passed = 0
        if possible_state.current_player.health <= 0:
          game_state = -1
        else:
          game_state = 1

      state_score = GreedyActionSmart.get_score(possible_state, turn_passed, game_state) #must get before passing turn

      possible_actions.append((action_index, state_score, turn_passed))
    best_action = sorted(possible_actions, key=lambda x: x[1])[-1]
    state.perform_action(available_actions[best_action[0]])
    return best_action[2]

  def get_score(possible_state, turn_passed, game_state):
    if game_state == -1:
      return -1000
    elif game_state == 1:
      return 1000

    turn_passed = 1 if turn_passed else 0

    hp = possible_state.current_player.health
    enemy_hp = possible_state.current_player.other_player.health
    health_difference = hp - enemy_hp

    armor = possible_state.current_player.armor
    enemy_armor = possible_state.current_player.other_player.armor
    armor_difference = armor - enemy_armor


    num_minions = len(possible_state.current_player.board)
    enemy_num_minions = len(possible_state.current_player.other_player.board)
    num_minions_difference = num_minions - enemy_num_minions

    total_minion_health = sum([minion.get_health() for minion in possible_state.current_player.board])
    total_enemy_minion_health = sum([minion.get_health() for minion in possible_state.current_player.other_player.board])
    total_minion_health_difference = total_minion_health - total_enemy_minion_health

    return turn_passed * -1 + health_difference * 10 + armor_difference + num_minions_difference + total_minion_health_difference



class RandomAction():
  def mulligan_rule(card):
    return card.get_manacost() < 3
  
  def choose_action(state):
    chosen_action = state.game_manager.random_state.choice(state.get_available_actions(state.current_player))
    turn_passed = state.perform_action(chosen_action)
    return turn_passed

class RandomNoEarlyPassing():
  def mulligan_rule(card):
    return card.get_manacost() < 3
  
  def choose_action(state):
    all_available_actions = state.get_available_actions(state.current_player)
    available_actions_without_ending = list(filter(lambda x: x.action_type != Actions.END_TURN, all_available_actions))

    if len(available_actions_without_ending) > 0:
      chosen_action = state.game_manager.random_state.choice(available_actions_without_ending)
    else:
      chosen_action = all_available_actions[0]

    turn_passed = state.perform_action(chosen_action)
    return turn_passed