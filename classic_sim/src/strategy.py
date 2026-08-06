from copy import deepcopy
from enums import Actions, Attributes
import time
import _pickle as cPickle
from exceptions import PlayerDead
from utilities import clone_with_action, BoundCloner

from montecarlotreesearch import MonteCarloTreeSearchNode

class MCTS():
  def __init__(self, iterations=50, c_param=1.4, rollout_turn_limit=6, guided=False, eval_weights=None):
    self.iterations = iterations
    self.c_param = c_param
    self.rollout_turn_limit = rollout_turn_limit
    self.guided = guided #no-early-pass rollouts + feature evaluation at rollout cutoff
    self.eval_weights = eval_weights #None -> montecarlotreesearch's own default (the hand-tuned weights)

  def mulligan_rule(self, card):
    return card.get_manacost() < 4

  def choose_action(self, state):
    root = MonteCarloTreeSearchNode(state)
    if len(root.available_actions) == 1:
      return state.perform_action(root.available_actions[0])

    kwargs = {} if self.eval_weights is None else {"eval_weights": self.eval_weights}
    best_child = root.best_action(state.game_manager.random_state, self.iterations, self.c_param, self.rollout_turn_limit, self.guided, **kwargs)
    #root.available_actions reference this state's objects, so applying directly is safe
    return state.perform_action(root.available_actions[best_child.parent_action_index])


