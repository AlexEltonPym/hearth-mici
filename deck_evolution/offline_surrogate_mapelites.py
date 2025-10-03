## **Offline surrogate map-elites**

# Preprocess data

import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
import tensorflow as tf
import tensorflow_addons as tfa
import random
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import json
from IPython import display
from statistics import mean, variance
from itertools import combinations
from tqdm import tqdm

data = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vQQjntJiCUHUFAxlIwg8up-MMquUNfarDIZQPEfunP5S0Yr2qco8M0Om6XANEyJChS-aABMBsxnqv7n/pub?gid=1113108314&single=true&output=csv')

"""Get matchups from other players perspectives"""

flipped_data = data[['enemy', 'player', 'health', 'winrate']]
flipped_data.rename({'enemy': 'player', 'player': 'enemy'}, axis=1, inplace=True)
flipped_data['health'] = flipped_data['health'].apply(lambda x: x * -1)
flipped_data['winrate'] = flipped_data['winrate'].apply(lambda x: 1 - x)

combined = pd.concat([data, flipped_data], axis=0, ignore_index=True)

"""Split decks to bag of cards"""

card_details = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vQQjntJiCUHUFAxlIwg8up-MMquUNfarDIZQPEfunP5S0Yr2qco8M0Om6XANEyJChS-aABMBsxnqv7n/pub?gid=468949505&single=true&output=csv')

player_bag = combined['player'].astype(str).apply(lambda x: pd.Series(list(x))).astype(int)
enemy_bag  = combined['enemy'].astype(str).apply(lambda x: pd.Series(list(x))).astype(int)

simulations = pd.concat([combined[['health', 'winrate']], player_bag, enemy_bag], axis=1, ignore_index=True)

player_card_names = [f"p {card_name}" for card_name in card_details['name']]
enemy_card_names = [f"e {card_name}" for card_name in card_details['name']]
simulations.columns = ['health', 'winrate'] + player_card_names + enemy_card_names

"""# Train regression model"""

sample = simulations.copy()
winrate = sample['winrate']
health = sample['health']
sample = sample.drop('winrate', axis=1)
sample = sample.drop('health', axis=1)


X_train, X_test, y_train, y_test = train_test_split(sample, winrate, random_state=1)



model = tf.keras.Sequential([tf.keras.layers.Dense(512, activation='relu', input_dim=306),
                             tf.keras.layers.Dense(256, activation='relu'),
                             tf.keras.layers.Dense(128, activation='relu'),
                             tf.keras.layers.Dense(64, activation='relu'),
                             tf.keras.layers.Dense(32, activation='relu'),
                             tf.keras.layers.Dense(1, activation='relu'),

                             ])

model.summary()

model.compile(optimizer='adam', loss=tf.keras.losses.MeanSquaredError(), metrics=['mse', tfa.metrics.r_square.RSquare()])
stop_early = tf.keras.callbacks.EarlyStopping(monitor='val_r_square', patience=2)

history = model.fit(x=X_train, y=y_train, epochs=30, validation_data=(X_test, y_test), callbacks=[stop_early])

history_df = pd.DataFrame(history.history['loss'])
history_df.plot(title='Regressor loss')

"""#Utilities classes and functions"""




