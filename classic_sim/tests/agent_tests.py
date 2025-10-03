import sys
  
# appending the parent directory path
sys.path.append('../src/')

from game_manager import GameManager
from strategy import GreedyAction, GreedyActionSmart, RandomNoEarlyPassing, RandomAction, GreedyActionSmartv1, MCTS
from enums import *
from zones import Deck
from tqdm import tqdm
from exceptions import TooManyActions
from copy import deepcopy
from timeit import timeit


def test_copy_speeds():
  cpickle = timeit(stmt="cpy=cPickle.loads(cPickle.dumps(game, -1))", setup="import _pickle as cPickle; from game_manager import GameManager; game=GameManager().create_test_game()", number=100)
  pickle = timeit(stmt="cpy=pickle.loads(pickle.dumps(game, -1))", setup="import pickle; from game_manager import GameManager; game=GameManager().create_test_game()", number=100)
  dc = timeit(stmt="cpy=deepcopy(game)", setup="from copy import deepcopy; from game_manager import GameManager; game=GameManager().create_test_game()", number=100)
  
  print(cpickle, pickle, dc)




def test_mcts_vs_greedy():

  mage_player = ['Gadgetzan Auctioneer', 'Gadgetzan Auctioneer', 'Dire Wolf Alpha', 'Dire Wolf Alpha', 'Raging Worgen', 'Raging Worgen', 'Arcane Missiles', 'Arcane Missiles', 'Fen Creeper', 'Fen Creeper', 'Big Game Hunter', 'Big Game Hunter', 'Spellbender', 'Spellbender', 'Silvermoon Guardian', 'Silvermoon Guardian', 'Thrallmar Farseer', 'Thrallmar Farseer', 'Etherial Arcanist', 'Etherial Arcanist', 'Frostbolt', 'Frostbolt', 'Nightblade', 'Nightblade', 'Spellbreaker', 'Spellbreaker', 'Abusive Sergeant', 'Abusive Sergeant', 'Frost Nova', 'Frost Nova']
  mage_enemy = ['Arcane Missiles', 'Arcane Missiles', 'Murloc Raider', 'Murloc Raider', 'Arcane Explosion', 'Arcane Explosion', 'Bloodfen Raptor', 'Bloodfen Raptor', 'Novice Engineer', 'Novice Engineer', 'River Crocolisk', 'River Crocolisk', 'Arcane Intellect', 'Arcane Intellect', 'Raid Leader', 'Raid Leader', 'Wolfrider', 'Wolfrider', 'Fireball', 'Fireball', 'Oasis Snapjaw', 'Oasis Snapjaw', 'Polymorph', 'Polymorph', "Sen'jin Shieldmasta", "Sen'jin Shieldmasta", 'Nightblade', 'Nightblade', 'Boulderfist Ogre', 'Boulderfist Ogre']

  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_player(Classes.MAGE, Deck.generate_from_decklist(mage_player), MCTS())
  game_manager.create_enemy(Classes.MAGE, Deck.generate_from_decklist(mage_enemy), GreedyActionSmart())
  game_results = game_manager.simulate(10, False, 1, True)

  print(game_results)


def test_smart_greedy_vs_greedy():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random_from_fixed_seed, GreedyActionSmart())
  game_manager.create_enemy(Classes.HUNTER, Deck.generate_random_from_fixed_seed, GreedyAction())
  game_results = game_manager.simulate(20, False, -1)
  print(game_results)

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
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  game_manager.create_player(Classes.WARRIOR, Deck.generate_from_decklist(basic_warrior), GreedyActionSmart([-0.1, 1, -1, 1, 1, 2, 2, 1.5, 3, -3, 1, -1, 1, -1, 1, -1, 1, -1, -1, 0, 1]))
  game_manager.create_enemy(Classes.HUNTER, Deck.generate_from_decklist(basic_hunter), GreedyActionSmart([-0.1, 1, -1, 1, 1, 2, 2, 1.5, 3, -3, 1, -1, 1, -1, 1, -1, 1, -1, -1, 0, 1]))
  results = game_manager.simulate(17, False, -1)
  print(results)
  
def main():
  test_mcts_vs_greedy()

if __name__ == '__main__':
  main()