import sys
sys.path.append('../')

from random import shuffle, choice
import matplotlib.pyplot as plt
import json
from statistics import mean
import numpy as np
import numpy.ma as ma
from colorhash import ColorHash


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
    if attribute_to_display == 'colorhash':
      z = [[tuple(np.uint8(np.array(ColorHash(elite['sample']).rgb))) if elite['sample'] != None else tuple(np.uint8(np.array((255, 255, 255)))) for elite in row] for row in self.bins]
    else:
      z = [[el[attribute_to_display] if el[attribute_to_display] != None else np.NaN for el in row] for row in self.bins]
    x = self.x_bin_ranges
    y = self.y_bin_ranges

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
    
    if attribute_to_display != 'colorhash':
      fig.colorbar(im, ax=ax)
    ax.set_xlabel(self.x_title)
    ax.set_ylabel(self.y_title)
    fig.set_figheight(5)
    fig.set_figwidth(5)
    if save_file:
      plt.savefig(save_file)
    else:
      plt.show()
    plt.close()

  def save(self, save_file="data/map_archive.json"):
    with open(save_file, 'w', encoding='utf-8') as f:
      archive_bins_as_bag = self.get_bins_as_string()
      json.dump(archive_bins_as_bag, f, ensure_ascii=False)

  def load(self, save_file="data/map_archive.json"):
    with open(save_file, 'r', encoding='utf-8') as f:
      archive_json = json.load(f)
      for entry in archive_json:
        self.bins[entry['x']][entry['y']]['fitness'] = entry['fitness']
        self.bins[entry['x']][entry['y']]['sample'] = entry['sample']

