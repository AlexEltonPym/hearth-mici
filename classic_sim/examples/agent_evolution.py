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
    
    z = [[el[attribute_to_display] if el[attribute_to_display] != None else np.NaN for el in row] for row in self.bins]
    x = self.x_bin_ranges
    y = self.y_bin_ranges
    Zm = ma.masked_invalid(z)

    fig, ax = plt.subplots()
 
    if attribute_to_display == 'winrate':
      im = ax.pcolormesh(x, y, Zm.T[:-1, :-1], vmin=0, vmax=1, shading='flat')
    else:
      im = ax.pcolormesh(x, y, Zm.T[:-1, :-1], shading='flat')
    fig.colorbar(im, ax=ax)
    ax.set_xlabel(self.x_title)
    ax.set_ylabel(self.y_title)
    if save_file:
      plt.savefig(save_file)
    else:
      plt.show()

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

def get_sublist(lst, num_cores, core_num):
  start_index = core_num * (len(lst) // num_cores) + min(core_num, (len(lst) % num_cores))
  end_index = start_index + (len(lst) // num_cores) + (1 if core_num < (len(lst) % num_cores) else 0)
  return lst[start_index:end_index]

def evaluate(agent, agent_class, enemy_class, rank):
  enemy_agent = [-0.1, 1, -1, 1, 1, 2, 2, 1.5, 3, -3, 1, -1, 1, -1, 1, -1, 1, -1, -1, 0, 1]

  class_setups = {
    "M": (Classes.MAGE, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE], Deck.generate_from_decklist(basic_mage)),
    "H": (Classes.HUNTER, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER], Deck.generate_from_decklist(basic_hunter)),
    "W": (Classes.WARRIOR, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR], Deck.generate_from_decklist(basic_warrior))
  }

  game_manager = GameManager()
  player_class_enum, player_cardset, player_decklist = class_setups[agent_class]
  enemy_class_enum, enemy_cardset, enemy_decklist = class_setups[enemy_class]
  game_manager.build_full_game_manager(player_cardset, enemy_cardset,
                                      player_class_enum, player_decklist, GreedyActionSmart(agent),
                                      enemy_class_enum, enemy_decklist, GreedyActionSmart(enemy_agent))
  winrate, turns, health_difference, cards_in_hand = game_manager.simulate(3, silent=True, parralel=1, rng=True, rank=rank)

  return (winrate, turns, health_difference, cards_in_hand, enemy_class)

def peturb_agent(agent):
  for weight in agent:
    if uniform(0, 1) < 0.5:
      weight = weight+gauss(0, 1)

def main():
  comm = MPI.COMM_WORLD
  num_cores = comm.Get_size()
  rank = comm.Get_rank()

  number_of_generations = 30

  if rank == 0:
    initial_population_size = 64 #max 96
    map_archive = Archive("Hand size", "Turns", x_range=(0, 10), y_range=(5, 25), num_buckets=40)

  for i in range(number_of_generations):
    if rank == 0:
      start = time.time()
      print(f"\nStarting generation {i}")
      if i==0:
        population = [[gauss(0, 2.5) for i in range(21)] for j in range(initial_population_size)]
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
    print(f"Core {rank} has {len(my_population_subset)} agents to evaluate")
    my_results = [evaluate(agent, "M", enemy_class, rank) for (agent, enemy_class) in my_population_subset]
    all_results = comm.gather(my_results, root=0)
    
    if rank == 0:
      flattened_results = [result for individual_core_reponses in all_results for result in individual_core_reponses]
      recombined_results = [((flattened_results[i][j] + flattened_results[i+1][j] + flattened_results[i+2][j])/3 for j in range(4)) for i in range(0, len(flattened_results), 3)]

      print(f"Total agent results received {len(flattened_results)}, recombined to {len(recombined_results)}")
      for (winrate, turns, health_difference, cards_in_hand), agent in zip(recombined_results, population):
        map_archive.add_sample(cards_in_hand, turns, fitness=health_difference, sample=agent)
      map_archive.save()
      map_archive.display(save_file=f'data/generation{i}.png')
      end = time.time()
      print(f"Finished generation {i} total {end-start} taken")
      print(f'Most fit: {map_archive.get_most_fit()}')
      print(f'Average fitness {map_archive.get_average_fitness()}')

if __name__ == '__main__':
  main()
