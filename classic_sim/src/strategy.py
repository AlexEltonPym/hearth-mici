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

    #the state features live in heuristic_features (the single shared
    #implementation - montecarlotreesearch.evaluate_position uses the same
    #one); a 27-long weight vector selects the historical v1 set, a 30-long
    #vector the post-study v2 set - both with turn_passed prepended.
    from heuristic_features import features_for_weights
    feature_vector = [1 if turn_passed else 0] + \
                     features_for_weights(possible_state, possible_state.current_player,
                                          len(self.weights) - 1)
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
  def __init__(self, eval_weights, beam_width=3, depth=3, pass_penalty=0.02,
               reply_samples=0, reply_mode="decklist", reply_weights=None,
               reply_priors=None):
    self.eval_weights = eval_weights
    self.beam_width = beam_width
    self.depth = depth
    self.pass_penalty = pass_penalty
    #Tier 2 reply stage (0 = off, exactly the original beam behavior):
    #re-score each final candidate plan by simulating reply_samples opponent
    #reply turns from determinized hands (see src/determinize.py) and
    #averaging the post-reply evaluation. reply_mode selects the knowledge
    #model ("decklist" or "class_prior"); reply_weights are the linear
    #weights for the cheap greedy that plays the reply (None = defaults);
    #reply_priors is the {card_name: share} dict class_prior mode needs.
    self.reply_samples = reply_samples
    self.reply_mode = reply_mode
    self.reply_weights = reply_weights
    self.reply_priors = reply_priors or {}
    self._plan = []

  def mulligan_rule(self, card):
    return card.get_manacost() < 4

  def _evaluate_for(self, possible_state, me):
    if isinstance(self.eval_weights, dict):
      from neural_eval import evaluate_state
      return evaluate_state(self.eval_weights, possible_state, me=me)
    #evaluate_position is state.player-relative, not perspective-relative
    #(montecarlotreesearch.py handles this via acting_player_name in backprop
    #instead) - a single sign flip covers the other seat.
    from montecarlotreesearch import evaluate_position
    score = evaluate_position(possible_state, self.eval_weights)
    if me is not possible_state.player:
      score = -score
    return score

  def _evaluate(self, possible_state):
    #current_player is fixed as us for the whole own-turn search
    return self._evaluate_for(possible_state, possible_state.current_player)

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
    #snapshot kept even for done entries: the reply stage clones them from
    #exactly this stream position
    rng_state = random_state.get_state()
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

  def _reply_score(self, entry, random_state):
    """Tier 2: mean post-reply evaluation of this plan's end state over
    reply_samples determinized opponent hands. The plan's turn is ended if
    it wasn't already (evaluating end-of-turn states, the SilverFish/Tier 2
    framing), the opponent's hidden hand is resampled per the knowledge
    model, and a cheap linear greedy plays their whole reply turn."""
    import zlib
    from numpy.random import RandomState as _NumpyRandomState
    from determinize import determinize_opponent_hand, sample_class_prior_hand

    cloner = BoundCloner(entry.state, None)
    base_seed = zlib.crc32(entry.rng_state[1].tobytes()) + entry.rng_state[2]
    total = 0.0
    for sample_index in range(self.reply_samples):
      sample_rng = _NumpyRandomState((base_seed + sample_index * 7919) % (2 ** 32))
      #position the shared master stream per-sample so each reply sim's
      #engine draws (untap draw, random targets) differ but deterministically
      random_state.set_state(sample_rng.get_state())
      clone, _ = cloner.clone()
      me_name = clone.current_player.name
      try:
        if not entry.done:
          #END_TURN is always the last available action (game.py appends it)
          clone.perform_action(clone.get_available_actions(clone.current_player)[-1])
        clone.end_turn()
        clone.untap()
        replier = clone.current_player
        me = replier.other_player
        if self.reply_mode == "class_prior":
          sample_class_prior_hand(replier, sample_rng, self.reply_priors)
        else:
          determinize_opponent_hand(replier, sample_rng)
        reply_agent = GreedyActionSmart(self.reply_weights) if self.reply_weights \
                      else GreedyActionSmart()
        for _ in range(30):
          if reply_agent.choose_action(clone):
            break
        total += self._evaluate_for(clone, me)
      except PlayerDead:
        #someone died during end-turn triggers, the untap draw (fatigue), or
        #the reply itself - resolve from our fixed perspective by name (the
        #me/replier locals may not exist yet on early deaths)
        us = clone.player if clone.player.name == me_name else clone.enemy
        total += -1000.0 if us.health <= 0 else 1000.0
    return total / self.reply_samples

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

    if self.reply_samples:
      #re-score the finalists by how well their end states survive a
      #determinized opponent reply; lethal-now plans (+-1000) keep their
      #terminal score - no reply exists after a dead player
      for entry in beam:
        if abs(entry.score) < 999:
          entry.score = self._reply_score(entry, random_state)

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