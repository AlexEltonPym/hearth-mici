import os

from spellsource.context import Context
from tqdm import tqdm
import json
import random
import statistics


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

def convert_deck_to_spellsource(deck, hero_class):
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
    CONSTRUCTED_DECK += f"\n# {num_in_deck}x{card['name']}"
  return CONSTRUCTED_DECK

def get_mana_curve(deck):
  mana_costs = []
  for card in deck:
    mana_costs.append(card['baseManaCost'])
  return (statistics.mean(mana_costs), statistics.variance(mana_costs))

def convert_deck_to_bag_of_cards(deck, hero_class):
  bag = [0] * 306 #230 base cards + 70 new cards + 3 classes + 3 popularities
  for card in deck:
    bag[card['id']] += 1

  if(hero_class == 'hunter'):
    bag[-6] = 1
  elif(hero_class == 'mage'):
    bag[-5] = 1
  else:
    bag[-4] = 1
  
  bag[-3] = hunter_populatrity
  bag[-2] = mage_popularity
  bag[-1] = warrior_popularity
  return bag

def fitness_evaluation(ctx, deck, num_games):
  winrate_vs_hunter, health_delta_vs_hunter = playtest(ctx, deck, HUNTER_DECK, num_games)
  winrate_vs_mage, health_delta_vs_mage = playtest(ctx, deck, MAGE_DECK, num_games)
  winrate_vs_warrior, health_delta_vs_warrior = playtest(ctx, deck, WARRIOR_DECK, num_games)

  weighted_win_rate = winrate_vs_hunter * hunter_populatrity + winrate_vs_mage * mage_popularity + winrate_vs_warrior * warrior_popularity
  weighted_health_delta = health_delta_vs_hunter * hunter_populatrity + health_delta_vs_mage * mage_popularity + health_delta_vs_warrior * warrior_popularity
  return weighted_win_rate, weighted_health_delta

def playtest(ctx, player_deck, enemy_deck, num_games):

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

  for i in tqdm(range(num_games)):
    game_context = ctx.GameContext.fromDeckLists([player_deck, enemy_deck])
    game_context.setBehaviour(ctx.GameContext.PLAYER_1, player1_ai)
    game_context.setBehaviour(ctx.GameContext.PLAYER_2, player2_ai)

    game_context.play()

    stats = str(game_context.getPlayer(ctx.GameContext.PLAYER_1).getStatistics())
    for stat in stats.split("\n")[1:-1]:
      stat_name, stat_value = tuple(stat.split(": "))
      if(stat_name in player_stats):
        player_stats[stat_name] += float(stat_value)/num_games

    player1health = int(str(game_context.getPlayer(ctx.GameContext.PLAYER_1).getHero()).split(",")[3].split("/")[1])
    player2health = int(str(game_context.getPlayer(ctx.GameContext.PLAYER_2).getHero()).split(",")[3].split("/")[1])
    player_stats['HEALTH_DELTA'] += (player1health-player2health)/num_games

  # [print(f"{stat}: {player_stats[stat]}") for stat in player_stats]
  return player_stats['WIN_RATE'], player_stats['HEALTH_DELTA']


if __name__ == "__main__":
  with Context() as ctx:
    player1_ai = ctx.behaviour.GameStateValueBehaviour()
    player2_ai = ctx.behaviour.GameStateValueBehaviour()

    hunter_populatrity = 0.33
    mage_popularity = 0.33
    warrior_popularity = 0.33

    hunter_cards, mage_cards, warrior_card, all_cards = load_cards()
    hunter_sample = random_deck(hunter_cards)
    mana_mean, mana_variance = get_mana_curve(hunter_sample)
    as_spellsource = convert_deck_to_spellsource(hunter_sample, 'hunter')
    as_bag_of_cards = convert_deck_to_bag_of_cards(hunter_sample, 'hunter')

    wwr, whd = fitness_evaluation(ctx, as_spellsource, 100)


    print(wwr, whd, mana_mean, mana_variance)