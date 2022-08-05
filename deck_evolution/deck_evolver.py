from asyncio import BufferedProtocol
import os
import zipfile

from spellsource.context import Context
from tqdm import tqdm
import json
import random
import statistics

import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
import numpy as np
import numpy.ma as ma

from sklearn.neural_network import MLPRegressor

from joblib import Parallel, delayed
import multiprocessing


HUNTER_DECK = '''### HUNTER_DECK
# Class: GREEN
# Format: Standard
# 2x Arcane Shot
# 2x Stonetusk Boar
# 2x Timber Wolf
# 2x Tracking
# 2x Bloodfen Raptor
# 2x River Crocolisk
# 2x Ironforge Rifleman
# 2x Raid Leader
# 2x Razorfen Hunter
# 2x Silverback Patriarch
# 2x Houndmaster
# 2x Multi-Shot
# 2x Oasis Snapjaw
# 2x Stormpike Commando
# 2x Core Hound
#'''

MAGE_DECK = '''### MAGE_DECK
# Class: BLUE
# Format: Standard
# 2x Arcane Missiles
# 2x Murloc Raider
# 2x Arcane Explosion
# 2x Bloodfen Raptor
# 2x Novice Engineer
# 2x River Crocolisk
# 2x Arcane Intellect
# 2x Raid Leader
# 2x Wolfrider
# 2x Fireball
# 2x Oasis Snapjaw
# 2x Polymorph
# 2x Sen'jin Shieldmasta
# 2x Nightblade
# 2x Boulderfist Ogre
#'''

WARRIOR_DECK = '''### WARRIOR_DECK
# Class: RED
# Format: Standard
# 2x Boulderfist Ogre
# 2x Charge
# 2x Dragonling Mechanic
# 2x Execute
# 2x Fiery War Axe
# 2x Frostwolf Grunt
# 2x Gurubashi Berserker
# 2x Heroic Strike
# 2x Lord of the Arena
# 2x Murloc Raider
# 2x Murloc Tidehunter
# 2x Razorfen Hunter
# 2x Sen'jin Shieldmasta
# 2x Warsong Commander
# 2x Wolfrider
#'''

test_deck ='''### CONSTRUCTED_HUNTER_DECK
# Class: GREEN
# Format: Standard

# 2xSecretkeeper
# 1xVoodoo Doctor
# 1xWindfury Harpy
# 1xExplosive Trap
# 1xSpiteful Smith
# 1xStampeding Kodo
# 1xYsera
# 1xLeper Gnome
# 2xAcolyte of Pain
# 1xSnake Trap
# 1xBluegill Warrior
# 1xRazorfen Hunter
# 1xBloodfen Raptor
# 1xInjured Blademaster
# 1xKing Krush
# 1xAzure Drake
# 1xJungle Panther
# 1xSnipe
# 1xTracking
# 1xEmperor Cobra
# 1xLeeroy Jenkins
# 1xMad Bomber
# 1xMisdirection
# 1xTauren Warrior
# 1xFlesheating Ghoul
# 1xKing Mukla
# 1xOasis Snapjaw
# 1xMillhouse Manastorm
#'''

def load_cards():
  
  hunter_cards = []
  mage_cards = []
  warrior_cards = []
  all_cards = []
  id = 0

  root_path = "../internalcontent/bin/main/internalcontent/"
  file_paths = [
    "basic/hunter",
    "basic/mage",
    "basic/warrior",
    "basic/neutral",
    "classic/hunter",
    "classic/mage",
    "classic/warrior",
    "classic/neutral"
  ]
  for file_path in file_paths:
    for file_name in [file for file in os.listdir(os.path.join(root_path, file_path))]:
      with open(os.path.join(root_path, file_path, file_name), 'r') as json_file:
        data = json.load(json_file)
        if(data['collectible'] and data['type'] != "CLASS"):
          data['id'] = id
          id += 1
          all_cards.append(data)

          if data['heroClass'] == 'ANY':
            hunter_cards.append(data)
            mage_cards.append(data)
            warrior_cards.append(data)
          elif data['heroClass'] == 'GREEN':
            hunter_cards.append(data)
          elif data['heroClass'] == 'BLUE':
            mage_cards.append(data)
          else:
            warrior_cards.append(data)

  return (hunter_cards, mage_cards, warrior_cards, all_cards)

