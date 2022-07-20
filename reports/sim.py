
import multiprocessing as mp
import time
from spellsource.utils import simulate
from spellsource.context import Context
import json
import csv
import pprint
import os
from statistics import mean
from deck_lists import *
from itertools import combinations
import pyfiglet
from fpdf import FPDF
import math
from filelock import FileLock
from tqdm import tqdm
import sys


def generate_custom_card(attack, hp, mana, taunt, lifesteal, charge):

  generated_card = {
    "baseManaCost": mana,
    "baseHp": hp,
    "baseAttack": attack,
    "attributes": {
        "TAUNT": taunt,
        "LIFESTEAL": lifesteal,
        "CHARGE": charge
    },
    "name": "Custom Card",
    "type": "MINION",
    "rarity": "COMMON",
    "description": "A custom card",
    "collectible": True,
    "set": "CUSTOM",
    "fileFormatVersion": 1
  }

  return json.dumps(generated_card)

def run_with_context(num_games, custom_cards, decks):

  with Context() as context:
    for c in custom_cards:
      context.CardCatalogue.addOrReplaceCard(c)
    test_results = list(simulate(context=context, decks=decks, number=num_games, behaviours=['GameStateValueBehaviour', 'GameStateValueBehaviour'], reduce=False))
    return test_results

