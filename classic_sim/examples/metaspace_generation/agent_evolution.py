import sys
sys.path.append('../')

from enums import *
from copy import deepcopy
from tqdm import tqdm
from strategy import GreedyAction, GreedyActionSmart, RandomNoEarlyPassing, RandomAction, GreedyActionSmartv1
from game_manager import GameManager
from zones import Deck
from random import uniform, gauss, shuffle, choice
import matplotlib.pyplot as plt
from IPython import display
import json

import numpy as np
import numpy.ma as ma
from statistics import mean
from joblib import Parallel, delayed
from multiprocessing import cpu_count
import time

import csv

from mpi4py import MPI


class Archive():
  def __init__(self, x_title, y_title, x_range, y_range, num_buckets=10):
    self.x_title = x_title
    self.y_title = y_title
    self.num_buckets = num_buckets
    self.x_bin_ranges = []
    self.y_bin_ranges = []
    self.x_min, self.x_max = x_range
    self.y_min, self.y_max = y_range
    self.bins = [[{"x": x, "y": y, "fitness": None, "sample": None} for x in range(self.num_buckets)] for y in range(self.num_buckets)] 
    
    for i in range(num_buckets):
      self.x_bin_ranges.append(self.x_min+(i/num_buckets)*(self.x_max-self.x_min))
      self.y_bin_ranges.append(self.y_min+(i/num_buckets)*(self.y_max-self.y_min))

  def val_to_bin_index(self, value, dimension):
    if dimension == 0:
      for index, x in enumerate(self.x_bin_ranges):
        if value < x:
          return index-1
      return len(self.x_bin_ranges)-1
    elif dimension == 1:
      for index, y in enumerate(self.y_bin_ranges):
        if value < y:
          return index-1
      return len(self.y_bin_ranges)-1
    
  def add_sample(self, x, y, fitness, sample):
    x_index = self.val_to_bin_index(x, 0)
    y_index = self.val_to_bin_index(y, 1)

    bin_fitness = self.bins[x_index][y_index]['fitness']
    if bin_fitness == None or bin_fitness < fitness:
      self.bins[x_index][y_index]['fitness'] = fitness
      self.bins[x_index][y_index]['sample'] = sample

  def clear(self):
    self.bins = [[{"x": x, "y": y, "fitness": None, "sample": None} for x in range(self.num_buckets)] for y in range(self.num_buckets)] 

  def get_elites(self, num_to_get=-1):
    all_elites = []
    for row in self.bins:
      for elite in row:
        if(elite['fitness'] != None):
          all_elites.append(elite)
    if num_to_get == -1:
      return all_elites
    else:
      shuffle(all_elites)
      return all_elites[:num_to_get]

  def get_bins(self):
    all_bins = []
    for row in self.bins:
      for elite in row:
        all_bins.append({'x': elite['x'], 'y': elite['y'],\
                         'fitness': elite['fitness'], \
                         'sample': elite['sample']})
    return all_bins
  
  def get_bins_as_string(self):
    all_bins = []
    for row in self.bins:
      for elite in row:
        
        all_bins.append({'x': elite['x'], 'y': elite['y'],\
                         'fitness': elite['fitness'], \
                         'sample': elite['sample']})
    return all_bins

  def get_most_fit(self):
    return max(self.get_elites(), key = lambda x: x['fitness'])
  def get_average_fitness(self):
    return mean([elite['fitness'] for elite in self.get_elites()])
  def get_random(self):
    return choice(self.get_elites())
  def get_total_population_count(self):
    return len(self.get_elites())

  def display(self, attribute_to_display='fitness', save_file=None):
    
    z = [[el[attribute_to_display] if el[attribute_to_display] != None else np.nan for el in row] for row in self.bins]
    x = self.x_bin_ranges
    y = self.y_bin_ranges
    Zm = ma.masked_invalid(z)

    fig, ax = plt.subplots()
 
    if attribute_to_display == 'winrate':
      im = ax.pcolormesh(x, y, Zm.T[:-1, :-1], vmin=0, vmax=1, shading='flat')
    else:
      im = ax.pcolormesh(x, y, Zm.T[:-1, :-1], vmin=-30, vmax=30, shading='flat')
    fig.colorbar(im, ax=ax)
    ax.set_xlabel(self.x_title)
    ax.set_ylabel(self.y_title)
    if save_file:
      plt.savefig(save_file)
    else:
      plt.show()
    plt.close()

  def save(self, save_file="data/map_archive.json"):
    with open(save_file, 'w', encoding='utf-8') as f:
      archive_bins_as_bag = self.get_bins_as_string()
      json.dump(archive_bins_as_bag, f, ensure_ascii=False)

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

