import sys
sys.path.append('../../')

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
  game_manager.create_player(Classes.MAGE, Deck.generate_from_decklist(mage_player), GreedyActionSmart([-9.854581441763525, 2.657496233411372, -3.6072743836534915, -0.6478507131609952, -5.088893271660031, 7.887471404722554, 3.7086334661485125, 1.548993522919302, -5.93328226799545, -8.05241041210411, 2.913315742740263, -5.514530992036361, -0.8364601792409374, 3.1159253138681677, 2.561393716573111, -8.593355960935654, -7.591839617288403, 3.7209453403110366, -2.04326490991847, 1.0229424944333392, -5.473427125141708]))
  game_manager.create_enemy(Classes.MAGE, Deck.generate_from_decklist(mage_enemy), GreedyActionSmart([-9.854581441763525, 2.657496233411372, -3.6072743836534915, -0.6478507131609952, -5.088893271660031, 7.887471404722554, 3.7086334661485125, 1.548993522919302, -5.93328226799545, -8.05241041210411, 2.913315742740263, -5.514530992036361, -0.8364601792409374, 3.1159253138681677, 2.561393716573111, -8.593355960935654, -7.591839617288403, 3.7209453403110366, -2.04326490991847, 1.0229424944333392, -5.473427125141708]))
  game_results = game_manager.simulate(100, False, 1, True)

  print(game_results)
