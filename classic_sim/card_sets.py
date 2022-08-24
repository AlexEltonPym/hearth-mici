from card import Card
from enums import *

def get_utility_card(utility_card):
  the_coin = Card(-2, 'The coin', {'card_type': 'spell', 'mana': 0, 'effects': [{'effect_type': 'gain_mana', 'method': Methods.NONE, 'duration': Durations.TURN, 'trigger': Triggers.BATTLECRY}]} )
  utility_cards = {'coin': the_coin}
  return utility_cards[utility_card]

def get_hero_power(hero_class): 
  hunter_hero_power = Card(-1, 'Hunter hero power', {'card_type': 'hero_power', 'mana': 2, 'effects':[{'effect_type': 'deal_damage', 'amount': 2, 'method': Methods.ALL, 'targets': Targets.HEROES, 'filter': Filters.ENEMY}]})
  hero_powers = {Classes.HUNTER: hunter_hero_power}
  return hero_powers[hero_class]

def get_hunter_cards():
  elven_archer = Card(0, 'Elven archer', {'card_type': 'minion', 'mana': 1, 'attack':1, 'health':1, 'effects':[{'effect_type': 'deal_damage', 'amount': 1, 'method': Methods.TARGETED,'targets': Targets.MINIONS_OR_HEROES, 'filter': Filters.ALL, 'trigger': Triggers.BATTLECRY}]})
  basic_minion = Card(1, 'Basic minion', {'card_type': 'minion', 'minion_type': Targets.ELEMENTALS, 'mana': 4, 'attack':5, 'health':5, 'effects':[]})
  taunt_minion = Card(2, 'Taunt minion', {'card_type': 'minion', 'mana': 1, 'attack':5, 'health':5, 'effects':[], 'attributes': [Attributes.TAUNT]})

  hunter_cards = [elven_archer, basic_minion, taunt_minion]

  return hunter_cards

def get_classic_cards():
  classic_cards = []
  return classic_cards

def build_pool(set_name):
  pool = []
  if set_name == CardSets.CLASSIC_HUNTER:
    pool = get_classic_cards() + get_hunter_cards()
  return pool