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
from tqdm import tqdm


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

def evaluate(agent, agent_class):
  enemy_agent = [-0.1, 1, -1, 1, 1, 2, 2, 1.5, 3, -3, 1, -1, 1, -1, 1, -1, 1, -1, -1, 0, 1]

  class_setups = {"mage": ([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE], Classes.MAGE, Deck.generate_from_decklist(basic_mage)),
  "hunter": ([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER], Classes.HUNTER, Deck.generate_from_decklist(basic_hunter)),
  "warrior": ([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR], Classes.WARRIOR, Deck.generate_from_decklist(basic_warrior))}

  player_cardset, player_class_enum, player_decklist = class_setups[agent_class]
  
  game_manager = GameManager()

  game_results = []
  for enemy_class in class_setups:
    enemy_cardset, enemy_class_enum, enemy_decklist = class_setups[enemy_class]
    game_manager.build_full_game_manager(player_cardset, enemy_cardset,
                                        player_class_enum, player_decklist, GreedyActionSmart(agent),
                                        enemy_class_enum, enemy_decklist, GreedyActionSmart(enemy_agent))
    game_results.append(game_manager.simulate(2, silent=True, parralel=1, rng=True))

  winrate = sum([game_results[i][0] for i in range(3)])/3
  turns = sum([game_results[i][1] for i in range(3)])/3
  health_difference = sum([game_results[i][2] for i in range(3)])/3
  winrate_range = max([game_results[i][0] for i in range(3)])-min([game_results[i][0] for i in range(3)])
  return (winrate, turns, health_difference, winrate_range)

def peturb_agent(agent):
  for weight in agent:
    if uniform(0, 1) < 0.5:
      weight = weight+gauss(0, 1)

def evolve(agent):
  peturb_agent(agent)
  return evaluate(agent, "mage")  

def main():
  comm = MPI.COMM_WORLD
  num_cores = comm.Get_size()
  rank = comm.Get_rank()

  if rank == 0:
    initial_population_size = 2
    number_of_generations = 10
    map_archive = Archive("Winrate difference", "Turns", x_range=(0, 1), y_range=(5, 25), num_buckets=40)

  for i in range(number_of_generations+1):
    print(f"Starting generation {i}")
    if rank == 0:
      if i==0:
        population = [[gauss(0, 2.5) for i in range(21)] for j in range(initial_population_size)]
      else:
        population = [elite['sample'] for elite in map_archive.get_elites()]
    
    population = comm.bcast(population, root=0)

    my_population_subset = get_sublist(population, num_cores, rank)
    my_results = [evolve(agent) for agent in my_population_subset]
    all_results = comm.gather(my_results, root=0)

    if rank == 0:
      for (winrate, turns, health_difference, winrate_range), agent in zip(all_results, population):
        map_archive.add_sample(winrate_range, turns, fitness=health_difference, sample=agent)
      map_archive.save()
      map_archive.display(save_file=f'data/generation{i}.png')
      print(f'Most fit: {map_archive.get_most_fit()}')
      print(f'Average fitness {map_archive.get_average_fitness()}')
      print(f'Population size: {len(population)}')

if __name__ == '__main__':
  main()
