from asyncio import BufferedProtocol
import os
import zipfile

from tqdm import tqdm
import json
import csv
import random
import statistics
import time

import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
import numpy as np
import numpy.ma as ma

from sklearn.neural_network import MLPRegressor

from joblib import Parallel, delayed
import multiprocessing
from subprocess import run, PIPE

DOTNET_DIR = 'dotnet'#'/home/ubuntu/.dotnet/dotnet'
SABBERSTONE_DIR = '../SabberStone/core-extensions/SabberStoneCoreConsole/bin/Debug/netcoreapp2.1/SabberStoneCoreConsole.dll'
NUM_GAMES = 100
NUM_DECKS = 160
hunter_available_cards = []

def get_bag(deck):
  as_bag = [str(0)] * 153
  for card in deck:
    card_id = hunter_available_cards.index(card)
    as_bag[card_id] = str(1)
  return "".join(as_bag)

def random_deck(available_cards):
  return random.sample(available_cards, 15)

def fitness_evaluation(player_deck, enemy_deck):
  deck_string=",".join(player_deck + enemy_deck)
  subp = run([DOTNET_DIR, SABBERSTONE_DIR, str(NUM_GAMES)], \
  stdout=PIPE, input=deck_string, \
  encoding='ascii')
  health_difference, winrate = subp.stdout.split(",")

  player_deck_as_bag = get_bag(player_deck)
  enemy_deck_as_bag = get_bag(enemy_deck)
  with open('results.out', 'a') as outfile:
    print(f"{player_deck_as_bag},{enemy_deck_as_bag},{health_difference},{winrate}", end="", file=outfile)

def main():
  global hunter_available_cards
  with open('sabber_hunter_cards_no_leg.txt', 'r') as f:
    hunter_available_cards = [line.strip() for line in f]

  decks_to_test = []
  for i in range(NUM_DECKS):
    player_deck = random_deck(hunter_available_cards)
    enemy_deck = random_deck(hunter_available_cards)
    decks_to_test.append((player_deck, enemy_deck))
    

  start = time.time()

  with Parallel(n_jobs=multiprocessing.cpu_count(), verbose=100) as parallel:
    parallel(delayed(fitness_evaluation)(player_deck, enemy_deck) for player_deck, enemy_deck in decks_to_test)
  
  end = time.time()
  print(f"elapsed: {end-start}")

if __name__ == '__main__':
  main()
