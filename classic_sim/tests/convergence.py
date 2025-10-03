from sys import path
path.append('../')

from game_manager import GameManager
from strategy import GreedyActionSmart
from enums import *
from zones import Deck
from random import uniform, gauss, choice, shuffle
from exceptions import TooManyActions

from numpy.random import RandomState

import csv
from time import strftime

from multiprocessing import cpu_count
from joblib import Parallel, delayed

from scipy.stats import ttest_ind



try:
  from mpi4py import MPI
  MPI.Errhandler(MPI.ERRORS_ARE_FATAL)
  using_mpi = True
except ModuleNotFoundError:
  using_mpi = False

def get_available_cards(player_class):
  class_pools = {
    "M": [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE],
    "H": [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER],
    "W": [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR]
  }
  game_manager = GameManager()
  game_manager.create_player_pool(class_pools[player_class])
  pool = [card.name for card in game_manager.get_player_pool()]
  return pool

def generate_random_deck(player_class):
  pool = get_available_cards(player_class)
  shuffle(pool)
  new_deck = []
  while(len(new_deck) < 30):
    card = pool.pop()
    new_deck.append(card)
    new_deck.append(card)

  return new_deck

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
agents = {
  'uniform_random_agent': [uniform(-10, 10) for i in range(21)],
  'gaussian_random_agent': [gauss(0, 1) for i in range(21)],
  'uniform_big_range_agent': [uniform(-20, 20) for i in range(21)],
  'gaussian_big_random_agent': [gauss(0, 10) for i in range(21)],
  'handmade_agent': [-0.1, 1, -1, 1, 1, 2, 2, 1.5, 3, -3, 1, -1, 1, -1, 1, -1, 1, -1, -1, 0, 1],
  'mage_agent': [-6.30930064220375, 3.091874348044037, -6.790822546926796, -4.378467750148789, -0.8574207485421077, 9.089306035290257, 8.03074509395254, 6.504327063311184, 9.965734991863016, -4.592153540775539, -2.6633526968654087, -9.440514068705866, -9.354643495575266, -0.6833605761973534, 3.761689862095949, 6.369749949507067, -1.1518607311441968, 0.5478485048174786, 1.548645735116839, -3.437208480581903, -7.424767157011272],
  'hunter_agent': [-4.058971271031244, 2.1097634416195774, -1.8912384626642584, -0.05767500466243369, -1.6842945838523846, 7.262959220816892, 3.1318965653591295, 3.99463564279354, 9.901794307893734, 2.0026365717083667, 4.506207187306231, 9.159092434572809, 0.39961053565188465, -2.7335121257341033, 0.43248792231032773, -2.713591214930224, -1.0126169802546432, 6.444766518351983, 9.434699741664662, 3.6748772341665, 5.300157254256423],
  'warrior_agent': [-9.206668925240766, 0.46439987693736207, -4.243421070296598, 2.500776867990586, -0.3650013841396067, -0.9365588564010352, 9.169870100641706, 8.554686947411533, 6.498323223590283, 7.535773901931282, -0.5256028433840054, -1.793645091119327, 4.7372734059884625, -6.217831834179792, -5.484159837998648, 5.732531168240643, -6.268097913929314, 1.5790775714886767, -2.0947944907594866, -7.590179691483694, 5.289212641484882],
  'magev3smarter': [-9.854581441763525, 2.657496233411372, -3.6072743836534915, -0.6478507131609952, -5.088893271660031, 7.887471404722554, 3.7086334661485125, 1.548993522919302, -5.93328226799545, -8.05241041210411, 2.913315742740263, -5.514530992036361, -0.8364601792409374, 3.1159253138681677, 2.561393716573111, -8.593355960935654, -7.591839617288403, 3.7209453403110366, -2.04326490991847, 1.0229424944333392, -5.473427125141708],
  'hunterv3smarter': [-9.245836563752468, 6.535637553159926, 5.854314844973796, 9.057238865246468, -4.791810370896094, 4.64469557202265, 8.699578386559658, 7.502711397905475, 2.292278716637421, 8.190804827802953, -0.3459011100584526, -4.977193082239277, 8.216475885171619, -2.311341131108609, -6.968293150693105, 4.263720118140705, -1.8990974760107466, 3.9559629257655526, -3.879377391895275, -7.005762213538096, -8.236311859528769],
  'warriorv3smarter': [-7.636410158099602, -5.289945697148861, -1.882124283690505, -4.975148150421651, -1.701047943799317, 7.868744892576615, 3.9166519184732103, 6.337684467437011, 4.4234049016361325, 1.2589507924678962, 6.401783861312502, -7.543752886934783, -1.8591074526400497, -8.928997965329588, -6.43569418290501, -4.530507363337004, 8.699927098013287, -6.509241118388016, -7.206145512039443, 0.07572489321879772, 6.291185934210294],
}




