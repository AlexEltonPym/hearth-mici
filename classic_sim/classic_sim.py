from card import Card
from deck import Deck
from player import Player
from game import Game
from enums import *
from card_sets import build_pool
from strategy import GreedyAction, RandomAction, RandomNoEarlyPassing
import numpy as np
from tqdm import tqdm
from statistics import mean
from joblib import Parallel, delayed
from numpy.random import RandomState
from game_manager import GameManager
NUM_GAMES = 16

def main():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(NUM_GAMES, parralel=-1)
  assert result > 0 and result < 1
  print(result)

if __name__ == '__main__':
  main()