class GreedyAction():
  def mulligan_rule(self, card):
    return card.get_manacost() < 4
  def choose_action(self, state):
    available_actions = state.get_available_actions(state.current_player)
    cloner = BoundCloner(state, available_actions)
    #clones share the live random_state (cloning it is the expensive part of
    #the pickle round-trip - see utilities._stripped_dump). Without rewinding
    #it between candidates, each candidate's random draws (e.g. random-target
    #cards) would bleed into the next candidate's evaluation, and the whole
    #lookahead loop's draws would bleed into the real action actually
    #performed below. get_state/set_state are cheap (a tuple copy, no
    #generator reconstruction) so this keeps evaluation deterministic and
    #the real game's RNG stream uncontaminated by discarded candidates.
    random_state = state.game_manager.random_state
    saved_rng_state = random_state.get_state()
    possible_actions = []
    for action_index in range(len(available_actions)):
      random_state.set_state(saved_rng_state)
      possible_state, cloned_actions = cloner.clone()
      try:
        turn_passed = possible_state.perform_action(cloned_actions[action_index])
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
    random_state.set_state(saved_rng_state)
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
    cloner = BoundCloner(state, available_actions)
    #see GreedyAction.choose_action for why the RNG state is rewound between
    #candidates and before the real action is performed.
    random_state = state.game_manager.random_state
    saved_rng_state = random_state.get_state()
    possible_actions = []
    for action_index in range(len(available_actions)):
      random_state.set_state(saved_rng_state)
      possible_state, cloned_actions = cloner.clone()
      try:
        turn_passed = possible_state.perform_action(cloned_actions[action_index])
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

    random_state.set_state(saved_rng_state)
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
  #the trailing 6 zeros are the additive feature extension's default weights
  #(lethal_margin_mine, lethal_margin_theirs, weapon_durability_difference,
  #fatigue_proximity, hero_power_available_difference, unused_mana) - zero
  #means the default behaves exactly as it did with the original 21 features
  #until calibrate_greedy_weights.py finds better values.
  def __init__(self, weights = [-1, 10, -10, 10, 10, 1, 1, 1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, 1, 1, 0, 0, 0, 0, 0, 0]):
    self.weights = weights
  def mulligan_rule(self, card):
    return card.get_manacost() < 4
  def choose_action(self, state):
    available_actions = state.get_available_actions(state.current_player)
    cloner = BoundCloner(state, available_actions)
    #see GreedyAction.choose_action for why the RNG state is rewound between
    #candidates and before the real action is performed.
    random_state = state.game_manager.random_state
    saved_rng_state = random_state.get_state()
    possible_actions = []
    for action_index in range(len(available_actions)):
      random_state.set_state(saved_rng_state)
      possible_state, cloned_actions = cloner.clone()
      try:
        turn_passed = possible_state.perform_action(cloned_actions[action_index])
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
    # print("gas: " + str(available_actions[best_action[0]]))
    random_state.set_state(saved_rng_state)
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

    #one attribute snapshot per minion instead of one aura scan per (minion, attribute)
    minion_attributes = [minion.get_all_attributes() for minion in possible_state.current_player.board]
    enemy_minion_attributes = [minion.get_all_attributes() for minion in possible_state.current_player.other_player.board]

    num_minions_with_taunt = sum([1 if Attributes.TAUNT in attributes else 0 for attributes in minion_attributes])
    num_enemy_minions_with_taunt = sum([1 if Attributes.TAUNT in attributes else 0 for attributes in enemy_minion_attributes])

    num_minions_with_divine_shield = sum([1 if Attributes.DIVINE_SHIELD in attributes else 0 for attributes in minion_attributes])
    num_enemy_minions_with_divine_shield = sum([1 if Attributes.DIVINE_SHIELD in attributes else 0 for attributes in enemy_minion_attributes])

    num_minions_with_lifesteal = sum([1 if Attributes.LIFESTEAL in attributes else 0 for attributes in minion_attributes])
    num_enemy_minions_with_lifesteal = sum([1 if Attributes.LIFESTEAL in attributes else 0 for attributes in enemy_minion_attributes])

    num_minions_with_spell_damage = sum([1 if Attributes.SPELL_DAMAGE in attributes else 0 for attributes in minion_attributes])
    num_enemy_minions_with_spell_damage = sum([1 if Attributes.SPELL_DAMAGE in attributes else 0 for attributes in enemy_minion_attributes])

    other_positive_attributes = [Attributes.CHARGE, Attributes.STEALTH, Attributes.WINDFURY, Attributes.HEXPROOF, Attributes.POISONOUS, Attributes.IMMUNE, Attributes.FREEZER]
    num_other_positive_attributes = sum([sum([1 if attribute in attributes else 0 for attributes in minion_attributes]) for attribute in other_positive_attributes])
    num_other_enemy_positive_attributes = sum([sum([1 if attribute in attributes else 0 for attributes in enemy_minion_attributes]) for attribute in other_positive_attributes])

    num_cards_in_hand = len(possible_state.current_player.hand)
    num_enemy_cards_in_hand = len(possible_state.current_player.other_player.hand)
    num_cards_in_hand_difference = num_cards_in_hand - num_enemy_cards_in_hand

    num_cards_in_library = len(possible_state.current_player.deck)
    num_enemy_cards_in_library = len(possible_state.current_player.other_player.deck)
    num_cards_in_library_difference = num_cards_in_library - num_enemy_cards_in_library

    num_cards_in_secrets_zone = len(possible_state.current_player.secrets_zone)
    num_enemy_cards_in_secrets_zone = len(possible_state.current_player.other_player.secrets_zone)
    num_cards_in_secrets_zone_difference = num_cards_in_secrets_zone - num_enemy_cards_in_secrets_zone

    #additive extension (Aug 2026): features the original 21 structurally can't
    #express - threshold/interaction effects (lethal), a resource the original
    #set never tracked (weapon durability), and a non-linear-in-state but still
    #linear-in-weight injection of "how close to fatigue" (deck size difference
    #alone can't distinguish 25->20 from 5->0, but 1/(n+1) can). Appended, not
    #interleaved, so the original 21 weights still line up unchanged when these
    #are zero-weighted - see calibrate_greedy_weights.py.
    my_total_attack = possible_state.current_player.get_attack() + total_minion_attack
    their_total_attack = possible_state.current_player.other_player.get_attack() + total_enemy_minion_attack
    lethal_margin_mine = my_total_attack - enemy_hp
    lethal_margin_theirs = their_total_attack - hp

    my_weapon = possible_state.current_player.weapon
    their_weapon = possible_state.current_player.other_player.weapon
    weapon_durability_difference = (my_weapon.get_health() if my_weapon else 0) - (their_weapon.get_health() if their_weapon else 0)

    fatigue_proximity = 1 / (num_enemy_cards_in_library + 1) - 1 / (num_cards_in_library + 1)

    hero_power_available_difference = (0 if possible_state.current_player.used_hero_power else 1) \
                                       - (0 if possible_state.current_player.other_player.used_hero_power else 1)

    unused_mana = possible_state.current_player.current_mana

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
                      num_cards_in_hand_difference, num_cards_in_library_difference, num_cards_in_secrets_zone_difference,
                      lethal_margin_mine, lethal_margin_theirs, weapon_durability_difference,
                      fatigue_proximity, hero_power_available_difference, unused_mana]

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