def random_deck(available_cards):
  constructed_deck = []

  while len(constructed_deck) < 30:
    added_card = random.choice(available_cards)
    num_already_in_deck = len([c for c in constructed_deck if c is added_card])
    max_allowed = 1 if added_card['rarity'] == 'LEGENDARY' else 2
    if num_already_in_deck < max_allowed:
      constructed_deck.append(added_card)
  return constructed_deck

def perturb_deck(deck, available_cards):
  num_to_remove = 0
  rand = random.random()
  
  for exponent in range(4):
    if rand < 1/(2**exponent):
      num_to_remove = exponent

  random.shuffle(deck)
  for to_remove in range(num_to_remove):
    deck.pop()
  
  while len(deck) < 30:
    added_card = random.choice(available_cards)
    num_already_in_deck = len([c for c in deck if c is added_card])
    max_allowed = 1 if added_card['rarity'] == 'LEGENDARY' else 2
    if num_already_in_deck < max_allowed:
      deck.append(added_card)
  
  return deck

def convert_deck_to_spellsource(deck, hero_class):
  already_added = []
  if hero_class == "hunter":
    CONSTRUCTED_DECK = '''### CONSTRUCTED_HUNTER_DECK
# Class: GREEN
# Format: Standard
'''
  elif hero_class == "mage":
    CONSTRUCTED_DECK = '''### CONSTRUCTED_MAGE_DECK
# Class: BLUE
# Format: Standard
'''
  else:
    CONSTRUCTED_DECK = '''### CONSTRUCTED_WARRIOR_DECK
# Class: RED
# Format: Standard
'''
  for card in deck:
    num_in_deck = len([c for c in deck if c is card])
    if card['name'] not in already_added:
      CONSTRUCTED_DECK += f"\n# {num_in_deck}x{card['name']}"
      already_added.append(card['name'])
  return CONSTRUCTED_DECK

def get_mana_curve(deck):
  mana_costs = []
  for card in deck:
    mana_costs.append(card['baseManaCost'])
  return (statistics.mean(mana_costs), statistics.variance(mana_costs))

def convert_deck_to_bag_of_cards(deck, hero_class):
  bag = [0] * 303 #(230 base cards + 70 new cards + 3 classes) * 2
  for card in deck:
    bag[int(card['id'])] += 1

  if(hero_class == 'hunter'):
    bag[-3] = 1
  elif(hero_class == 'mage'):
    bag[-2] = 1
  elif(hero_class == 'warrior'):
    bag[-1] = 1
  else:
    raise Exception("Invalid hero class")
  
  return bag

def convert_spellsource_to_bag_of_cards(deck, hero_class):
  bag = [0] * 303
  deck = [(int(card.split("x ")[0].split(" ")[1]), card.split("x ")[1]) for card in deck.split("\n")[3:-1]]
  for num, name in deck:
    for card in all_cards:
      if card['name'] == name:
        bag[card['id']] = num
  
  if(hero_class == 'hunter'):
    bag[-3] = 1
  elif(hero_class == 'mage'):
    bag[-2] = 1
  elif(hero_class == 'warrior'):
    bag[-1] = 1
  else:
    raise Exception("Invalid hero class")

  return bag


def fitness_evaluation(deck, num_games):
  if num_games == -1:
    return random.random(), random.gauss(0, 10)
  else:
    with tqdm(total=1, disable=True, leave=False, desc='           classes') as pbar:

      health_delta_vs_hunter = playtest(deck, HUNTER_DECK, int(num_games))
      pbar.update(1)
      return health_delta_vs_hunter
    #   winrate_vs_mage, health_delta_vs_mage = playtest(ctx, deck, MAGE_DECK, int(num_games/3))
    #   pbar.update(1)
    #   winrate_vs_warrior, health_delta_vs_warrior = playtest(ctx, deck, WARRIOR_DECK, int(num_games/3))
    #   pbar.update(1)

    # weighted_win_rate = winrate_vs_hunter * hunter_populatrity + winrate_vs_mage * mage_popularity + winrate_vs_warrior * warrior_popularity
    # weighted_health_delta = health_delta_vs_hunter * hunter_populatrity + health_delta_vs_mage * mage_popularity + health_delta_vs_warrior * warrior_popularity
    # return weighted_win_rate, weighted_health_delta

