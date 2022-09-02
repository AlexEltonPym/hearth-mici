from card import Card
from condition import Condition
from enums import *
from effects import *
from copy import deepcopy
import random

def get_utility_card(utility_card):
  the_coin = Card(name="The Coin", collectable=False, card_type=CardTypes.SPELL, mana=0, \
                  effect=GainMana(value = 1, method = Methods.TARGETED,\
                  duration = Durations.TURN, target=Targets.HEROES, owner_filter=OwnerFilters.FRIENDLY))
  utility_cards = {"Coin": the_coin}
  return utility_cards[utility_card]

def get_hero_power(hero_class): 
  steady_shot = Card(name="Steady Shot", collectable=False, card_type=CardTypes.HERO_POWER, mana=2, \
                          effect=DealDamage(value=2, method=Methods.ALL, \
                          target=Targets.HEROES, owner_filter=OwnerFilters.ENEMY))
  hero_powers = {Classes.HUNTER: steady_shot}
  return hero_powers[hero_class]

def get_hunter_cards():
  hunter_cards = []

  return hunter_cards

def get_op_cards():
  op_cards = []
  return op_cards

def get_classic_cards():
  #One drops
  wisp = Card(name="Wisp", card_type = CardTypes.MINION, mana = 0, attack = 1, health = 1)
  abusive_sergeant = Card(name="Abusive Sergeant", card_type=CardTypes.MINION, mana=1, attack=1, health=1,\
                          effect=ChangeStats(value=(2,0), method = Methods.TARGETED,\
                          target=Targets.MINIONS, owner_filter = OwnerFilters.ALL, duration = Durations.TURN,\
                          trigger= Triggers.BATTLECRY, type_filter=CreatureTypes.ALL))
  argent_squire = Card(name="Argent Squire", card_type=CardTypes.MINION, mana = 1, attack=1, health=1,\
                       attributes=[Attributes.DIVINE_SHIELD])
  leper_gnome = Card(name="Leper Gnome", card_type=CardTypes.MINION, mana=1, attack=2, health=1,\
                    effect=DealDamage(value=2, method=Methods.ALL, target=Targets.HEROES,\
                    owner_filter=OwnerFilters.ENEMY, trigger=Triggers.DEATHRATTLE))
  shieldbearer = Card(name="Shieldbearer", card_type=CardTypes.MINION, mana=1, attack=0, health=4, attributes=[Attributes.TAUNT])
  southsea_deckhand = Card(name="Southsea Deckhand", card_type=CardTypes.MINION, mana=1, attack=2, health=1,\
                          condition=Condition(requirement=Condition.has_weapon, result={'attributes': [Attributes.CHARGE]}))
  worgen_infiltrator = Card(name="Worgen Infiltrator", card_type=CardTypes.MINION, mana=1, attack=2, health=1, attributes=[Attributes.STEALTH])
  young_dragonhawk = Card(name="Young Dragonhawk", card_type=CardTypes.MINION, mana=1, attack=1, health=1, attributes=[Attributes.WINDFURY])
  
  #Two drops
  amani_berserker = Card(name="Amani Berserker", card_type=CardTypes.MINION, mana=2, attack=2, health=3, condition=Condition(requirement=Condition.damaged, result={'temp_attack': 3}))
  bloodsail_raider = Card(name="Bloodsail Raider", card_type=CardTypes.MINION, mana=2, attack=2, health=3,\
                         effect=GainWeaponAttack(method=Methods.TARGETED, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  one_drops = [wisp, abusive_sergeant, argent_squire, leper_gnome, shieldbearer, southsea_deckhand, worgen_infiltrator, young_dragonhawk]
  two_drops = [amani_berserker, bloodsail_raider]
  return one_drops + two_drops



def get_test_cards():
  all_dam = Card("All Damage", card_type=CardTypes.SPELL, mana=0,\
                effect=DealDamage(value=3, method=Methods.ALL, target=Targets.MINIONS_OR_HEROES,\
                  owner_filter=OwnerFilters.ALL)
    )
  generic_weapon = Card("Generic Weapon", card_type=CardTypes.WEAPON, mana=1,\
                        attack=3, health=2)
  battlecry_weapon = Card("Battlecry Weapon", card_type=CardTypes.WEAPON, mana=1, attack=3, health=2,\
                          effect=DealDamage(value=1, method=Methods.ALL, target=Targets.MINIONS_OR_HEROES, owner_filter=OwnerFilters.ALL, trigger=Triggers.BATTLECRY))
  windfury_weapon = Card("Windfury Weapon", card_type=CardTypes.WEAPON, mana=0, attack=2, health=2, attributes=[Attributes.WINDFURY])
  test_cards = [all_dam, generic_weapon, battlecry_weapon, windfury_weapon]
  return test_cards

def get_random_cards():
  rand_cards = [make_random_card(i) for i in range(100)]
  return rand_cards

def make_random_card(id):
  _card_type = random.choice(list(CardTypes))
  _mana = random.randint(0, 10)
  _attack = random.randint(0, 10)
  _health = random.randint(1, 10)
  _attributes = random.choice([[random.choice([a for a in Attributes])], []])
  EffectType = random.choice([None, DealDamage, GainMana, ChangeStats])
  if EffectType:
    if EffectType.param_type == ParamTypes.X:
      _value = random.randint(1, 10)
    elif EffectType.param_type == ParamTypes.XY:
      _value = (random.randint(1, 10), random.randint(1, 10))
    _method = choice_with_none(EffectType.available_methods)
    _target = choice_with_none(EffectType.available_targets)
    _owner_filter = choice_with_none(EffectType.available_owner_filters)
    _type_filter = choice_with_none(EffectType.available_type_filters)
    _duration = choice_with_none(EffectType.available_durations)
    _trigger = choice_with_none(EffectType.available_triggers)

    rand_card = Card(f"Random Card {id}", card_type=_card_type, mana=_mana, attack=_attack, health=_health, attributes=_attributes,\
      effect=EffectType(value=_value, method=_method, target=_target, owner_filter=_owner_filter, type_filter=_type_filter, duration=_duration, trigger=_trigger)
    )
  else:
    rand_card = Card(f"Random Card {id}", card_type=CardTypes.MINION, mana=_mana, attack=_attack, health=_health, attributes=_attributes)

  return rand_card

def choice_with_none(iterable):
  if len(iterable) == 0:
    return None
  else:
    return random.choice(iterable)

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
  if CardSets.RANDOM_CARDS in set_names:
    pool.extend(get_random_cards())
  return pool

def get_from_name(pool, name):
  for card in pool:
    if card.name == name:
      return deepcopy(card)
  
  raise KeyError("Could not find card")