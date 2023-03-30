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
  game_manager.create_player(Classes.HUNTER, Deck.generate_random_from_fixed_seed, GreedyActionSmart)
  game_manager.create_enemy(Classes.HUNTER, Deck.generate_random_from_fixed_seed, GreedyAction)
  game = game_manager.create_game()
  # print(game_manager.player.deck)
  # for card in game_manager.player.deck:
  #   print(card)
  # print("---")
  # print(game_manager.enemy.deck)
  # for card in game_manager.enemy.deck:
  #   print(card)

  game_results = []
  num_games = 200
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


def test_decklist_vs_decklist():
  basic_mage = [
    "Arcane Missiles",
    "Arcane Missiles",
    "Murloc Raider",
    "Murloc Raider",
    "Arcane Explosion",
    "Arcane Explosion",
    "Bloodfen Raptor",
    "Bloodfen Raptor",
    "Novice Engineer",
    "Novice Engineer",
    "River Crocolisk",
    "River Crocolisk",
    "Arcane Intellect",
    "Arcane Intellect",
    "Raid Leader",
    "Raid Leader",
    "Wolfrider",
    "Wolfrider",
    "Fireball",
    "Fireball",
    "Oasis Snapjaw",
    "Oasis Snapjaw",
    "Polymorph",
    "Polymorph",
    "Sen'jin Shieldmasta",
    "Sen'jin Shieldmasta",
    "Nightblade",
    "Nightblade",
    "Boulderfist Ogre",
    "Boulderfist Ogre"
  ]

  basic_warrior = [
    "Boulderfist Ogre",
    "Boulderfist Ogre",
    "Charge",
    "Charge",
    "Dragonling Mechanic",
    "Dragonling Mechanic",
    "Execute",
    "Execute",
    "Fiery War Axe",
    "Fiery War Axe",
    "Frostwolf Grunt",
    "Frostwolf Grunt",
    "Gurubashi Berserker",
    "Gurubashi Berserker",
    "Heroic Strike",
    "Heroic Strike",
    "Lord of the Arena",
    "Lord of the Arena",
    "Murloc Raider",
    "Murloc Raider",
    "Murloc Tidehunter",
    "Murloc Tidehunter",
    "Razorfen Hunter",
    "Razorfen Hunter",
    "Sen'jin Shieldmasta",
    "Sen'jin Shieldmasta",
    "Warsong Commander",
    "Warsong Commander",
    "Wolfrider",
    "Wolfrider"
  ]

  basic_hunter = [
    "Arcane Shot",
    "Arcane Shot",
    "Stonetusk Boar",
    "Stonetusk Boar",
    "Timber Wolf",
    "Timber Wolf",
    "Tracking",
    "Tracking",
    "Bloodfen Raptor",
    "Bloodfen Raptor",
    "River Crocolisk",
    "River Crocolisk",
    "Ironforge Rifleman",
    "Ironforge Rifleman",
    "Raid Leader",
    "Raid Leader",
    "Razorfen Hunter",
    "Razorfen Hunter",
    "Silverback Patriarch",
    "Silverback Patriarch",
    "Houndmaster",
    "Houndmaster",
    "Multi-Shot",
    "Multi-Shot",
    "Oasis Snapjaw",
    "Oasis Snapjaw",
    "Stormpike Commando",
    "Stormpike Commando",
    "Core Hound",
    "Core Hound"
  ]

  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_player(Classes.WARRIOR, Deck.generate_from_decklist(basic_warrior), GreedyActionSmart)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_from_decklist(basic_mage), GreedyActionSmart)
  game = game_manager.create_game()
  
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
  # print(game_results)
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
  test_decklist_vs_decklist()

if __name__ == '__main__':
  main()