from card_sets import *
from player import Player
from game import Game
from exceptions import TooManyActions
from zones import Deck
from strategy import GreedyAction, MCTS
from numpy import empty
from tqdm import trange
import multiprocessing
from joblib import Parallel, delayed
from numpy.random import RandomState
import numpy as np
from statistics import mean
from random import randint

class GameManager():
  def __init__(self, random_state=RandomState()):
    self.random_state = random_state
    self.player = None
    self.enemy = None
    self.game = None

  def build_full_game_manager(self, player_sets, enemy_sets, player_class, player_deck_constuctor, player_strategy, enemy_class, enemy_deck_constructor, enemy_strategy, random_state=RandomState(None)):
    self.random_state = random_state
    self.player = None
    self.enemy = None
    self.game = None
    self.create_player_pool(player_sets)
    self.create_enemy_pool(enemy_sets)
    self.create_player(player_class, player_deck_constuctor, player_strategy)
    self.create_enemy(enemy_class, enemy_deck_constructor, enemy_strategy)
    

  def create_player_pool(self, sets):
    self.player_pool_sets = sets

  def create_enemy_pool(self, sets):
    self.enemy_pool_sets = sets

  def get_player_pool(self):
    return build_pool(self.player_pool_sets, self.random_state)

  def get_enemy_pool(self):
    return build_pool(self.enemy_pool_sets, self.random_state)

  def create_player(self, player_class, deck_constructor, strategy):
    self.player = Player("player", self, player_class, deck_constructor, strategy)

  def create_enemy(self, enemy_class, deck_constructor, strategy):
    self.enemy = Player("enemy", self, enemy_class, deck_constructor, strategy)

  def find_card(self, name):
    for card in self.get_player_pool() + self.get_enemy_pool():
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
    self.game.setup_players()
    self.game.start_game()

    return self.game
  
  def create_test_game(self):
    self.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR, CardSets.TEST_CARDS])
    self.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR, CardSets.TEST_CARDS])
    self.create_player(Classes.WARRIOR, Deck.generate_random, GreedyAction())
    self.create_enemy(Classes.HUNTER, Deck.generate_random, GreedyAction())
    self.create_game()
    self.game.player.hand.clear()
    self.game.enemy.hand.clear()
    self.game.player.current_mana = 10
    self.game.enemy.current_mana = 10
    return self.game

  def simulate(self, num_games, silent=False, parralel=1, rng=True, rank=-1):
    game_results = []

    if parralel == 1:
      if not silent:
        # print(f"Running {num_games} games on single core")
        pass
      game_results = self.run_games(num_games, silent, rng, rank)
    else:
      num_processors = multiprocessing.cpu_count() if parralel == -1 else parralel
      num_games_per_processor = 1 if num_games < num_processors else num_games // num_processors
      num_jobs_to_run = num_games // num_games_per_processor
      if not silent:
        print(f'Spliting {num_games} games across {num_processors} cores, {num_games_per_processor} games per core.')
        (f'{num_jobs_to_run} total jobs to run')

      parralel_game_results = Parallel(timeout=None, n_jobs=parralel, verbose=0 if silent else 100)(delayed(self.run_games)(num_games_per_processor, silent, rng, rank) for i in range(num_jobs_to_run))
      for processors_result in parralel_game_results:
        game_results.extend(processors_result)
    return [mean(x) for x in zip(*game_results)] #average the stats


  def run_games(self, num_games, silent, rng, rank):
    game_results = []
    if rng:
      self.random_state = RandomState()
    else:
      self.random_state = RandomState(0)
    self.create_game()

    for i in trange(num_games, disable=silent, position=1, leave=True, desc=f"Core {rank} playing {self.game.player.player_class} vs {self.game.enemy.player_class}"):
      try:
        if isinstance(self.game.player.strategy, MCTS) or isinstance(self.game.enemy.strategy, MCTS):
          game_result = self.game.play_mcts()
        else:
          game_result = self.game.play_game()
      except (TooManyActions, RecursionError) as e:
        game_result = None
        # if not silent:
        print(e)
      except Exception as e:
        game_result = None
        # if not silent:
          # print(e)
          # print(self.player.deck.names())
          # print(self.enemy.deck.names())
        raise e
      game_results.append(game_result)
      self.game.reset_game()
      self.game.start_game()
    return game_results