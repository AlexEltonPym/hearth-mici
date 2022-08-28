from card import Card
from enums import *

def get_utility_card(utility_card):
  the_coin = Card('The coin', {'card_type': CardType.SPELL, 'mana': 0, 'effects': [{'effect_type': EffectType.GAIN_MANA, 'amount': 1, 'method': Methods.NONE, 'duration': Durations.TURN, 'trigger': Triggers.BATTLECRY}]} )
  utility_cards = {'coin': the_coin}
  return utility_cards[utility_card]

def get_hero_power(hero_class): 
  hunter_hero_power = Card('Hunter hero power', {'card_type': CardType.HERO_POWER, 'mana': 2, 'effects':[{'effect_type': EffectType.DEAL_DAMAGE, 'amount': 2, 'method': Methods.ALL, 'targets': Targets.HEROES, 'filter': Filters.ENEMY}]})
  hero_powers = {Classes.HUNTER: hunter_hero_power}
  return hero_powers[hero_class]

def get_hunter_cards():
  elven_archer = Card('Elven archer', {'card_type': CardType.MINION, 'mana': 1, 'attack':1, 'health':1, 'effects':[{'effect_type': EffectType.DEAL_DAMAGE, 'amount': 1, 'method': Methods.TARGETED,'targets': Targets.MINIONS_OR_HEROES, 'filter': Filters.ALL, 'trigger': Triggers.BATTLECRY}]})
  basic_minion = Card('Basic minion', {'card_type': CardType.MINION, 'minion_type': Targets.ELEMENTALS, 'mana': 4, 'attack':5, 'health':5, 'effects':[]})
  taunt_minion = Card('Taunt minion', {'card_type': CardType.MINION, 'mana': 1, 'attack':5, 'health':5, 'effects':[], 'attributes': [Attributes.TAUNT]})

  hunter_cards = [elven_archer, basic_minion, taunt_minion]

  return hunter_cards

def get_op_cards():
  big_minion = Card('Big minion', {'card_type': CardType.MINION, 'mana': 0, 'attack': 100, 'health': 100, 'effects': [] })
  op_cards = [big_minion]
  return op_cards

def get_classic_cards():
  wisp = Card('Wisp', {'card_type': CardType.MINION, 'mana': 0, 'attack':1, 'health': 1})
  abusive_sergeant = Card('Abusive Sergeant', {'card_type': CardType.MINION, 'mana': 1, 'attack':1, 'health': 1, 'effects': []})
  classic_cards = [wisp]
  return classic_cards

def build_pool(set_names):
  pool = []
  for set_name in set_names:
    if set_name == CardSets.CLASSIC_NEUTRAL:
      pool.extend(get_classic_cards())
    elif set_name == CardSets.CLASSIC_HUNTER:
      pool.extend(get_hunter_cards())
    elif set_name == CardSets.OP_CARDS:
      pool.extend(get_op_cards())
  return pool