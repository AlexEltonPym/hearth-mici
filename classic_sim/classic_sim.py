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

NUM_GAMES = 100

def main():
  hunter_pool = build_pool([CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_NEUTRAL])
  op_pool = build_pool([CardSets.OP_CARDS])
  mirror_deck = Deck().generate_random(hunter_pool)
  player = Player(Classes.HUNTER, mirror_deck, GreedyAction)
  enemy = Player(Classes.HUNTER, mirror_deck, GreedyAction)

  game_results = Parallel(n_jobs=-1, verbose=10)(delayed(run_games)(player, enemy) for i in range(8))
  print(mean(game_results))

  # game_results = run_games(player,enemy)
  # print(game_results)

def run_games(player, enemy):
  games = np.empty(NUM_GAMES)
  game = Game(player, enemy)

  for i in tqdm(range(NUM_GAMES)):
    games[i] = game.simulate_game()
    game.reset_game()
    
  return games.mean()

if __name__ == '__main__':
  main()