def play_games_stoppage(num_games, verbose_interval):
  print("Running games with p-value early stoppage")
  run_games_fixed_stoppage(num_games, 0, verbose_interval)


def play_games_parralel(num_repeats, num_games_per_core, verbose_interval=10):
  num_processors = cpu_count()
  parralel_game_results = Parallel(timeout=None, n_jobs=num_processors, verbose=100)(delayed(run_games_fixed)(num_games_per_core, i, verbose_interval) for i in range(num_repeats))
  with open("convergence_results.csv", "a+") as f:
    writer = csv.writer(f)
    # writer.writerow(("match_id", "player_deck", "player_strategy", "opponent_deck", "opponent_strategy", "status", "player_health_diff", "player_cards", "turn", "enemy_health_diff", "enemy_cards"))
    for core_result in parralel_game_results: writer.writerows(core_result)



def run_games_fixed_stoppage(num_games_per_core, rank, verbose_interval):
  class_setups = {
    "M": (Classes.MAGE, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE]),
    "H": (Classes.HUNTER, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER]),
    "W": (Classes.WARRIOR, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR])
  }
  player_class, opponent_class = "M", "W"
  player_agent_weights, opponent_agent_weights = agents['handmade_agent'], agents['handmade_agent']
  player_agent, opponent_agent = GreedyActionSmart(player_agent_weights), GreedyActionSmart(opponent_agent_weights)
  player_deck = Deck.generate_from_decklist(basic_mage)
  opponent_deck = Deck.generate_from_decklist(basic_warrior)

  (player_class_enum, player_cardset), (opponent_class_enum, opponent_cardset) = class_setups[player_class], class_setups[opponent_class]


  game_manager = GameManager()
  game_manager.build_full_game_manager(player_cardset, opponent_cardset, player_class_enum, player_deck, player_agent, opponent_class_enum, opponent_deck, opponent_agent, RandomState(None))

  game_results = []
  game_manager.create_game()
  for i in range(num_games_per_core):
    try:
      game_result = game_manager.game.play_game()
      game_results.append((rank,game_manager.player.deck.names(), player_agent_weights, game_manager.enemy.deck.names(), opponent_agent_weights)+game_result)
      player_healths = [result[6] for result in game_results]
      enemy_healths = [result[9] for result in game_results]
      if i > 1:
        tstat, pvalue = ttest_ind(player_healths, enemy_healths, equal_var=False)
        print(f"{pvalue=}")
        if pvalue < 0.05:
          print(f"Reached alpha significance at game {i}")
    except (TooManyActions, RecursionError) as e:
      game_result = None
    except Exception as e:
      print(e)
      game_result = None
    if i % verbose_interval == 0 and verbose_interval != 0:  
      print(f"{strftime('%X')}-#{rank}: {i}/{num_games_per_core} games, ({len(game_results)} success)")
    game_manager.game.reset_game()
    game_manager.game.start_game()
  return game_results



def run_games_fixed(num_games_per_core, rank, verbose_interval):
  class_setups = {
    "M": (Classes.MAGE, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE]),
    "H": (Classes.HUNTER, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER]),
    "W": (Classes.WARRIOR, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR])
  }
  player_class, opponent_class = "M", "W"
  player_agent_weights, opponent_agent_weights = agents['handmade_agent'], agents['handmade_agent']
  player_agent, opponent_agent = GreedyActionSmart(player_agent_weights), GreedyActionSmart(opponent_agent_weights)
  player_deck = Deck.generate_from_decklist(basic_mage)
  opponent_deck = Deck.generate_from_decklist(basic_warrior)

  (player_class_enum, player_cardset), (opponent_class_enum, opponent_cardset) = class_setups[player_class], class_setups[opponent_class]


  game_manager = GameManager()
  game_manager.build_full_game_manager(player_cardset, opponent_cardset, player_class_enum, player_deck, player_agent, opponent_class_enum, opponent_deck, opponent_agent, RandomState(None))

  game_results = []
  game_manager.create_game()
  for i in range(num_games_per_core):
    try:
      game_result = game_manager.game.play_game()
      game_results.append((rank,game_manager.player.deck.names(), player_agent_weights, game_manager.enemy.deck.names(), opponent_agent_weights)+game_result)
    except (TooManyActions, RecursionError) as e:
      game_result = None
    except Exception as e:
      print(e)
      game_result = None
    if i % verbose_interval == 0 and verbose_interval != 0:  
      print(f"{strftime('%X')}-#{rank}: {i}/{num_games_per_core} games, ({len(game_results)} success)")
    game_manager.game.reset_game()
    game_manager.game.start_game()
  return game_results


