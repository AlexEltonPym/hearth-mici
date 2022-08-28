from card import Card
from enums import *
from effects import GainMana, DealDamage, ChangeStats
from copy import deepcopy

def get_utility_card(utility_card):
  the_coin = Card(name='The coin', card_type=CardTypes.SPELL, mana=0, \
                  effects=[GainMana(amount = 1, method = Methods.SELF,\
                  duration = Durations.TURN, trigger=Triggers.CAST)])
  utility_cards = {'coin': the_coin}
  return utility_cards[utility_card]

def get_hero_power(hero_class): 
  hunter_hero_power = Card(name='Hunter hero power', card_type=CardTypes.HERO_POWER, mana=2, \
                          effects=[DealDamage(amount=2, method=Methods.ALL, \
                          target=Targets.HEROES, owner_filter=OwnerFilters.ENEMY, trigger=Triggers.CAST)])
  hero_powers = {Classes.HUNTER: hunter_hero_power}
  return hero_powers[hero_class]

def get_hunter_cards():
  hunter_cards = []

  return hunter_cards

def get_op_cards():
  op_cards = []
  return op_cards

def get_classic_cards():
  wisp = Card(name='Wisp', card_type = CardTypes.MINION, mana = 0, attack = 1, health = 1)
  abusive_sergeant = Card(name='Abusive sergeant', card_type=CardTypes.MINION, mana=1, attack=1, health=1,\
                          effects=[ChangeStats(attack_amount=2, health_amount=0, method = Methods.TARGETED,\
                          target=Targets.MINIONS, owner_filter = OwnerFilters.ALL, duration = Durations.TURN,\
                          trigger= Triggers.BATTLECRY, type_filter=CreatureTypes.ALL)])
  classic_cards = [wisp, abusive_sergeant]
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

def get_from_name(pool, name):
  for card in pool:
    if card.name == name:
      return deepcopy(card)