from card_sets import *
from player import Player
from game import Game
from deck import Deck
from strategy import GreedyAction
from numpy import empty
from tqdm import trange
import multiprocessing
from joblib import Parallel, delayed
from numpy.random import RandomState

class GameManager():
  def __init__(self, random_state=RandomState(0)):
    self.random_state = random_state
    self.player_pool = None
    self.enemy_pool = None
    self.player = None
    self.enemy = None
    self.game = None

  def create_player_pool(self, sets):
    self.player_pool = build_pool(sets, self.random_state)

  def create_enemy_pool(self, sets):
    self.enemy_pool = build_pool(sets, self.random_state)

  def create_player(self, player_class, deck_constructor, strategy):
    self.player = Player("player", self, player_class, deck_constructor, strategy)

  def create_enemy(self, player_class, deck_constructor, strategy):
    self.enemy = Player("enemy", self, player_class, deck_constructor, strategy)

  def find_card(self, name):
    for card in self.player_pool + self.enemy_pool:
      if card.name == name:
        return deepcopy(card)

    raise KeyError("Could not find card")

  def get_card(self, name, zone):
    card = self.find_card(name)
    card.set_owner(zone.parent)
    card.set_parent(zone)
    return card

  def create_game(self):
    self.game = Game(self)
    return self.game

  def create_test_game(self):
    self.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
    self.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
    self.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
    self.create_enemy(Classes.HUNTER, Deck.generate_random, GreedyAction)
    self.create_game()
    self.game.player.hand.clear()
    self.game.enemy.hand.clear()
    self.game.player.current_mana = 10
    self.game.enemy.current_mana = 10
    return self.game

  def simulate(self, num_games, silent=False, parralel=1):
    game_results = empty(num_games)

    num_games /= multiprocessing.cpu_count() if parralel == -1 else parralel

    if parralel == 1:
      game_results = self.run_games(num_games, silent)
    else:
      parralel_game_results = Parallel(n_jobs=parralel, verbose=10)(delayed(self.run_games)(num_games, silent) for i in range(num_games))
      for result in parralel_game_results:
        game_results.append(result.mean())

    return game_results.mean()

  def run_games(self, num_games, silent):
    game_results = empty(num_games)
    self.create_game()

    for i in trange(num_games, disable=silent):
      game_results[i] = self.game.simulate_game()
      self.game.reset_game()
      
    return game_results.mean()