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
  
class NeuralGreedy():
  """1-ply greedy over the value net (neural_eval). Same clone/RNG-rewind loop
  as GreedyActionSmart; only the evaluator differs. pass_penalty nudges the
  agent away from ending the turn while value-neutral plays remain - the net
  scores the pass-state identically to the current state, so without it the
  argmax can pass early on ties."""
  def __init__(self, net_weights, pass_penalty=0.02):
    self.net_weights = net_weights
    self.pass_penalty = pass_penalty

  def mulligan_rule(self, card):
    return card.get_manacost() < 4

  def choose_action(self, state):
    from neural_eval import evaluate_state
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
        if possible_state.current_player.health <= 0:
          state_score = -1000.0
        elif possible_state.current_player.other_player.health <= 0:
          state_score = 1000.0
        else:
          state_score = evaluate_state(self.net_weights, possible_state,
                                       me=possible_state.current_player)
          if turn_passed:
            state_score -= self.pass_penalty
      except PlayerDead:
        turn_passed = 0
        if possible_state.current_player.health <= 0:
          state_score = -1000.0
        else:
          state_score = 1000.0
      possible_actions.append((action_index, state_score, turn_passed))

    best_action = sorted(possible_actions, key=lambda x: x[1])[-1]
    random_state.set_state(saved_rng_state)
    state.perform_action(available_actions[best_action[0]])
    return best_action[2]


class _BeamEntry():
  __slots__ = ("state", "parent", "action_index", "available_count", "rng_state", "score", "done")
  def __init__(self, state, parent, action_index, available_count, rng_state, score, done):
    self.state = state
    self.parent = parent
    self.action_index = action_index #index into this entry's *own* available_actions at its ply
    self.available_count = available_count #len(available_actions) this index was chosen from - see choose_action
    self.rng_state = rng_state #arrival snapshot, for expanding further - None once done (no expansion needed)
    self.score = score
    self.done = done #turn ended or game ended along this branch - carried forward unexpanded