def playtest(player_deck, enemy_deck, num_games):
  player_stats = dict({'HEALTH_DELTA': 0,
                      'WIN_RATE': 0,
                      'DAMAGE_DEALT': 0,
                      'HEALING_DONE': 0,
                      'MANA_SPENT': 0,
                      'CARDS_PLAYED': 0,
                      'TURNS_TAKEN': 0,
                      'ARMOR_GAINED': 0,
                      'CARDS_DRAWN': 0,
                      'FATIGUE_DAMAGE': 0,
                      'MINIONS_PLAYED': 0,
                      'SPELLS_CAST': 0,
                      'HERO_POWER_USED': 0,
                      'WEAPONS_EQUIPPED': 0,
                      'WEAPONS_PLAYED': 0,
                      'CARDS_DISCARDED': 0,
                      'HERO_POWER_DAMAGE_DEALT': 0,
                      'ARMOR_LOST': 0})
  with Context() as ctx:
    player1_ai = ctx.behaviour.GameStateValueBehaviour()
    player2_ai = ctx.behaviour.GameStateValueBehaviour()

    delta_health = 0
    i = 0
    while i < num_games:
      try:
        game_context = ctx.GameContext.fromDeckLists([player_deck, enemy_deck])
        game_context.setBehaviour(ctx.GameContext.PLAYER_1, player1_ai)
        game_context.setBehaviour(ctx.GameContext.PLAYER_2, player2_ai)
        game_context.play()
        player1health = int(str(game_context.getPlayer(ctx.GameContext.PLAYER_1).getHero()).split(",")[3].split("/")[1])
        player2health = int(str(game_context.getPlayer(ctx.GameContext.PLAYER_2).getHero()).split(",")[3].split("/")[1])
        # stats = str(game_context.getPlayer(ctx.GameContext.PLAYER_1).getStatistics())
        # for stat in stats.split("\n")[1:-1]:
        #   stat_name, stat_value = tuple(stat.split(": "))
        #   if(stat_name in player_stats):
        #     player_stats[stat_name] += float(stat_value)/num_games

        # player_stats['HEALTH_DELTA'] += (player1health-player2health)/num_games
        delta_health += player1health-player2health
        i += 1
      except Exception as e:
        pass
  return delta_health / num_games

def print_deck(deck, sorted=False):
  already_printed = []
  if sorted:
    deck.sort(key=lambda card : card['baseManaCost'])
  for card in deck:
    num_in_deck = len([c for c in deck if c is card])
    if card['name'] not in already_printed:
      print(f"{card['id']}: {num_in_deck}x ({card['baseManaCost']}) {card['name']}")
    already_printed.append(card['name'])

def DSAME():
  truth_archive = Archive((0, 10), (0, 20), num_buckets=20)
  surrogate_archive = Archive((0, 10), (0, 20), num_buckets=20)
  surrogate_model = MLPRegressor(random_state=1, max_iter=500, hidden_layer_sizes=[128, 64, 32], verbose=False)
  training_buffer = [[], []]
  fittest_history = []

  for intitial in tqdm(range(elite_population), leave=False, desc='initial population'):
    hunter_sample = random_deck(hunter_cards)
    mana_mean, mana_variance = get_mana_curve(hunter_sample)
    hunter_sample_as_spellsource = convert_deck_to_spellsource(hunter_sample, 'hunter')
    whd = fitness_evaluation(hunter_sample_as_spellsource, num_games)

    truth_archive.add_sample(mana_mean, mana_variance, whd, hunter_sample)
    training_buffer[0].append(convert_deck_to_bag_of_cards(hunter_sample, 'hunter'))
    training_buffer[1].append(whd)

  for outer in tqdm(range(num_outer_loops), desc='        outer loop'):
    surrogate_model.fit(training_buffer[0], training_buffer[1])
    surrogate_archive.clear()
    for inner in tqdm(range(num_inner_loops), leave=False, desc='        inner loop'):
      if inner < elite_population:
        surrogate_elite = random_deck(hunter_cards)
      else:
        random_elite = surrogate_archive.get_random()['sample']
        surrogate_elite = perturb_deck(random_elite, hunter_cards)
      
      mana_mean, mana_variance = get_mana_curve(surrogate_elite)
      elite_as_bag = convert_deck_to_bag_of_cards(surrogate_elite, 'hunter')
      elite_as_bag = np.array(elite_as_bag)
      elite_as_bag = np.reshape(elite_as_bag, (1, -1))
      estimated_delta_health = surrogate_model.predict(elite_as_bag)
      surrogate_archive.add_sample(mana_mean, mana_variance, estimated_delta_health, surrogate_elite)

    # print(f"Simulating {len(surrogate_archive.get_elites())} elites")
    for elite in tqdm(surrogate_archive.get_elites(num_to_get=max_simulated_elites), leave=False, desc=' simulating elites'):
      elite_sample = elite['sample']
      elite_as_spellsource = convert_deck_to_spellsource(elite_sample, 'hunter')

      whd = fitness_evaluation(elite_as_spellsource, num_games)

      training_buffer[0].append(convert_deck_to_bag_of_cards(elite_sample, 'hunter'))
      training_buffer[1].append(whd)
      truth_archive.add_sample(mana_mean, mana_variance, whd, elite_sample)
    fittest_history.append(truth_archive.get_most_fit()['winrate'])

  most_fit = truth_archive.get_most_fit()
  print(fittest_history)
  print(f"Number of elites: {len(truth_archive.get_elites())}")
  print(f"Fitness: {most_fit['fitness']}")
  print(f"Winrate: {most_fit['winrate']}")
  print_deck(most_fit['sample'], sorted=True)
  return truth_archive, fittest_history, training_buffer, surrogate_model