class Archive():
  def __init__(self, x_range, y_range, num_buckets=10):
    self.num_buckets = num_buckets
    self.x_bin_ranges = []
    self.y_bin_ranges = []
    self.x_min, self.x_max = x_range
    self.y_min, self.y_max = y_range
    self.bins = [[{"x": x, "y": y, "fitness": None, "sample": pd.Series()} for x in range(self.num_buckets)] for y in range(self.num_buckets)] 
    
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
    self.bins = [[{"x": x, "y": y, "fitness": None, "sample": pd.Series()} for x in range(self.num_buckets)] for y in range(self.num_buckets)] 

  def get_elites(self, num_to_get=-1):
    all_elites = []
    for row in self.bins:
      for elite in row:
        if(elite['fitness'] != None):
          all_elites.append(elite)
    if num_to_get == -1:
      return all_elites
    else:
      random.shuffle(all_elites)
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
                         'fitness': str(elite['fitness']), \
                         'sample': elite['sample'].to_json()})
    return all_bins

  def get_most_fit(self):
    return max(self.get_elites(), key = lambda x: x['fitness'])
  def get_average_fitness(self):
    return sum(self.get_elites(), key = lambda x: x['fitness'])
  def get_random(self):
    return random.choice(self.get_elites())

  def display(self, attribute_to_display='fitness'):
    
    z = [[el[attribute_to_display] if el[attribute_to_display] != None else np.nan for el in row] for row in self.bins]
    x = self.x_bin_ranges
    y = self.y_bin_ranges
    Zm = ma.masked_invalid(z)

    fig, ax = plt.subplots()
 
    if attribute_to_display == 'winrate':
      im = ax.pcolormesh(x, y, Zm.T[:-1, :-1], vmin=0, vmax=1, shading='flat')
    else:
      im = ax.pcolormesh(x, y, Zm.T[:-1, :-1], vmin=0, vmax=1, shading='flat')
    fig.colorbar(im, ax=ax)
    # ax.set_xticks(range(0,11))
    # ax.set_yticks(range(0,21,2))
    ax.set_xlabel('Mean mana-cost')
    ax.set_ylabel('Mana-cost variance')
    display.clear_output(wait=True)

    # display.display(plt)

    plt.show()

  def save(self):
    with open('/data/map_archive.json', 'w', encoding='utf-8') as f:
      archive_bins_as_bag = self.get_bins_as_string()
      json.dump(archive_bins_as_bag, f, ensure_ascii=False)

def generate_random_deck():
  rand_deck = pd.Series(0.0, index=range(153))
  for index, num in random.sample(list(enumerate(rand_deck)), 15):
    rand_deck[index] = 1.0
  return rand_deck

def generate_matchup(player_deck, enemy_deck):
  matchup_df = pd.DataFrame(columns=player_card_names+enemy_card_names)
  matchup = pd.concat([player_deck, enemy_deck])
  matchup.index=player_card_names+enemy_card_names
  matchup_df = matchup_df.append(matchup, ignore_index=True)
  return matchup_df

def perturb_deck(deck):

  rand = random.random()
  for exponent in range(6):
    if rand < 1/(2**exponent):
      num_swaps = exponent + 5

  cards_in_deck = [(index, card) for index, card in enumerate(deck) if card == 1.0]
  cards_not_in_deck = [(index, card) for index, card in enumerate(deck) if card == 0.0]

  for index, removed_card in random.sample(cards_in_deck, num_swaps):
    deck[index] = 0.0
  for index, removed_card in random.sample(cards_not_in_deck, num_swaps):
    deck[index] = 1.0
  return deck


def get_mana_stats(deck):
  mana_costs = []  
  for index, count in enumerate(deck):
    if count == 1.0:
      mana_costs.append(float(card_details['mana'][index]))
  return (mean(mana_costs), variance(mana_costs))

def get_matchups(population, matchup_size):
  random.shuffle(population)
  matchups = []
  
  for skip_size in range(matchup_size):
    for index, player in enumerate(population):
      enemy = population[(index+skip_size)%len(population)]
      matchups.append((player, enemy))
  return matchups

def convert_decklist_to_bag(decklist):
  deck_as_bag = pd.Series(0.0, index=range(153))

  for card in decklist:
    index = card_details.loc[card_details['name'] == card].index[0]
    deck_as_bag[index] = 1.0

  return deck_as_bag.astype('float32')

def convert_bag_to_decklist(bag):
  deck_as_list = []

  for index, count in enumerate(bag):
    if count == 1.0:
      deck_as_list.append(card_details['name'][index])

  return deck_as_list

