import random
from card import Card
from deck import Deck
from player import Player
from game import Game
from enums import *
from card_sets import build_pool
from strategy import GreedyAction
import numpy as np
from tqdm import tqdm

def main():
  num_games = 1000

  random.seed(0)

  card_pool = build_pool([CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_NEUTRAL])
  player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
  enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)

  game_results = np.empty(num_games)
  for i in tqdm(range(num_games)):
    game = Game(player, enemy)
    game_results[i] = game.simulate_game()
  
  print(game_results)

if __name__ == '__main__':
  main()
