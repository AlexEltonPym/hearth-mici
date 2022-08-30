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
  argent_squire = Card(name='Argent squire', card_type=CardTypes.MINION, mana = 1, attack=1, health=1,\
                       attributes=[Attributes.DIVINE_SHIELD])
  leper_gnome = Card(name='Leper gnome', card_type=CardTypes.MINION, mana=1, attack=2, health=1,\
                    effects=[DealDamage(amount=2, method=Methods.ALL, target=Targets.HEROES,\
                    owner_filter=OwnerFilters.ENEMY, trigger=Triggers.DEATHRATTLE)])
  shieldbearer = Card(name='Shieldbearer', card_type=CardTypes.MINION, mana=1, attack=0, health=4, attributes=[Attributes.TAUNT])
  classic_cards = [wisp, abusive_sergeant, argent_squire, leper_gnome, shieldbearer]
  return classic_cards

def get_test_cards():
  all_dam = Card('All dam', card_type= CardTypes.SPELL, mana=0, attack=1, health=5,\
                effects=[DealDamage(amount=3, method=Methods.ALL, target=Targets.MINIONS_OR_HEROES,\
                  owner_filter=OwnerFilters.ALL, trigger=Triggers.CAST)]
    )
  test_cards = [all_dam]
  return test_cards


def build_pool(set_names):
  pool = []
  if CardSets.CLASSIC_NEUTRAL in set_names:
    pool.extend(get_classic_cards())
  if CardSets.CLASSIC_HUNTER in set_names:
    pool.extend(get_hunter_cards())
  if CardSets.OP_CARDS in set_names:
    pool.extend(get_op_cards())
  if CardSets.TEST_CARDS in set_names:
    pool.extend(get_test_cards())
  return pool

def get_from_name(pool, name):
  for card in pool:
    if card.name == name:
      return deepcopy(card)