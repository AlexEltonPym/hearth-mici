import sys
sys.path.append('../')

from enums import *
from strategy import GreedyActionSmart, RandomNoEarlyPassing
from game_manager import GameManager
from zones import Deck
from statistics import mean
from random import uniform, gauss
from numpy.random import RandomState



mage_player = [
  'Gadgetzan Auctioneer', 'Gadgetzan Auctioneer', 'Dire Wolf Alpha', 'Dire Wolf Alpha', 'Raging Worgen', 'Raging Worgen', 'Arcane Missiles', 'Arcane Missiles', 'Fen Creeper', 'Fen Creeper', 'Big Game Hunter', 'Big Game Hunter', 'Spellbender', 'Spellbender', 'Silvermoon Guardian', 'Silvermoon Guardian', 'Thrallmar Farseer', 'Thrallmar Farseer', 'Etherial Arcanist', 'Etherial Arcanist', 'Frostbolt', 'Frostbolt', 'Nightblade', 'Nightblade', 'Spellbreaker', 'Spellbreaker', 'Abusive Sergeant', 'Abusive Sergeant', 'Frost Nova', 'Frost Nova'
]

mage_enemy = [
  'Arcane Missiles', 'Arcane Missiles', 'Murloc Raider', 'Murloc Raider', 'Arcane Explosion', 'Arcane Explosion', 'Bloodfen Raptor', 'Bloodfen Raptor', 'Novice Engineer', 'Novice Engineer', 'River Crocolisk', 'River Crocolisk', 'Arcane Intellect', 'Arcane Intellect', 'Raid Leader', 'Raid Leader', 'Wolfrider', 'Wolfrider', 'Fireball', 'Fireball', 'Oasis Snapjaw', 'Oasis Snapjaw', 'Polymorph', 'Polymorph', "Sen'jin Shieldmasta", "Sen'jin Shieldmasta", 'Nightblade', 'Nightblade', 'Boulderfist Ogre', 'Boulderfist Ogre'
]

for i in range(1):
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_player(Classes.MAGE, Deck.generate_from_decklist(mage_player), RandomNoEarlyPassing())
  game_manager.create_enemy(Classes.MAGE, Deck.generate_from_decklist(mage_enemy), RandomNoEarlyPassing())
  game_results = game_manager.simulate(32, False, 1, True)

  print(game_results)