def evaluate(agent, agent_class, enemy_class, rank):
  class_setups = {
    "M": (Classes.MAGE, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE], Deck.generate_from_decklist(basic_mage), agents['mage_agent']),
    "H": (Classes.HUNTER, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER], Deck.generate_from_decklist(basic_hunter), agents['hunter_agent']),
    "W": (Classes.WARRIOR, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR], Deck.generate_from_decklist(basic_warrior), agents['warrior_agent'])
  }

  game_manager = GameManager()
  player_class_enum, player_cardset, player_decklist, _ = class_setups[agent_class]
  enemy_class_enum, enemy_cardset, enemy_decklist, enemy_agent = class_setups[enemy_class]
  game_manager.build_full_game_manager(player_cardset, enemy_cardset,
                                      player_class_enum, player_decklist, GreedyActionSmart(agent),
                                      enemy_class_enum, enemy_decklist, GreedyActionSmart(enemy_agent))
  winrate, health_difference, cards_in_hand, turns, _, _ = game_manager.simulate(8, silent=True, parralel=1, rng=True, rank=rank)

  return (winrate, health_difference, cards_in_hand, turns, enemy_class)

def peturb_agent(agent):
  for weight in agent:
    weight = weight+gauss(0, 0.5)

def main():
  comm = MPI.COMM_WORLD
  num_cores = comm.Get_size()
  rank = comm.Get_rank()

  number_of_generations = 101

  if rank == 0:
    with open('data/generations.csv', 'w', encoding='UTF8', newline='') as f:
      writer = csv.writer(f)
      writer.writerow(["generation", "time_elapsed", "population", "mean_fitness", "best_fitness", "best_sample"])

    initial_population_size = 96 #max 96
    map_archive = Archive("Hand size", "Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40)

  for generation_number in range(number_of_generations):
    if rank == 0:
      start = time.time()
      print(f"\nStarting generation {generation_number}")
      if generation_number==0:
        population = [[uniform(-10, 10) for i in range(21)] for j in range(initial_population_size)]
        print(f"Selecting {len(population)} of {initial_population_size}")
      else:
        population = [elite['sample'] for elite in map_archive.get_elites(96)]
        print(f"Selecting {len(population)} of {map_archive.get_total_population_count()}")
      [peturb_agent(agent) for agent in population]
      tripled_population = [(elite, enemy_class) for elite in population for enemy_class in ('M', 'H', 'W')]
      print(f"Spread to {len(tripled_population)} agents")
      time.sleep(0.5)
    else:
      tripled_population = None
    tripled_population = comm.bcast(tripled_population, root=0)

    my_population_subset = get_sublist(tripled_population, num_cores, rank)
    if rank < 10:
      print(f"Core {rank} has {len(my_population_subset)} agents to evaluate")
    my_results = [evaluate(agent, "W", enemy_class, rank) for (agent, enemy_class) in my_population_subset]
    all_results = comm.gather(my_results, root=0)
    
    if rank == 0:
      flat_res = [result for individual_core_reponses in all_results for result in individual_core_reponses]
      recombined_results = [((flat_res[i][0] + flat_res[i+1][0] + flat_res[i+2][0])/3, (flat_res[i][1] + flat_res[i+1][1] + flat_res[i+2][1])/3, (flat_res[i][2] + flat_res[i+1][2] + flat_res[i+2][2])/3, (flat_res[i][3] + flat_res[i+1][3] + flat_res[i+2][3])/3) for i in range(0, len(flat_res), 3)]
      print(f"Total agent results received {len(flat_res)}, recombined to {len(recombined_results)}")
      for (winrate, health_difference, cards_in_hand, turns), agent in zip(recombined_results, population):
        map_archive.add_sample(cards_in_hand, turns, fitness=health_difference, sample=agent)
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
