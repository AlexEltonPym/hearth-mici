import sys
sys.path.append('../../src/')
sys.path.append('../map_elites')

from enums import *
from copy import deepcopy
from tqdm import tqdm
from strategy import GreedyAction, GreedyActionSmart, RandomNoEarlyPassing, RandomAction, GreedyActionSmartv1
from game_manager import GameManager
from zones import Deck
from random import uniform, gauss, shuffle, choice, random, randint
import matplotlib.pyplot as plt
from IPython import display
import json

import numpy as np
import numpy.ma as ma
from statistics import mean
from joblib import Parallel, delayed
from multiprocessing import cpu_count
import time

import ast


import csv

from map_elites import Archive

try:
  from mpi4py import MPI
except ModuleNotFoundError:
  pass

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



def get_sublist(lst, num_cores, core_num):
  start_index = core_num * (len(lst) // num_cores) + min(core_num, (len(lst) % num_cores))
  end_index = start_index + (len(lst) // num_cores) + (1 if core_num < (len(lst) % num_cores) else 0)
  return lst[start_index:end_index]

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

def evaluate(elite, agent_class, enemy_class, enemy_policy, agent_only, num_games_per_matchup):
  agent, deck = elite
  class_setups = {
    "M": (Classes.MAGE, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE], Deck.generate_from_decklist(basic_mage), agents['handmade_agent']),
    "H": (Classes.HUNTER, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER], Deck.generate_from_decklist(basic_hunter), agents['handmade_agent']),
    "W": (Classes.WARRIOR, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR], Deck.generate_from_decklist(basic_warrior), agents['handmade_agent'])
  }

  game_manager = GameManager()
  player_class_enum, player_cardset, player_default_deck, _ = class_setups[agent_class]
  if agent_only:
    player_decklist = player_default_deck
  else:
    player_decklist = Deck.generate_from_decklist(deck)
  enemy_class_enum, enemy_cardset, enemy_decklist, _ = class_setups[enemy_class]
  enemy_agent = enemy_policy
  if num_games_per_matchup == -1:
    winrate = random()
    health_difference = uniform(-30, 30)
    cards_in_hand = uniform(0, 9)
    turns = uniform(10, 20)
  else:
    game_manager.build_full_game_manager(player_cardset, enemy_cardset,
                                      player_class_enum, player_decklist, GreedyActionSmart(agent),
                                      enemy_class_enum, enemy_decklist, GreedyActionSmart(enemy_agent))
    winrate, player_health, cards_in_hand, turns, enemy_health, enemy_cards_in_hand = game_manager.simulate(num_games_per_matchup, silent=True, parralel=1, rng=True)
    health_difference = player_health - enemy_health
  return (winrate, health_difference, cards_in_hand, turns)

def peturb_agent_and_deck(individual, player_class, agent_only):
  agent, deck = individual
  
  agent = list(map(lambda weight: weight+gauss(0, 0.5), agent))

  if not agent_only:
    num_to_remove = 0
    rand = random()
    for exponent in range(4):
      if rand < 1/(2**exponent):
        num_to_remove = exponent

    pool = get_available_cards(player_class)

    for i in range(num_to_remove):
      selected_card = randint(0, 14)
      selected_card_name = deck[selected_card*2]
      new_card = choice([card for card in pool if card != selected_card_name and card not in deck])

      deck[selected_card*2] = new_card
      deck[selected_card*2+1] = new_card
  return (agent, deck)

def main():
  start_generation = 0
  end_generation = 301
  player_class = "H"
  load_from_file = False
  agent_only = False
  initial_population_size = 38 #max 96/38
  max_selection_count = 38
  num_games_per_matchup = 3 #if -1, dummy games are played

  if load_from_file:
    with open('data/generations.csv', 'r', encoding='UTF8') as f:
      reader = csv.reader(f, delimiter=',')
      for row in reader:
        generation_offset = row[0]
      start_generation += int(generation_offset)+1
  else:
    with open('data/generations.csv', 'w', encoding='UTF8', newline='') as f:
      writer = csv.writer(f)
      writer.writerow(["generation", "time_elapsed", "population", "mean_fitness", "best_fitness", "best_sample"])

  map_archive = Archive("Hand size", "Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40)

  if load_from_file:
    try:
      map_archive.load(f'data/generation{start_generation-1}_archive.json')
    except:
      map_archive.load('data/map_archive.json')

  gauntlet = []
  with open('gauntlet.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    headers = next(reader)
    for row in reader:
      sample = ast.literal_eval(str(row[6:])[1:-1].replace(" ","").replace("[", "").replace("]", ""))
      sample = [float(value) for value in sample]
      gauntlet.append({headers[0]: row[0], headers[1]: row[1], headers[2]: row[2], headers[3]: row[3], headers[4]: row[4], headers[5]: row[5], headers[6]: sample})

  with Parallel(timeout=None, n_jobs=10, verbose=100) as para:
    for generation_number in range(start_generation, end_generation):
      start = time.time()
      print(f"\nStarting generation {generation_number}")
      if generation_number==0:
        population = [([gauss(0, 10) for i in range(21)], generate_random_deck(player_class)) for j in range(initial_population_size)]
        print(f"Selecting {len(population)} of {initial_population_size}")
      else:
        population = [elite['sample'] for elite in map_archive.get_elites(max_selection_count, unique_only=True, only_consider_policy=agent_only)]
        print(f"Selecting {len(population)} of {map_archive.get_total_population_count()}")
      population = [peturb_agent_and_deck(individual, player_class, agent_only) for individual in population]
      matchups = [(elite, enemy['agent_class'], enemy['sample']) for elite in population for enemy in gauntlet]
      print(f"Spread to {len(matchups)} matchups")
      # my_results = [evaluate(elite, player_class, enemy_class, enemy_policy, agent_only, num_games_per_matchup) for (elite, enemy_class, enemy_policy) in matchups]
      my_results = para(delayed(evaluate)(elite, player_class, enemy_class, enemy_policy, agent_only, num_games_per_matchup) for (elite, enemy_class, enemy_policy) in matchups)

      recombined_results = [my_results[i:i+15]for i in range(0, len(my_results), 15)] #there are 15 agents in the gauntlet
      recombined_results = [(mean(column) for column in list(zip(*result))) for result in recombined_results]

      print(f"Total agent results received {len(my_results)}, recombined to {len(recombined_results)}")

      for (winrate, health_difference, cards_in_hand, turns), agent in zip(recombined_results, population):
        map_archive.add_sample(cards_in_hand, turns, fitness=health_difference, sample=agent)
      map_archive.save(save_file=f'data/generation{generation_number}_archive.json')
      map_archive.save()
      map_archive.display(save_file=f'data/generation{generation_number}.png')
      end = time.time()
      print(f"Finished generation {generation_number} total {end-start} taken")
      print(f'Most fit: {map_archive.get_most_fit()}')
      print(f'Average fitness {map_archive.get_average_fitness()}')
      with open('data/generations.csv', 'a', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([generation_number, end-start, map_archive.get_total_population_count(), map_archive.get_average_fitness(), map_archive.get_most_fit()['fitness'],  map_archive.get_most_fit()['sample']])

if __name__ == '__main__':
  main()
