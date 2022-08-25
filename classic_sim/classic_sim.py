import random
from card import Card
from deck import Deck
from player import Player
from game import Game
from enums import *
from card_sets import build_pool
from strategy import GreedyAction, RandomAction
import numpy as np
from tqdm import tqdm
from statistics import mean

def main():
  num_games = 10

  random.seed(0)

  hunter_pool = build_pool([CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_NEUTRAL])
  op_pool = build_pool([CardSets.OP_CARDS])
  mirror_deck = Deck().generate_random(hunter_pool)
  player = Player(Classes.HUNTER, mirror_deck, GreedyAction)
  enemy = Player(Classes.HUNTER, mirror_deck, GreedyAction)

  game_results = np.empty(num_games)
  for i in tqdm(range(num_games)):
    game = Game(player, enemy)
    game_results[i] = game.simulate_game()
  
  print(mean(game_results))

if __name__ == '__main__':
  main()