def get_stats(game_results, perspective):
  perspective = perspective.split('### ')[1].split('\n')[0]
  player_results = [game['results'][game['decks'].index(perspective)] for game in game_results]
  

  player_stats = dict({'WIN_RATE': 0,
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

  player_stats_deviations = dict({'WIN_RATE': 0,
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
  # for game_result in player_results:
  #   for x, y in player_stats.items():
  #     player_stats[x] = 0
  for game_result in player_results:
    for i, j in game_result.items():
      for x, _ in player_stats.items():
        if i == x:
          player_stats[i] += j


  for x, _ in player_stats.items():
    player_stats[x] = round(player_stats[x]/len(player_results), 30)

  for game_result in player_results:
    for i, j in game_result.items():
      for x, _ in player_stats_deviations.items():
        if i == x:
          player_stats_deviations[i] += pow(j - player_stats[i], 2)
  
  for x, _ in player_stats_deviations.items():
    player_stats[x] = (player_stats[x], math.sqrt(player_stats_deviations[x]/len(player_results)))

  return [(x, y) for x, y in player_stats.items() if x == 'WIN_RATE' or y != 0]

def tryout(num_games, decks, custom_cards):

  #todo check JobLib.parralel threading
  # pool = mp.Pool(8)
  # result_objects = [pool.apply_async(run_with_context, (3, custom_cards, decks)) for i in range(8)]
  # pool.close()
  # pool.join()
  # results = [get_stats(r.get(), decks[0]) for r in result_objects]

  #from perspective of deck 0
  stats = get_stats(run_with_context(num_games, custom_cards, decks), decks[0])
  return stats

def progressive_tryout(games_to_sim_list, decks, custom_cards = []):
  stats = []
  for games_to_sim in games_to_sim_list:

    #print(f"Simulating {games_to_sim} games on {processors_to_use}/{max_processors} cores ({games_to_sim * processors_to_use} games)")

    stats.append(tryout(games_to_sim, decks, custom_cards))
    # total_wins = sum([wins for (wins, games) in win_rates])
    # total_games = sum([games for (wins, games) in win_rates])
    #print(f"{total_games} games simulated so far")
    #print(f"{round(total_wins/total_games, 2)}")

  return stats

def send_to_database(user, card_id, games_played, player, enemy, stats):
  
  with FileLock("../../hearth-mici/reports/database.json.lock"):
    with open('../../hearth-mici/reports/database.json', 'r') as database_file:
      entry_name = f"{user}_{card_id}_{player}_v_{enemy}"
      database = json.load(database_file)

      database[entry_name] = {}
      database[entry_name]["user"] = user
      database[entry_name]["card_id"] = card_id
      database[entry_name]["games_played"] = games_played
      database[entry_name]["player"] = player
      database[entry_name]["enemy"] = enemy
      database[entry_name]["stats"] = stats


    with open('../../hearth-mici/reports/database.json', 'w') as database_file:
      json.dump(database, database_file)


def experiment_all_custom_card_combos():
  print("attack, health, mana, winrate")
  for enemy_deck in [DRUID_DECK]:
    for player_deck in [MAGE_DECK]:
      for test_attack in range(1, 11):
        for test_health in range(1, 11):
          for test_mana in range(1, 11):
            player_deck_title = player_deck.split('\n', 1)[0][4:]
            enemy_deck_title = enemy_deck.split('\n', 1)[0][4:]

            print(f"{player_deck_title} vs {enemy_deck_title}")
            custom_card = generate_custom_card(test_attack, test_health, test_mana, False, False, False)
            stats = progressive_tryout([2], [enemy_deck, player_deck], [custom_card])
            print(f"{test_attack}, {test_health}, {test_mana}")

def experiment_baselines():
  all_nine_basic_decks = [PRIEST_DECK, DRUID_DECK, HUNTER_DECK, MAGE_DECK, PALADIN_DECK, ROUGE_DECK, SHAMAN_DECK, WARLOCK_DECK, WARRIOR_DECK]
  
  for count, (player_deck, enemy_deck) in enumerate(combinations(all_nine_basic_decks, 2)):
    #from perspective of deck 0
    if count >= 1:
      # print(player_deck, enemy_deck)

      wr = progressive_tryout([1000], [player_deck, enemy_deck])

      player_deck_name = player_deck.split("\n")[0].split(" ")[1]
      enemy_deck_name = enemy_deck.split("\n")[0].split(" ")[1]
      print(f"{player_deck_name},{enemy_deck_name},{wr}")

def experiment_minimeta():
  mini_metagame = [HUNTER_DECK, WARRIOR_DECK, MAGE_DECK]
  for (player_deck, enemy_deck) in combinations(mini_metagame, 2):
    #from perspective of deck 0
    wr = progressive_tryout([3], [player_deck, enemy_deck])

    player_deck_name = player_deck.split("\n")[0].split(" ")[1]
    enemy_deck_name = enemy_deck.split("\n")[0].split(" ")[1]
    print(f"{player_deck_name},{enemy_deck_name},{wr}")

def experiment_impact():
  print("mage v hunter")
  # print("baseline")
  print(progressive_tryout([99], [MAGE_DECK, HUNTER_DECK], 1, 1, 10, False, False, False))
  # print("with 6 bad cards")
  # print(progressive_tryout([9], [MAGE_DECK_6_CUSTOM, HUNTER_DECK], 1, 1, 10, False, False, False))
  # print("with 4 bad cards")
  # print(progressive_tryout([9], [MAGE_DECK_4_CUSTOM, HUNTER_DECK], 1, 1, 10, False, False, False))
  # print("with 2 bad cards")
  # print(progressive_tryout([9], [MAGE_DECK_2_CUSTOM, HUNTER_DECK], 1, 1, 10, False, False, False))
  # print("with 6 good cards")
  # print(progressive_tryout([9], [MAGE_DECK_6_CUSTOM, HUNTER_DECK], 10, 10, 1, False, False, False))
  # print("with 4 good cards")
  # print(progressive_tryout([9], [MAGE_DECK_4_CUSTOM, HUNTER_DECK], 10, 10, 1, False, False, False))
  # print("with 2 good cards")
  # print(progressive_tryout([9], [MAGE_DECK_2_CUSTOM, HUNTER_DECK], 10, 10, 1, False, False, False))
  # print("with 2 4/4s")
  print(progressive_tryout([99], [MAGE_DECK_2_CUSTOM, HUNTER_DECK], 4, 4, 5, False, False, False))
  # print("with 2 5/5s")
  print(progressive_tryout([99], [MAGE_DECK_2_CUSTOM, HUNTER_DECK], 5, 5, 5, False, False, False))
  # print("with 2 6/6s")
  print(progressive_tryout([99], [MAGE_DECK_2_CUSTOM, HUNTER_DECK], 6, 6, 5, False, False, False))
  
def experiment_histogram():
  print(progressive_tryout([32], [MAGE_DECK, HUNTER_DECK], 0, 0, 0, False, False, False))

def experiment_timing_alpha():

  print(progressive_tryout([1, 1, 1], [MAGE_DECK, DRUID_DECK], 0, 0, 0, False, False, False))

def experiment_timing_beta():

  print(progressive_tryout([3], [MAGE_DECK, DRUID_DECK], 0, 0, 0, False, False, False))

def experiment_simple_game():

  WARRIOR_DECK_LITERAL = '''### WARRIOR_DECK_LITERAL
  # Class: RED
  # Format: Standard
  #
  # 2x (1) Charge
  # 2x (1) Murloc Raider
  # 2x (2) Execute
  # 2x (2) Frostwolf Grunt
  # 2x (2) Heroic Strike
  # 2x (2) Murloc Tidehunter
  # 2x (3) Fiery War Axe
  # 2x (3) Razorfen Hunter
  # 2x (3) Warsong Commander
  # 2x (3) Wolfrider
  # 2x (4) Dragonling Mechanic
  # 2x (4) Sen'jin Shieldmasta
  # 2x (5) Gurubashi Berserker
  # 2x (6) Boulderfist Ogre
  # 2x (6) Lord of the Arena
  #'''

  MAGE_DECK_LITERAL = '''### MAGE_DECK_LITERAL
  # Class: BLUE
  # Format: Standard
  #
  # 2x (1) Arcane Missiles
  # 2x (1) Murloc Raider
  # 2x (2) Arcane Explosion
  # 2x (2) Bloodfen Raptor
  # 2x (2) Novice Engineer
  # 2x (2) River Crocolisk
  # 2x (3) Arcane Intellect
  # 2x (3) Raid Leader
  # 2x (3) Wolfrider
  # 2x (4) Fireball
  # 2x (4) Oasis Snapjaw
  # 2x (4) Polymorph
  # 2x (4) Sen'jin Shieldmasta
  # 2x (5) Nightblade
  # 2x (6) Boulderfist Ogre
  #'''

  custom_card = generate_custom_card(9, 9, 0, False, False, False)
  stats = progressive_tryout([3], [WARRIOR_DECK_LITERAL, MAGE_DECK_LITERAL], [custom_card])

  return stats

def experiment_custom_card():
  with open('experiment_cards/genetic_card.json', 'r') as c:
    custom_card = json.dumps(json.load(c))
    stats = progressive_tryout([3], [HUNTER_DECK_6_CUSTOM, HUNTER_DECK_MIRROR], [custom_card])

    return stats


def experiement_validate_card():
  card = {
    "baseManaCost": 5,
    "baseHp": 5,
    "baseAttack": 5,
    "attributes": {
        "TAUNT": False,
        "LIFESTEAL": 17
    },
    "name": "Great Card",
    "type": "MINION",
    "rarity": "COMMON",
    "description": "Custom card",
    "collectible": True,
    "set": "CUSTOM",
    "fileFormatVersion": 1
  }
  
  with Context() as context:
    as_string = json.dumps(card)
    card_name = context.CardCatalogue.addOrReplaceCard(as_string)
    print(f"Successfully added {card_name}")


def experiment_reference():

  matchups = [(HUNTER_DECK, HUNTER_DECK_MIRROR),
              (WARRIOR_DECK,WARRIOR_DECK_MIRROR),
              (MAGE_DECK, MAGE_DECK_MIRROR),
              (MAGE_DECK, HUNTER_DECK),
              (HUNTER_DECK, MAGE_DECK),
              (WARRIOR_DECK, MAGE_DECK),
              (MAGE_DECK, WARRIOR_DECK),
              (HUNTER_DECK, WARRIOR_DECK),
              (WARRIOR_DECK, HUNTER_DECK)]
  for (player_deck, enemy_deck) in matchups:
    player_deck_name = player_deck.split('### ')[1].split('\n')[0]
    enemy_deck_name = enemy_deck.split('### ')[1].split('\n')[0]

    stats = progressive_tryout([1000], [player_deck, enemy_deck])
    
    send_to_database("baseline", "x", 1000, player_deck_name, enemy_deck_name, stats)

def experiment_custom_card_gauntlet():
  pp = pprint.PrettyPrinter(indent=1, compact=False)
  username = "liam"
  card_id = "01"
  test_class = "HUNTER" #HUNTER, MAGE, WARRIOR, NEUTRAL
  card_swaps = 2
  games_to_play = 1000
  
  with open(f'experiment_cards/{username}{card_id}.json', 'r') as c:
    custom_card = json.dumps(json.load(c))

    if test_class == "NEUTRAL":
      options = ["HUNTER", "WARRIOR", "MAGE"]
    else:
      options = [test_class]

    for test_deck_class in options:

      PLAYER_DECK = globals()[f"{test_deck_class}_DECK_{card_swaps}_CUSTOM"]

      for ENEMY_DECK in [MAGE_DECK, WARRIOR_DECK, HUNTER_DECK]:
        stats = progressive_tryout([games_to_play], [PLAYER_DECK, ENEMY_DECK], [custom_card])
        player_deck_name = PLAYER_DECK.split("\n")[0].split(" ")[1]
        enemy_deck_name =  ENEMY_DECK.split("\n")[0].split(" ")[1]
        
        send_to_database(username, card_id, games_to_play, player_deck_name, enemy_deck_name, stats)

        pp.pprint(f"{username}_{card_id}")
        pp.pprint(f"{player_deck_name} vs {enemy_deck_name}")
        pp.pprint(f"Card swaps: {card_swaps}")
        pp.pprint(f"Games played: {games_to_play}")
        pp.pprint(stats)


def initalise_system():

  ascii_banner = pyfiglet.figlet_format("HS MICI SIM")
  print(ascii_banner)
  print("System startup")
  print(f"MP cpu count: {mp.cpu_count()}")
  print(f"OS cpu count: {os.cpu_count()}\n\n")

  global cpus_to_use
  cpus_to_use = os.cpu_count()


def run_cards(cards, num_games):
  stats = []
  decks = [HUNTER_DECK_6_CUSTOM, MAGE_DECK]
  with Context() as context:
    for c in cards:
      asString = json.dumps(c)
      context.CardCatalogue.addOrReplaceCard(asString)
      sim_results = list(simulate(context=context, decks=decks, number=int(num_games), behaviours=['GameStateValueBehaviour', 'GameStateValueBehaviour'], reduce=False))
      stats.append(get_stats(sim_results, decks[0]))
  return stats

def run_experiments(experiments): 
  pp = pprint.PrettyPrinter(indent=1, compact=False)
  # pdf = FPDF()
  # pdf.add_page()
  # pdf.set_font("Arial", size = 12)

  print("Experiment startup...")
  start_time = time.time()
  last_exp_time = start_time
  
  experiments_to_run = [expfunc for (expfunc, should_run) in experiments if should_run]

  for expfunc in experiments_to_run:
    print(f"Running {expfunc.__name__}\n")
    official_result = expfunc()
    print(f"Official result:\n")
    pp.pprint(official_result)
    # pdf.write(10, pp.pformat(official_result))
    # pdf.output("report.pdf")   

    print(f"\nExperiment took {time.time() - last_exp_time} \n")
    
    last_exp_time = time.time()

    
  print(f"Total experiments time: {time.time() - start_time}")

if __name__ == '__main__':
 
  experimenting = True

  if experimenting:
    experiments = [(experiment_simple_game, False),\
                  (experiement_validate_card, False),\
                  (experiment_timing_alpha, False),\
                  (experiment_timing_beta, False),\
                  (experiment_impact, False),\
                  (experiment_baselines, False),\
                  (experiment_histogram, False),\
                  (experiment_minimeta, False),\
                  (experiment_custom_card, False),\
                  (experiment_custom_card_gauntlet, True),\
                  (experiment_reference, False)]

    initalise_system()
    run_experiments(experiments)
  else:
    with open('generation.json', 'r') as data_in:
      data = json.load(data_in)
      game_results = run_cards(data, sys.argv[1])
      print([stats[0][1] for stats in game_results])


