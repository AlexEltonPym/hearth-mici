import sys
sys.path.append('../')

from random import shuffle, choice
import matplotlib.pyplot as plt
import json
from statistics import mean
import numpy as np
import numpy.ma as ma
from colorhash import ColorHash
from math import dist

from sklearn.cluster import HDBSCAN
from enums import CardSets
from card_sets import build_pool

def get_pool():
  pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR], None)
  pool = [card.name for card in pool]
  return pool

def bags_from_decks(decks):
  pool = get_pool()

  bags = []
  for deck in decks:
    bag = np.zeros(len(pool))
    for card in deck:
      index = pool.index(card)
      bag[index] = 1
    bags.append(bag)
  return bags

def stretch(n, start1, stop1, start2, stop2):
  return (n - start1) / (stop1 - start1) * (stop2 - start2) + start2

class Archive():
  def __init__(self, x_title, y_title,  x_range, y_range, num_buckets=10, archive_name="", title_color="black"):
    self.archive_name = archive_name
    self.x_title = x_title
    self.y_title = y_title
    self.title_color = title_color
    self.num_buckets = num_buckets
    self.x_bin_ranges = []
    self.y_bin_ranges = []
    self.x_min, self.x_max = x_range
    self.y_min, self.y_max = y_range
    self.bins = [[{"x_index": x, "y_index": y, "x_value": None, "y_value": None, "fitness": None, "sample": None} for y in range(self.num_buckets)] for x in range(self.num_buckets)] 
    
    for i in range(num_buckets):
      self.x_bin_ranges.append(self.x_min+(i/num_buckets)*(self.x_max-self.x_min))
      self.y_bin_ranges.append(self.y_min+(i/num_buckets)*(self.y_max-self.y_min))

  def x_value_to_bin_index(self, x_value):
    for index, x in enumerate(self.x_bin_ranges):
      if x_value < x:
        return index-1
    return len(self.x_bin_ranges)-1

  def y_value_to_bin_index(self, y_value):
    for index, y in enumerate(self.y_bin_ranges):
      if y_value < y:
        return index-1
    return len(self.y_bin_ranges)-1
  
  def values_to_bin_index(self, value_x, value_y):
    x_index = self.x_value_to_bin_index(value_x)
    y_index = self.y_value_to_bin_index(value_y)
    return x_index, y_index
    
  def indices_to_value(self, indices):
    x_value = self.x_bin_ranges[indices[0]]
    y_value = self.y_bin_ranges[indices[1]]
    return x_value, y_value

  def vals_to_entry(self, x_value, y_value, missing_behaviour="none"):
    x_index, y_index = self.values_to_bin_index(x_value, y_value)
    found_value = self.bins[x_index][y_index]
    if missing_behaviour == "none":
      return found_value
    elif missing_behaviour == "closest":
      elites = self.get_elites()
      shortest_distance, closest_elite = sys.maxsize, None
      for elite in elites:
        current_distance = dist((x_index, y_index), (elite['x_index'], elite['y_index']))
        if current_distance < shortest_distance:
          shortest_distance, closest_elite = current_distance, elite
      return closest_elite
    
  def transform_from_real_space(self, x_value, y_value):
    x_min, x_max, y_min, y_max = self.get_range()

    transformed_x = stretch(x_value, 0, 40, x_min, x_max)
    transformed_y = stretch(y_value, 0, 40, y_min, y_max)
    return transformed_x, transformed_y

  def transform_from_real_space_to_scale(self, x_value, y_value):
    x_min, x_max, y_min, y_max = self.get_range()

    transformed_x = stretch(x_value, 0, 40, x_min, x_max) - x_min
    transformed_y = stretch(y_value, 0, 40, y_min, y_max) - y_min
    return transformed_x, transformed_y

  def add_sample(self, x_value, y_value, fitness, sample):
    x_index, y_index = self.values_to_bin_index(x_value, y_value)

    bin_fitness = self.bins[x_index][y_index]['fitness']
    if bin_fitness == None or bin_fitness < fitness:
      self.bins[x_index][y_index]['fitness'] = fitness
      self.bins[x_index][y_index]['sample'] = sample
      self.bins[x_index][y_index]['x_value'] = x_value
      self.bins[x_index][y_index]['y_value'] = y_value

  def clear(self):
    self.bins = [[{"x_index": x, "y_index": y, "x_value": None, "y_value": None, "fitness": None, "sample": None} for y in range(self.num_buckets)] for x in range(self.num_buckets)] 

  def get_elites(self, num_to_get=-1, unique_only=False, only_consider_policy=False):
    all_elites = []
    for row in self.bins:
      for elite in row:
        if(elite['fitness'] != None):
          all_elites.append(elite)

    if unique_only:
      shuffle(all_elites)
      unique_elites = []
      keys_set = set()
      for elite in all_elites:
        if only_consider_policy:
          key = tuple(elite['sample'][0])
        else:
          key = tuple(elite['sample'][0]+elite['sample'][1])

        if key not in keys_set:
          keys_set.add(key)
          unique_elites.append(elite)

    if num_to_get == -1:
      return unique_elites if unique_only else all_elites 
    else:
      shuffle(all_elites)
      return unique_elites[:num_to_get] if unique_only else all_elites[:num_to_get]


  def get_bins(self):
    all_bins = []
    for row in self.bins:
      for elite in row:
        all_bins.append({'x_index': elite['x_index'], 'y_index': elite['y_index'],\
                         'x_value': elite['x_value'], 'y_value': elite['y_value'],\
                         'fitness': elite['fitness'], 'sample': elite['sample']})
    return all_bins
  
  def get_most_fit(self):
    return max(self.get_elites(), key=lambda elite: elite['fitness'])
  def get_average_fitness(self):
    return mean([elite['fitness'] for elite in self.get_elites()])
  def get_random(self):
    return choice(self.get_elites())
  def get_total_population_count(self):
    return len(self.get_elites())
  def get_range(self):
    return self.x_min, self.x_max, self.y_min, self.y_max

  def assign_clusters(self):
    elites = self.get_elites(-1, False)
    elites = sorted(elites, key=lambda elite: elite['fitness']) #for anti-randomness
    strats = np.array([elite['sample'][0] for elite in elites])
    decks = np.array([elite['sample'][1] for elite in elites])
    bags = bags_from_decks(decks)
    x = np.array([np.append(strat, deck) for (strat, deck) in zip(strats, bags)])
    hdbscan_clusters = HDBSCAN(min_cluster_size=20).fit(x).labels_
    for elite, cluster_label in zip(elites, hdbscan_clusters):
      elite['hdbscan'] = cluster_label



  def get_graph(self):
    z = [[el['fitness'] if el['fitness'] != None else np.NaN for el in row] for row in self.bins]
    x = self.x_bin_ranges
    y = self.y_bin_ranges
    Zm = ma.masked_invalid(z)
    return x, y, Zm

  def display(self, attribute_to_display='fitness', save_file=None, fig=None, ax=None, dont_show=False):
    if attribute_to_display == 'colorhash':
      z = [[tuple(np.uint8(np.array(ColorHash(elite['sample']).rgb))) if elite['sample'] != None else tuple(np.uint8(np.array((255, 255, 255)))) for elite in row] for row in self.bins]
    elif attribute_to_display == 'hdbscan':
      self.assign_clusters()
      z = [[elite['hdbscan'] if elite['sample'] != None else np.NaN for elite in row] for row in self.bins]
    else:
      z = [[el[attribute_to_display] if el[attribute_to_display] != None else np.NaN for el in row] for row in self.bins]
    x = self.x_bin_ranges
    y = self.y_bin_ranges

    if fig == None or ax == None:
      fig, ax = plt.subplots()
 
    if attribute_to_display == 'winrate':
      Zm = ma.masked_invalid(z)
      im = ax.pcolormesh(x, y, Zm.T[:-1, :-1], vmin=0, vmax=1, shading='flat')
    elif attribute_to_display == 'fitness':
      Zm = ma.masked_invalid(z)
      im = ax.pcolormesh(x, y, Zm.T[:-1, :-1], vmin=-30, vmax=30, shading='flat')
    elif attribute_to_display == 'colorhash':
      z = np.array(z)
      im = ax.pcolormesh(x, y, np.transpose(z, (1, 0, 2))[:-1, :-1,:])
    elif attribute_to_display == 'hdbscan':
      Zm = ma.masked_invalid(z)
      im = ax.pcolormesh(x, y, Zm.T[:-1, :-1], cmap="tab20", shading='flat')

    
    if attribute_to_display != 'colorhash':
      fig.colorbar(im, ax=ax)
    ax.set_xlabel(self.x_title)
    ax.set_ylabel(self.y_title)
    ax.set_title(self.archive_name.capitalize())

    if save_file:
      fig.set_figheight(4)
      fig.set_figwidth(5)
      plt.savefig(save_file)
      plt.close()

    elif not dont_show:
      fig.set_figheight(4)
      fig.set_figwidth(5)
      plt.show()
      plt.close()
      

  def save(self, save_file="data/map_archive.json"):
    with open(save_file, 'w', encoding='utf-8') as f:
      archive_bins = self.get_bins()
      json.dump(archive_bins, f, ensure_ascii=False)

  def load(self, save_file="data/map_archive.json"):
    with open(save_file, 'r', encoding='utf-8') as f:
      archive_json = json.load(f)
      for entry in archive_json:
        self.bins[entry['x_index']][entry['y_index']]['fitness'] = entry['fitness']
        self.bins[entry['x_index']][entry['y_index']]['sample'] = entry['sample']
        self.bins[entry['x_index']][entry['y_index']]['x_value'] = entry['x_value']
        self.bins[entry['x_index']][entry['y_index']]['y_value'] = entry['y_value']

  def compatability_load(self, save_file="data/map_archive.json"):
    with open(save_file, 'r', encoding='utf-8') as f:
      archive_json = json.load(f)
      for entry in archive_json:
        self.bins[entry['x']][entry['y']]['fitness'] = entry['fitness']
        self.bins[entry['x']][entry['y']]['sample'] = entry['sample']
        x_value, y_value = self.indices_to_value((entry['x'], entry['y']))
        self.bins[entry['x']][entry['y']]['x_value'] = x_value
        self.bins[entry['x']][entry['y']]['y_value'] = y_value