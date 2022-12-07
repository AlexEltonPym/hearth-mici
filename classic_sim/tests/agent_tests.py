import sys
  
# appending the parent directory path
sys.path.append('../')

from game_manager import GameManager
from strategy import GreedyAction, GreedyActionSmart, RandomNoEarlyPassing, RandomAction
from enums import *
from zones import Deck
from tqdm import tqdm
from game import TooManyActions
from copy import deepcopy


def test_smart_greedy_vs_greedy():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random_from_fixed_seed, RandomNoEarlyPassing)
  game_manager.create_enemy(Classes.HUNTER, Deck.generate_random_from_fixed_seed, RandomNoEarlyPassing)
  game = game_manager.create_game()
  # print(game_manager.player.deck)
  # for card in game_manager.player.deck:
  #   print(card)
  # print("---")
  # print(game_manager.enemy.deck)
  # for card in game_manager.enemy.deck:
  #   print(card)

  game_results = []
  num_games = 100
  for i in tqdm(range(num_games)):
    try:
      game_result = game.play_game()
    except (TooManyActions, RecursionError) as e:
      game_result = None
      print(e)
    game_results.append(game_result)
    game.reset_game()
    game.start_game()
  print(game_results)
  winrate = 0
  turns = 0
  diff = 0
  for result in game_results:
    winrate += result[0]
    turns += result[1]
    diff += result[2]
  winrate /= num_games
  turns /= num_games
  diff /= num_games

  print((winrate, turns, diff))




def main():
  test_smart_greedy_vs_greedy()

if __name__ == '__main__':
  main()