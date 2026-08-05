from numpy import log, sqrt, argmax
from exceptions import PlayerDead
from utilities import BoundCloner

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

  def rollout(self, random_state, turn_limit):
    if self.is_terminal_node():
      return self.winner_name(self.state)
    rollout_state, _ = self._get_cloner().clone()
    turns = 0
    try:
      while not self.is_game_over(rollout_state) and turns < turn_limit:
        possible_moves = rollout_state.get_available_actions(rollout_state.current_player)
        action = possible_moves[random_state.randint(len(possible_moves))]
        turn_end = rollout_state.perform_action(action)
        if turn_end:
          rollout_state.end_turn()
          rollout_state.untap()
          turns += 1
    except PlayerDead:
      pass
    return self.winner_name(rollout_state)

  def backpropagate(self, winner_name):
    node = self
    while node is not None:
      node._number_of_visits += 1
      if winner_name is not None and node.acting_player_name is not None:
        node._score += 1.0 if node.acting_player_name == winner_name else -1.0
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

  def best_action(self, random_state, simulations, c_param, rollout_turn_limit):
    for i in range(simulations):
      v = self._tree_policy(random_state, c_param)
      winner_name = v.rollout(random_state, rollout_turn_limit)
      v.backpropagate(winner_name)
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

  def winner_name(self, state):
    #true terminals decide by death; rollouts cut off early decide by health lead
    player_dead = state.player.health <= 0
    enemy_dead = state.enemy.health <= 0
    if player_dead and enemy_dead:
      return None
    if enemy_dead:
      return "player"
    if player_dead:
      return "enemy"
    if state.player.health > state.enemy.health:
      return "player"
    if state.enemy.health > state.player.health:
      return "enemy"
    return None

  def __repr__(self):
    return f"{self.q()}/{self.n()}"
