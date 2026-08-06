from numpy import log, sqrt, argmax, tanh
from enums import Attributes
from exceptions import PlayerDead
from utilities import BoundCloner

#GreedyActionSmart's default weights with the turn_passed term dropped, plus
#the 6-feature additive extension from strategy.py's GreedyActionSmart
#(lethal margin both ways, weapon durability, fatigue proximity, hero power
#availability, unused mana), defaulting to 0 for the same reason it does
#there - unchanged behaviour until a caller supplies better ones (e.g. a
#self-play-trained vector - see examples/metagame_analysis).
_EVAL_WEIGHTS = [10, -10, 10, 10, 1, 1, 1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
_OTHER_POSITIVE = [Attributes.CHARGE, Attributes.STEALTH, Attributes.WINDFURY, Attributes.HEXPROOF,
                   Attributes.POISONOUS, Attributes.IMMUNE, Attributes.FREEZER]

def evaluate_position(state, weights=_EVAL_WEIGHTS):
  #the 26-feature linear evaluation from state.player's perspective, squashed
  #to [-1, 1]. weights is a real parameter, not just a module default - it
  #must survive being passed into a rollout running in another process
  #(distributed evaluation), where monkeypatching the module constant
  #wouldn't propagate.
  me, them = state.player, state.enemy
  my_attrs = [minion.get_all_attributes() for minion in me.board]
  their_attrs = [minion.get_all_attributes() for minion in them.board]
  total_my_attack = sum(minion.get_attack() for minion in me.board)
  total_their_attack = sum(minion.get_attack() for minion in them.board)
  my_weapon, their_weapon = me.weapon, them.weapon
  features = [
    me.health, them.health, me.health - them.health,
    me.armor - them.armor,
    len(me.board) - len(them.board),
    total_my_attack - total_their_attack,
    sum(minion.get_health() for minion in me.board) - sum(minion.get_health() for minion in them.board),
    sum(1 for attrs in my_attrs if Attributes.TAUNT in attrs),
    sum(1 for attrs in their_attrs if Attributes.TAUNT in attrs),
    sum(1 for attrs in my_attrs if Attributes.DIVINE_SHIELD in attrs),
    sum(1 for attrs in their_attrs if Attributes.DIVINE_SHIELD in attrs),
    sum(1 for attrs in my_attrs if Attributes.LIFESTEAL in attrs),
    sum(1 for attrs in their_attrs if Attributes.LIFESTEAL in attrs),
    sum(1 for attrs in my_attrs if Attributes.SPELL_DAMAGE in attrs),
    sum(1 for attrs in their_attrs if Attributes.SPELL_DAMAGE in attrs),
    sum(sum(1 for attrs in my_attrs if attribute in attrs) for attribute in _OTHER_POSITIVE),
    sum(sum(1 for attrs in their_attrs if attribute in attrs) for attribute in _OTHER_POSITIVE),
    len(me.hand) - len(them.hand),
    len(me.deck) - len(them.deck),
    len(me.secrets_zone) - len(them.secrets_zone),
    (me.get_attack() + total_my_attack) - them.health, #lethal_margin_mine
    (them.get_attack() + total_their_attack) - me.health, #lethal_margin_theirs
    (my_weapon.get_health() if my_weapon else 0) - (their_weapon.get_health() if their_weapon else 0),
    1 / (len(them.deck) + 1) - 1 / (len(me.deck) + 1), #fatigue_proximity
    (0 if me.used_hero_power else 1) - (0 if them.used_hero_power else 1),
    me.current_mana, #unused_mana
  ]
  return float(tanh(sum(feature * weight for feature, weight in zip(features, weights)) / 100.0))

#UCT search for two-player games with multiple actions per turn.
#Action objects hold references to the state they were generated from, so
#forward moves pickle (state, action) together (clone_with_action) to get an
#action bound to the clone. Rewards are stored per-node from the perspective
#of the player who took the action leading to that node, so best_child
#maximises correctly for whichever player is choosing, without assuming
#plies alternate.

class MonteCarloTreeSearchNode():
  def __init__(self, state, parent=None, parent_action_index=None, acting_player_name=None):
    self.state = state
    self.parent = parent
    self.parent_action_index = parent_action_index #index into parent.available_actions
    self.acting_player_name = acting_player_name #player who took parent_action; perspective for _score
    self.children = []
    self._number_of_visits = 0
    self._score = 0.0
    if self.is_terminal_node():
      self.available_actions = []
    else:
      self.available_actions = self.state.get_available_actions(self.state.current_player)
    self._untried_action_indices = list(range(len(self.available_actions)))
    self._cloner = None #lazy: one dump per node serves every expand and rollout

  def _get_cloner(self):
    if self._cloner is None:
      self._cloner = BoundCloner(self.state, self.available_actions)
    return self._cloner

  def q(self):
    return self._score

  def n(self):
    return self._number_of_visits

  def expand(self, random_state):
    untried = random_state.randint(len(self._untried_action_indices))
    action_index = self._untried_action_indices.pop(untried)
    next_state = self.move(action_index)
    child_node = MonteCarloTreeSearchNode(next_state, parent=self, parent_action_index=action_index,
                                          acting_player_name=self.state.current_player.name)
    self.children.append(child_node)
    return child_node

  def is_terminal_node(self):
    return self.is_game_over(self.state)

  def rollout(self, random_state, turn_limit, guided, eval_weights=_EVAL_WEIGHTS):
    if self.is_terminal_node():
      return self.state_value(self.state, guided, eval_weights)
    rollout_state, _ = self._get_cloner().clone()
    turns = 0
    try:
      while not self.is_game_over(rollout_state) and turns < turn_limit:
        possible_moves = rollout_state.get_available_actions(rollout_state.current_player)
        if guided and len(possible_moves) > 1:
          #END_TURN is always the last action; don't pass while plays remain
          action = possible_moves[random_state.randint(len(possible_moves) - 1)]
        else:
          action = possible_moves[random_state.randint(len(possible_moves))]
        turn_end = rollout_state.perform_action(action)
        if turn_end:
          rollout_state.end_turn()
          rollout_state.untap()
          turns += 1
    except PlayerDead:
      pass
    return self.state_value(rollout_state, guided, eval_weights)

  def backpropagate(self, value):
    #value is from the "player" side's perspective
    node = self
    while node is not None:
      node._number_of_visits += 1
      if node.acting_player_name is not None:
        node._score += value if node.acting_player_name == "player" else -value
      node = node.parent

  def is_fully_expanded(self):
    return len(self._untried_action_indices) == 0

  def best_child(self, c_param):
    choices_weights = [(c.q() / c.n()) + c_param * sqrt(2 * log(self.n()) / c.n()) for c in self.children]
    return self.children[argmax(choices_weights)]

  def _tree_policy(self, random_state, c_param):
    current_node = self
    while not current_node.is_terminal_node():
      if not current_node.is_fully_expanded():
        return current_node.expand(random_state)
      else:
        current_node = current_node.best_child(c_param)
    return current_node

  def best_action(self, random_state, simulations, c_param, rollout_turn_limit, guided, eval_weights=_EVAL_WEIGHTS):
    for i in range(simulations):
      v = self._tree_policy(random_state, c_param)
      value = v.rollout(random_state, rollout_turn_limit, guided, eval_weights)
      v.backpropagate(value)
    return self.children[argmax([child.n() for child in self.children])]

  def move(self, action_index):
    new_state, bound_actions = self._get_cloner().clone()
    try:
      turn_end = new_state.perform_action(bound_actions[action_index])
      if turn_end:
        new_state.end_turn()
        new_state.untap()
    except PlayerDead:
      pass
    return new_state

  def is_game_over(self, state):
    return state.player.health <= 0 or state.enemy.health <= 0

  def state_value(self, state, guided, eval_weights=_EVAL_WEIGHTS):
    #true terminals decide by death; rollouts cut off early are evaluated by
    #the feature evaluator (guided) or by raw health lead
    player_dead = state.player.health <= 0
    enemy_dead = state.enemy.health <= 0
    if player_dead and enemy_dead:
      return 0.0
    if enemy_dead:
      return 1.0
    if player_dead:
      return -1.0
    if guided:
      return evaluate_position(state, eval_weights)
    if state.player.health > state.enemy.health:
      return 1.0
    if state.enemy.health > state.player.health:
      return -1.0
    return 0.0

  def __repr__(self):
    return f"{self.q()}/{self.n()}"