def test_decklist(decklist):
  decklist = convert_decklist_to_bag(decklist)
  fitnesses = []
  for i in tqdm(range(100)):
    enemy = generate_random_deck()
    fitnesses.append(model.predict(generate_matchup(decklist, enemy))[0][0])

  return mean(fitnesses)

"""#Test decks"""

basic_hunter = ['Arcane Shot',
'Stonetusk Boar',
'Timber Wolf',
'Tracking',
'Bloodfen Raptor',
'River Crocolisk',
'Ironforge Rifleman',
'Raid Leader',
'Razorfen Hunter',
'Silverback Patriarch',
'Houndmaster',
'Multi-Shot',
'Oasis Snapjaw',
'Stormpike Commando',
'Core Hound']


test_decklist(basic_hunter)

#https://hearthstone-decks.net/face-hunter-338-legend-risewashere_hs-score-47-21/

meta_face_hunter = ['Abusive Sergeant',
                    'Arcane Shot',
                    'Argent Squire',
                    'Leper Gnome',
                    'Tracking',
                    'Worgen Infiltrator',
                    'Explosive Trap',
                    'Knife Juggler',
                    'Misdirection',
                    'Animal Companion',
                    'Arcane Golem',
                    'Eaglehorn Bow',
                    'Kill Command',
                    'Unleash the Hounds',
                    'Wolfrider']

test_decklist(meta_face_hunter)

basic = convert_decklist_to_bag(basic_hunter)
meta = convert_decklist_to_bag(meta_face_hunter)

model.predict(generate_matchup(meta, basic))

"""# Map elites

Initial population of random decks
"""


population_size = 100
matchup_size = 10
max_elites = 125
num_iterations = 200

map_archive = Archive((1, 6), (0, 20), num_buckets=20)

population = [{'index': index, 'deck': generate_random_deck(), 'fitness': 0} for index, deck_index in enumerate(range(population_size))]

matchups = get_matchups(population, matchup_size)

# for player, enemy in tqdm(matchups):
#   fitness = model.predict(generate_matchup(player['deck'], enemy['deck']))[0][0]
#   population[player['index']]['fitness'] += fitness / (matchup_size*2)
#   population[enemy['index']]['fitness'] += fitness / (matchup_size*2)
for player in population:
  fitness = model.predict(generate_matchup(player['deck'], meta))[0][0]
  population[player['index']]['fitness'] = fitness

for player in population:
  mana_mean, mana_variance = get_mana_stats(player['deck'])
  map_archive.add_sample(mana_mean, mana_variance, player['fitness'], player['deck'])

map_archive.save()
map_archive.display('fitness')

"""Iterativly perturb elites for next generation"""

fitness_history = []
fitness_average_history = []
for i in tqdm(range(num_iterations)):
  population = [{'index': index, 'deck': perturb_deck(elite['sample']), 'fitness': 0} for index, elite in enumerate(map_archive.get_elites(num_to_get = max_elites))]

  matchups = get_matchups(population, matchup_size)

  # for player, enemy in matchups:
  #   fitness = model.predict(generate_matchup(player['deck'], enemy['deck']))[0][0]
  #   population[player['index']]['fitness'] += fitness / (matchup_size*2)
  #   population[enemy['index']]['fitness'] += fitness / (matchup_size*2)
  for player in population:

    fitness = model.predict(generate_matchup(player['deck'], meta))[0][0]
    population[player['index']]['fitness'] = fitness

  for player in population:
    mana_mean, mana_variance = get_mana_stats(player['deck'])
    map_archive.add_sample(mana_mean, mana_variance, player['fitness'], player['deck'])

  fitness_history.append(map_archive.get_most_fit()['fitness'])
  fitness_average_history.append(map_archive.get_average_fitness())
  map_archive.display('fitness')
  pd.DataFrame(fitness_history, fitness_average_history).plot()


map_archive.save()

pd.DataFrame(fitness_history).plot()

most_fit = map_archive.get_most_fit()

print(f"Fitness: {most_fit['fitness']}")
convert_bag_to_decklist(most_fit['sample'])