class BeamSearch():
  """Beam search over turn-plans. GreedyAction/NeuralGreedy commit to the
  single best next action and re-decide from scratch every choose_action
  call - myopic, since it can't see a combo that needs two specific actions
  in order. This searches beam_width candidate continuations depth actions
  deep (same clone/RNG-rewind idiom as the flat greedy loop, applied per
  beam entry with parent pointers - see montecarlotreesearch.py's
  parent/parent_action_index for the same pattern) and commits the WHOLE
  winning plan, not just its first step, re-searching only once the plan
  is exhausted. Own-turn planning only: current_player never changes across
  the search (an END_TURN branch is scored but not expanded further, and is
  never advanced past with an actual end_turn() call, matching every other
  strategy's convention) - no opponent-hand modeling needed or attempted.
  Stateful across choose_action calls within a turn: never share one
  instance between both seats of a game. Self-play/ladder drivers reuse the
  same strategy object across many games on the same Game instance
  (reset_game() mutates in place - there's no fresh object to detect a new
  game from), so a plan left over from a game that ended abruptly (lethal,
  action-cap abort) would otherwise get replayed against a totally different
  next game's board. Each cached step therefore also carries the
  available-action count it was chosen from; choose_action discards the
  whole cached plan and re-searches if that count doesn't match reality
  instead of trusting a stale index.
  """
  def __init__(self, eval_weights, beam_width=3, depth=3, pass_penalty=0.02):
    self.eval_weights = eval_weights
    self.beam_width = beam_width
    self.depth = depth
    self.pass_penalty = pass_penalty
    self._plan = []

  def mulligan_rule(self, card):
    return card.get_manacost() < 4

  def _evaluate(self, possible_state):
    if isinstance(self.eval_weights, dict):
      from neural_eval import evaluate_state
      return evaluate_state(self.eval_weights, possible_state, me=possible_state.current_player)
    #evaluate_position is state.player-relative, not current_player-relative
    #(montecarlotreesearch.py handles this via acting_player_name in backprop
    #instead) - current_player is fixed as us for this whole search, so a
    #single sign flip here is enough.
    from montecarlotreesearch import evaluate_position
    score = evaluate_position(possible_state, self.eval_weights)
    if possible_state.current_player is not possible_state.player:
      score = -score
    return score

  def _perform_and_score(self, possible_state, action, parent, action_index, available_count, random_state):
    #see GreedyAction.choose_action for why terminal states are scored
    #before the caller advances further, and why PlayerDead is expected here.
    try:
      turn_passed = possible_state.perform_action(action)
      if possible_state.current_player.health <= 0:
        score, terminal = -1000.0, True
      elif possible_state.current_player.other_player.health <= 0:
        score, terminal = 1000.0, True
      else:
        score, terminal = self._evaluate(possible_state), False
        if turn_passed:
          score -= self.pass_penalty
    except PlayerDead:
      turn_passed, terminal = False, True
      score = -1000.0 if possible_state.current_player.health <= 0 else 1000.0

    done = turn_passed or terminal
    rng_state = None if done else random_state.get_state()
    return _BeamEntry(possible_state, parent, action_index, available_count, rng_state, score, done)

  def _prune(self, beam):
    return sorted(beam, key=lambda entry: entry.score, reverse=True)[:self.beam_width]

  def _expand_root(self, state, available_actions, random_state, saved_rng_state):
    cloner = BoundCloner(state, available_actions)
    entries = []
    for action_index in range(len(available_actions)):
      random_state.set_state(saved_rng_state)
      possible_state, cloned_actions = cloner.clone()
      entries.append(self._perform_and_score(possible_state, cloned_actions[action_index],
                                              None, action_index, len(available_actions), random_state))
    return entries

  def _expand_ply(self, beam, random_state):
    new_beam = []
    for entry in beam:
      if entry.done:
        new_beam.append(entry)
        continue
      available_actions = entry.state.get_available_actions(entry.state.current_player)
      cloner = BoundCloner(entry.state, available_actions)
      for action_index in range(len(available_actions)):
        random_state.set_state(entry.rng_state)
        possible_state, cloned_actions = cloner.clone()
        new_beam.append(self._perform_and_score(possible_state, cloned_actions[action_index],
                                                 entry, action_index, len(available_actions), random_state))
    return new_beam

  def _reconstruct_plan(self, entry):
    #each step is (action_index, available_count) - see choose_action for why
    #available_count rides along.
    plan = []
    node = entry
    while node is not None:
      plan.append((node.action_index, node.available_count))
      node = node.parent
    plan.reverse()
    return plan

  def _search(self, state):
    random_state = state.game_manager.random_state
    root_rng_state = random_state.get_state()

    available_actions = state.get_available_actions(state.current_player)
    if len(available_actions) == 1:
      return [(0, 1)]

    beam = self._prune(self._expand_root(state, available_actions, random_state, root_rng_state))
    ply = 1
    while ply < self.depth and any(not entry.done for entry in beam):
      beam = self._prune(self._expand_ply(beam, random_state))
      ply += 1

    #sorted(...)[-1], not max(): matches every other strategy's tie-break
    #convention in this file (stable sort favours the later-indexed action).
    best = sorted(beam, key=lambda entry: entry.score)[-1]
    #real execution starts from the original snapshot, not any explored branch's
    random_state.set_state(root_rng_state)
    return self._reconstruct_plan(best)

  def invalidate_plan(self):
    #for drivers that mutate the game behind the strategy's back (e.g.
    #epsilon-random injections in value_net_selfplay.play_recorded_game):
    #the cached plan was computed for a state that no longer exists, and the
    #available-count guard below only catches the corruption when the action
    #list happens to change length - so external actors must call this.
    self._plan = []

  def choose_action(self, state):
    available_actions = state.get_available_actions(state.current_player)
    #a plan whose next step wasn't chosen from this many available actions is
    #stale - left over from a previous game/turn this agent's object was
    #reused for (see class docstring) - discard it rather than trust an index
    #that might silently point at the wrong action instead of just crashing.
    if self._plan and self._plan[0][1] != len(available_actions):
      self._plan = []
    if not self._plan:
      self._plan = self._search(state)
      available_actions = state.get_available_actions(state.current_player)
    action_index, _ = self._plan.pop(0)
    return state.perform_action(available_actions[action_index])


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