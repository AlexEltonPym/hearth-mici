from collections import defaultdict
from numpy import log, sqrt, argmax
from numpy.random import RandomState
import _pickle as cPickle
from tqdm import trange
from exceptions import TooManyActions, PlayerDead

#from https://ai-boson.github.io/mcts/

class MonteCarloTreeSearchNode():
  def __init__(self, state, parent=None, parent_action=None):
    self.state = state
    self.parent = parent
    self.parent_action = parent_action
    self.children = []
    self._number_of_visits = 0
    self._results = defaultdict(int)
    self._results[1] = 0
    self._results[-1] = 0
    self._untried_actions = None
    self._untried_actions = self.untried_actions()
    return
  
  def untried_actions(self):
    self._untried_actions = self.get_legal_actions(self.state)
    return self._untried_actions
  
  def q(self):
    wins = self._results[1]
    loses = self._results[-1]
    return wins - loses
  
  def n(self):
    return self._number_of_visits

  def expand(self):
	
    action = self._untried_actions.pop()
    next_state = self.move(self.state, action)
    child_node = MonteCarloTreeSearchNode(next_state, parent=self, parent_action=action)

    self.children.append(child_node)
    return child_node 

  def is_terminal_node(self):
    return self.is_game_over(self.state)
  
  def rollout(self, random_state):
    current_rollout_state = self.state
    
    while not self.is_game_over(current_rollout_state):
        
      possible_moves = self.get_legal_actions(current_rollout_state)
      action = self.rollout_policy(possible_moves, random_state)
      current_rollout_state = self.move(current_rollout_state, action)
    return self.game_result(current_rollout_state)
  
  def backpropagate(self, result):
    self._number_of_visits += 1.
    self._results[result] += 1.
    if self.parent:
      self.parent.backpropagate(result)

  def is_fully_expanded(self):
    return len(self._untried_actions) == 0
  
  def best_child(self, c_param=0.1): #c_param ~= exploratation percentage
    #q = node winrate, n = node visits
    choices_weights = [(c.q() / c.n()) + c_param * sqrt((2 * log(self.n()) / c.n())) for c in self.children]
    return self.children[argmax(choices_weights)]

  def rollout_policy(self, possible_moves, random_state):
  
    return possible_moves[random_state.randint(len(possible_moves))]
  
  def _tree_policy(self):
    current_node = self
    while not current_node.is_terminal_node():
        
      if not current_node.is_fully_expanded():
        return current_node.expand()
      else:
        current_node = current_node.best_child()
    return current_node


  def best_action(self, random_state):
    simulation_no = 50

    for i in range(simulation_no):
      try:
        print(f"MCTS iteration {i}")
        v = self._tree_policy()
        reward = v.rollout(random_state)
        v.backpropagate(reward)
      except PlayerDead:
        print("DEAD")
        raise PlayerDead
    
    return self.best_child(c_param=0.) #c=0 means full exploitation

  def get_legal_actions(self, state): 

    return state.get_available_actions(state.current_player)

  def is_game_over(self, state):
    return state.player.health <= 0 or state.enemy.health <= 0


  def game_result(self, state):
    return -1 if state.current_player.health <= 0 else 1 if state.current_player.other_player.health <= 0 else 0

  def move(self, state, action):
    new_state = cPickle.loads(cPickle.dumps(state, -1))
    try:
      turn_end = new_state.perform_action(action)
      

      if turn_end:
        new_state.end_turn()
        new_state.untap()
    except PlayerDead:
      pass

    return new_state
  
  def __repr__(self):
    return f"{self.q()}/{self.n()}{[child for child in self.children] if len(self.children) > 0 else ""}"
  
