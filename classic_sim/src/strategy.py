from copy import deepcopy
from enums import Actions, Attributes
import time
import _pickle as cPickle
from exceptions import PlayerDead

from montecarlotreesearch import MonteCarloTreeSearchNode

class MCTS():
  def mulligan_rule(self, card):
    return card.get_manacost() < 4


class GreedyAction():
  def mulligan_rule(self, card):
    return card.get_manacost() < 4
  def choose_action(self, state):
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

      state_score = self.get_score(possible_state, turn_passed, game_state) #must get before passing turn

      possible_actions.append((action_index, state_score, turn_passed))
    best_action = sorted(possible_actions, key=lambda x: x[1])[-1]
    state.perform_action(available_actions[best_action[0]])


    return best_action[2]

  def get_score(self, possible_state, turn_passed, game_state):
    if game_state == -1:
      return -1000
    elif game_state == 1:
      return 1000
    if turn_passed:
      return -100
    hp = possible_state.current_player.health
    enemy_hp = possible_state.current_player.other_player.health
    return hp - enemy_hp

class GreedyActionSmartv1():
  def mulligan_rule(self, card):
    return card.get_manacost() < 4
  def choose_action(self, state):
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

      state_score = self.get_score(possible_state, turn_passed, game_state) #must get before passing turn

      possible_actions.append((action_index, state_score, turn_passed))
    best_action = sorted(possible_actions, key=lambda x: x[1])[-1]
    # print("v1: " + str(available_actions[best_action[0]]))

    state.perform_action(available_actions[best_action[0]])
    return best_action[2]

  def get_score(self, possible_state, turn_passed, game_state):
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

class GreedyActionSmart():
  def __init__(self, weights = [-1, 10, -10, 10, 10, 1, 1, 1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, 1, 1]):
    self.weights = weights
  def mulligan_rule(self, card):
    return card.get_manacost() < 4
  def choose_action(self, state):
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

      state_score = self.get_score(possible_state, turn_passed, game_state) #must get before passing turn

      possible_actions.append((action_index, state_score, turn_passed))

    best_action = sorted(possible_actions, key=lambda x: x[1])[-1]
    print("gas: " + str(available_actions[best_action[0]]))
    state.perform_action(available_actions[best_action[0]])
    return best_action[2]

  def get_score(self, possible_state, turn_passed, game_state):
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

    total_minion_attack = sum([minion.get_attack() for minion in possible_state.current_player.board])
    total_enemy_minion_attack = sum([minion.get_attack() for minion in possible_state.current_player.other_player.board])
    total_minion_attack_difference = total_minion_attack - total_enemy_minion_attack

    total_minion_health = sum([minion.get_health() for minion in possible_state.current_player.board])
    total_enemy_minion_health = sum([minion.get_health() for minion in possible_state.current_player.other_player.board])
    total_minion_health_difference = total_minion_health - total_enemy_minion_health

    num_minions_with_taunt = sum([1 if minion.has_attribute(Attributes.TAUNT) else 0 for minion in possible_state.current_player.board])
    num_enemy_minions_with_taunt = sum([1 if minion.has_attribute(Attributes.TAUNT) else 0 for minion in possible_state.current_player.other_player.board])
    
    num_minions_with_divine_shield = sum([1 if minion.has_attribute(Attributes.DIVINE_SHIELD) else 0 for minion in possible_state.current_player.board])
    num_enemy_minions_with_divine_shield = sum([1 if minion.has_attribute(Attributes.DIVINE_SHIELD) else 0 for minion in possible_state.current_player.other_player.board])
    
    num_minions_with_lifesteal = sum([1 if minion.has_attribute(Attributes.LIFESTEAL) else 0 for minion in possible_state.current_player.board])
    num_enemy_minions_with_lifesteal = sum([1 if minion.has_attribute(Attributes.LIFESTEAL) else 0 for minion in possible_state.current_player.other_player.board])
    
    num_minions_with_spell_damage = sum([1 if minion.has_attribute(Attributes.SPELL_DAMAGE) else 0 for minion in possible_state.current_player.board])
    num_enemy_minions_with_spell_damage = sum([1 if minion.has_attribute(Attributes.SPELL_DAMAGE) else 0 for minion in possible_state.current_player.other_player.board])
    
    other_positive_attributes = [Attributes.CHARGE, Attributes.STEALTH, Attributes.WINDFURY, Attributes.HEXPROOF, Attributes.POISONOUS, Attributes.IMMUNE, Attributes.FREEZER]
    num_other_positive_attributes = sum([sum([1 if minion.has_attribute(attribute) else 0 for minion in possible_state.current_player.board]) for attribute in other_positive_attributes])
    num_other_enemy_positive_attributes = sum([sum([1 if minion.has_attribute(attribute) else 0 for minion in possible_state.current_player.other_player.board]) for attribute in other_positive_attributes])

    num_cards_in_hand = len(possible_state.current_player.hand)
    num_enemy_cards_in_hand = len(possible_state.current_player.other_player.hand)
    num_cards_in_hand_difference = num_cards_in_hand - num_enemy_cards_in_hand

    num_cards_in_library = len(possible_state.current_player.deck)
    num_enemy_cards_in_library = len(possible_state.current_player.other_player.deck)
    num_cards_in_library_difference = num_cards_in_library - num_enemy_cards_in_library

    num_cards_in_secrets_zone = len(possible_state.current_player.secrets_zone)
    num_enemy_cards_in_secrets_zone = len(possible_state.current_player.other_player.secrets_zone)
    num_cards_in_secrets_zone_difference = num_cards_in_secrets_zone - num_enemy_cards_in_secrets_zone

    #-0.1, 
    #1, -1, 1, 1
    #2, 2, 1.5,
    #3, -3, 
    #1, -1
    #1, -1
    #1, -1
    #1, -1
    #-1, 0, 1
    feature_vector = [turn_passed, 
                      hp, enemy_hp, health_difference, armor_difference, 
                      num_minions_difference, total_minion_attack_difference, total_minion_health_difference,
                      num_minions_with_taunt, num_enemy_minions_with_taunt,
                      num_minions_with_divine_shield, num_enemy_minions_with_divine_shield,
                      num_minions_with_lifesteal, num_enemy_minions_with_lifesteal,
                      num_minions_with_spell_damage, num_enemy_minions_with_spell_damage,
                      num_other_positive_attributes, num_other_enemy_positive_attributes,
                      num_cards_in_hand_difference, num_cards_in_library_difference, num_cards_in_secrets_zone_difference]

    return sum(feature*weight for feature, weight in zip(feature_vector, self.weights))
  
class RandomAction():
  def mulligan_rule(self, card):
    return card.get_manacost() < 3
  
  def choose_action(self, state):
    chosen_action = state.game_manager.random_state.choice(state.get_available_actions(state.current_player))
    turn_passed = state.perform_action(chosen_action)
    return turn_passed

class RandomNoEarlyPassing():
  def mulligan_rule(self, card):
    return card.get_manacost() < 3
  
  def choose_action(self, state):
    all_available_actions = state.get_available_actions(state.current_player)
    available_actions_without_ending = list(filter(lambda x: x.action_type != Actions.END_TURN, all_available_actions))

    if len(available_actions_without_ending) > 0:
      chosen_action = state.game_manager.random_state.choice(available_actions_without_ending)
    else:
      chosen_action = all_available_actions[0]

    turn_passed = state.perform_action(chosen_action)
    return turn_passed