def run_games_random(num_games_per_core, rank, verbose_interval):
  class_setups = {
    "M": (Classes.MAGE, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE]),
    "H": (Classes.HUNTER, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER]),
    "W": (Classes.WARRIOR, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR])
  }
  player_class, opponent_class = choice(("M", "H", "W")), choice(("M", "H", "W"))
  player_agent_weights, opponent_agent_weights = [gauss(0, 10) for i in range(21)], [gauss(0, 10) for i in range(21)]
  player_agent, opponent_agent = GreedyActionSmart(player_agent_weights), GreedyActionSmart(opponent_agent_weights)
  player_deck = opponent_deck = Deck.generate_random_n_copies(2)
  (player_class_enum, player_cardset), (opponent_class_enum, opponent_cardset) = class_setups[player_class], class_setups[opponent_class]

  game_manager = GameManager()
  game_manager.build_full_game_manager(player_cardset, opponent_cardset, player_class_enum, player_deck, player_agent, opponent_class_enum, opponent_deck, opponent_agent, RandomState(None))

  game_results = []
  game_manager.create_game()
  for i in range(num_games_per_core):
    try:
      game_result = game_manager.game.play_game()
      game_results.append((rank,game_manager.player.deck.names(), player_agent_weights, game_manager.enemy.deck.names(), opponent_agent_weights)+game_result)
      if i > 1:
        player_healths = [result[6] for result in game_results]
        enemy_healths =  [result[9] for result in game_results]
        tstat, pvalue = ttest_ind(player_healths, enemy_healths, equal_var=False)
        print(f"{pvalue=}")
    except (TooManyActions, RecursionError) as e:
      game_result = None
    except Exception as e:
      print(e)
      game_result = None
    if i % verbose_interval == 0 and verbose_interval != 0:  
      print(f"{strftime('%X')}-#{rank}: {i}/{num_games_per_core} games, ({len(game_results)} success)")
    game_manager.game.reset_game()
    game_manager.game.start_game()
  return game_results


def play_games_mpi(num_games_per_core, verbose_interval=10):



  comm, num_cores, rank = (MPI.COMM_WORLD, MPI.COMM_WORLD.Get_size(), MPI.COMM_WORLD.Get_rank()) if using_mpi else (None, 1, 0)
  class_setups = {
    "M": (Classes.MAGE, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE]),
    "H": (Classes.HUNTER, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER]),
    "W": (Classes.WARRIOR, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR])
  }

  player_class, opponent_class = choice(("M", "H", "W")), choice(("M", "H", "W"))
  player_agent_weights, opponent_agent_weights = [gauss(0, 10) for i in range(21)], [gauss(0, 10) for i in range(21)]
  player_agent, opponent_agent = GreedyActionSmart(player_agent_weights), GreedyActionSmart(opponent_agent_weights)
  player_deck = opponent_deck = Deck.generate_random_n_copies(2)
  (player_class_enum, player_cardset), (opponent_class_enum, opponent_cardset) = class_setups[player_class], class_setups[opponent_class]

  game_manager = GameManager()
  game_manager.build_full_game_manager(player_cardset, opponent_cardset, player_class_enum, player_deck, player_agent, opponent_class_enum, opponent_deck, opponent_agent, RandomState(None))

  game_results = []
  game_manager.create_game()
  for i in range(num_games_per_core):
    try:
      game_result = game_manager.game.play_game()
      game_results.append((rank,game_manager.player.deck, player_agent_weights, game_manager.enemy.deck, opponent_agent_weights)+game_result)
    except (TooManyActions, RecursionError) as e:
      game_result = None
    except Exception as e:
      print(e)
      game_result = None
    if i % verbose_interval == 0 and verbose_interval != 0:  
      print(f"{strftime('%X')}-#{rank}: {i}/{num_games_per_core} games, ({len(game_results)} success)")
    game_manager.game.reset_game()
    game_manager.game.start_game()

  non_flat_results = comm.gather(game_results, root=0) if using_mpi else [game_results]

  if rank == 0:
    with open("convergence_results.csv", "w+") as f:
      writer = csv.writer(f)
      writer.writerow(("match_id", "player_deck", "player_strategy", "opponent_deck", "opponent_strategy", "status", "player_health_diff", "player_cards", "turn", "enemy_health_diff", "enemy_turns"))
      for core_result in non_flat_results: writer.writerows(core_result)

if __name__ == '__main__':
  # play_games_parralel(num_repeats=16, num_games_per_core=562, verbose_interval=10)
  play_games_stoppage(50, 1)