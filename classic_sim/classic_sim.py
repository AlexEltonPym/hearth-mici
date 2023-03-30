from zones import Deck
from enums import *
from strategy import GreedyAction, RandomAction, RandomNoEarlyPassing
from game_manager import GameManager
from numpy.random import RandomState
from itertools import combinations
  


def main():
  results = []
  # results.append(random_hunter_vs_mage())
  results.append(class_card_all_combinations())
  print(results)



  return True

def class_card_all_combinations():
  results = []
  mini_meta_names = ['Mage', 'Hunter', 'Warrior']
  mini_meta_cardsets = [CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR]
  mini_meta_classes = [Classes.MAGE, Classes.HUNTER, Classes.WARRIOR]
  for player_index, enemy_index in combinations(range(3), 2):
    game_manager = GameManager(RandomState())

    game_manager.create_player_pool([mini_meta_cardsets[player_index]])
    game_manager.create_enemy_pool([mini_meta_cardsets[enemy_index]])
    game_manager.create_player(mini_meta_classes[player_index], Deck.generate_random, GreedyAction)
    game_manager.create_enemy(mini_meta_classes[enemy_index], Deck.generate_random, GreedyAction)

    winrate = game_manager.simulate(num_games=10, parralel=-1, silent=False)
    matchup_string = f"{mini_meta_names[player_index]} vs {mini_meta_names[enemy_index]}"
    results.append((matchup_string, winrate))
  return results

def class_cards_mage_vs_hunter():
  game_manager = GameManager(RandomState())
  game_manager.create_player_pool([CardSets.CLASSIC_MAGE])
  game_manager.create_enemy_pool([CardSets.CLASSIC_HUNTER])
  game_manager.create_player(Classes.MAGE, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.HUNTER, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(num_games=100, parralel=-1, silent=False)
  return result

def class_cards_hunter_vs_warrior():
  game_manager = GameManager(RandomState())
  game_manager.create_player_pool([CardSets.CLASSIC_HUNTER])
  game_manager.create_enemy_pool([CardSets.CLASSIC_WARRIOR])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.WARRIOR, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(num_games=500, parralel=-1, silent=False)
  return result

def random_hunter_vs_mage():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(num_games=100, parralel=-1)
  return result



if __name__ == '__main__':
  main()
