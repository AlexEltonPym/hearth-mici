import sys

sys.path.append('../src/')
sys.path.append('/map_elites')
from enums import *
from strategy import GreedyActionSmart, RandomNoEarlyPassing
from game_manager import GameManager
from zones import Deck
from statistics import mean
from numpy.random import RandomState




# mage_player = [
#   'Gadgetzan Auctioneer', 'Gadgetzan Auctioneer', 'Dire Wolf Alpha', 'Dire Wolf Alpha', 'Raging Worgen', 'Raging Worgen', 'Arcane Missiles', 'Arcane Missiles', 'Fen Creeper', 'Fen Creeper', 'Big Game Hunter', 'Big Game Hunter', 'Spellbender', 'Spellbender', 'Silvermoon Guardian', 'Silvermoon Guardian', 'Thrallmar Farseer', 'Thrallmar Farseer', 'Etherial Arcanist', 'Etherial Arcanist', 'Frostbolt', 'Frostbolt', 'Nightblade', 'Nightblade', 'Spellbreaker', 'Spellbreaker', 'Abusive Sergeant', 'Abusive Sergeant', 'Frost Nova', 'Frost Nova'
# ]

# mage_enemy = [
#   'Arcane Missiles', 'Arcane Missiles', 'Murloc Raider', 'Murloc Raider', 'Arcane Explosion', 'Arcane Explosion', 'Bloodfen Raptor', 'Bloodfen Raptor', 'Novice Engineer', 'Novice Engineer', 'River Crocolisk', 'River Crocolisk', 'Arcane Intellect', 'Arcane Intellect', 'Raid Leader', 'Raid Leader', 'Wolfrider', 'Wolfrider', 'Fireball', 'Fireball', 'Oasis Snapjaw', 'Oasis Snapjaw', 'Polymorph', 'Polymorph', "Sen'jin Shieldmasta", "Sen'jin Shieldmasta", 'Nightblade', 'Nightblade', 'Boulderfist Ogre', 'Boulderfist Ogre'
# ]

hunter_deck = ['Mind Control Tech', 'Mind Control Tech', 'Spellbreaker', 'Spellbreaker', 'Mogushan Warden', 'Mogushan Warden', 'River Crocolisk', 'River Crocolisk', 'Tracking', 'Tracking', "Sen'jin Shieldmasta", "Sen'jin Shieldmasta", 'Acidic Swamp Ooze', 'Acidic Swamp Ooze', 'Shieldbearer', 'Shieldbearer', 'Faerie Dragon', 'Faerie Dragon', 'Ravenholdt Assassin', 'Ravenholdt Assassin', 'Murloc Tidehunter', 'Murloc Tidehunter', 'Doomsayer', 'Doomsayer', 'Ancient Brewmaster', 'Ancient Brewmaster', 'Amani Berserker', 'Amani Berserker', 'Sunwalker', 'Sunwalker']
hunter_strategy = [-22.12385930753943, 9.5065632267045, -2.096441151046316, 9.28995189000177, 10.634564120521556, -10.706230757952046, -2.9526491023306414, 2.2129414101596634, -4.412286017800183, -1.1528359001247617, -9.748021384220094, -13.216529330963112, 10.769192096288341, 17.030197761543608, 1.2372197580021578, -2.5762149092225024, -6.769467451718402, -11.731528079970682, 6.70574588298511, -1.232072995847521, -1.942522058600187]


mage_strategy = [-6.239820761144781, -0.29803130904812614, 3.0178646757977203, 16.28731625297628, 3.9359416822552022, -9.44699936778667, 1.2315411553893485, 23.804903348769635, -9.293441609316185, 0.4057027176963508, -6.798683747334426, -14.412970405717758, -13.723360360532386, -13.55002061960751, 9.287079190421515, -11.542958438441785, 24.777405165014844, -6.865002925691265, 2.47989269254874, -1.0578984598671513, 4.19282276897225]
mage_deck = ['Mad Bomber', 'Mad Bomber', 'Stranglethorn Tiger', 'Stranglethorn Tiger', 'Crazed Alchemist', 'Crazed Alchemist', 'Acolyte of Pain', 'Acolyte of Pain', 'Lord of the Arena', 'Lord of the Arena', 'Gadgetzan Auctioneer', 'Gadgetzan Auctioneer', 'Silver Hand Knight', 'Silver Hand Knight', 'Goldshire Footman', 'Goldshire Footman', 'Coldlight Seer', 'Coldlight Seer', 'Pint-Sized Summoner', 'Pint-Sized Summoner', 'Frost Nova', 'Frost Nova', 'Azure Drake', 'Azure Drake', 'Goldshire Footman', 'Goldshire Footman', 'Bloodfen Raptor', 'Bloodfen Raptor', 'Polymorph', 'Polymorph']
for i in range(1):
  game_manager = GameManager(random_state=RandomState(1))
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_player(Classes.HUNTER, Deck.generate_from_decklist(hunter_deck), GreedyActionSmart(hunter_strategy))
  game_manager.create_enemy(Classes.MAGE, Deck.generate_from_decklist(mage_deck), GreedyActionSmart(mage_strategy))
  game_manager.create_game()
  print(game_manager.game.enemy)
  print(game_manager.game.enemy.hero_power)

  # game_results = game_manager.simulate(1000, False, 1, False)

  # print(game_results)