class Archive():
  def __init__(self, x_range, y_range, num_buckets=10):
    self.num_buckets = num_buckets
    self.x_bin_ranges = []
    self.y_bin_ranges = []
    self.x_min, self.x_max = x_range
    self.y_min, self.y_max = y_range
    self.bins = [[{"fitness": None, "winrate": None, "sample": None} for x in range(self.num_buckets)] for y in range(self.num_buckets)] 
    
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
    
  def add_sample(self, x, y, fitness, sample, winrate = None):
    x_index = self.val_to_bin_index(x, 0)
    y_index = self.val_to_bin_index(y, 1)

    bin_fitness = self.bins[x_index][y_index]['fitness']
    if bin_fitness == None or bin_fitness < fitness:
      self.bins[x_index][y_index]['fitness'] = fitness
      self.bins[x_index][y_index]['winrate'] = winrate
      self.bins[x_index][y_index]['sample'] = sample

  def clear(self):
    self.bins = [[{"fitness": None, "winrate": None, "sample": None} for x in range(self.num_buckets)] for y in range(self.num_buckets)] 

  def get_elites(self, num_to_get=-1):
    all_elites = []
    for row in self.bins:
      for elite in row:
        if(elite['sample'] != None):
          all_elites.append(elite)
    if num_to_get == -1:
      return all_elites
    else:
      random.shuffle(all_elites)
      return all_elites[:num_to_get]

  def get_most_fit(self):
    return max(self.get_elites(), key = lambda x: x['fitness'])

  def get_random(self):
    return random.choice(self.get_elites())

  def display(self, display='winrate'):
    
    z = [[el[display] if el[display] != None else np.NaN for el in row] for row in self.bins]
    x = self.x_bin_ranges
    y = self.y_bin_ranges
    Zm = ma.masked_invalid(z)

    fig, ax = plt.subplots()
    if display == 'winrate':
      im = ax.pcolormesh(x, y, Zm.T[:-1, :-1], vmin=0, vmax=1, shading='flat')
    else:
      im = ax.pcolormesh(x, y, Zm.T[:-1, :-1], shading='flat')
    fig.colorbar(im, ax=ax)
    ax.set_xticks(range(0,11))
    ax.set_yticks(range(0,21,2))
    ax.set_xlabel('Mean mana-cost')
    ax.set_ylabel('Mana-cost variance')
    plt.show()



if __name__ == "__main__":
  hunter_populatrity = 0.33
  mage_popularity = 0.33
  warrior_popularity = 0.33

  elite_population = 10
  num_outer_loops = 10
  num_inner_loops = 100
  num_games = -1
  max_simulated_elites = 100

  hunter_cards, mage_cards, warrior_card, all_cards = load_cards()
  with Parallel(n_jobs=multiprocessing.cpu_count(), verbose=100) as parallel:

    archive, history, buffer, model = DSAME()
    archive.display(display='winrate')
    with open('data/buffer.json', 'w', encoding='utf-8') as f:
      json.dump(buffer, f, ensure_ascii=False, indent=4)


    # as_bag_of_cards = convert_deck_to_bag_of_cards(hunter_sample, 'hunter')

    # hunter_deck_as_bag = convert_spellsource_to_bag_of_cards(HUNTER_DECK, 'hunter')
    # mage_deck_as_bag = convert_spellsource_to_bag_of_cards(MAGE_DECK, 'mage')
    # warrior_deck_as_bag = convert_spellsource_to_bag_of_cards(WARRIOR_DECK, 'warrior')

    # combined = as_bag_of_cards + mage_deck_as_bag
    
    # print_deck(hunter_sample, sorted=True)

    # print(wwr, whd, mana_mean, mana_variance)