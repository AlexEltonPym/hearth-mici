from utilities import get_classes, choice_with_none

from enums import *
import effects
from card import Card
from condition import Condition
import numpy as np
from action import Action
from dynamics_generator import create_dynamics_tree
from numpy.random import RandomState

def make_dynamic_param(param_type, random_state):
  if param_type == ParamTypes.X:
    tree = create_dynamics_tree(int, 3, 0.4, random_state)
  elif param_type == ParamTypes.XY:
    tree = (create_dynamics_tree(int, 3, 0.4, random_state), create_dynamics_tree(int, 3, 0.4, random_state))
  elif param_type == ParamTypes.NONE:
    tree = None
  elif param_type == ParamTypes.KEYWORD:
    tree = create_dynamics_tree(Attributes, 3, 0.4, random_state)
  elif param_type == ParamTypes.DYNAMICS:
    tree = create_dynamics_tree(bool, 3, 0.4, random_state)
  elif param_type == ParamTypes.X_TOKENS:
    tree = (create_dynamics_tree(int, 3, 0.4, random_state), create_dynamics_tree("CARD", 3, 0.4, random_state))
  
  return tree

def make_random_condition(random_state):
  requirement = create_dynamics_tree(bool, 3, 0.4, random_state, is_condition=True)
  minion_attributes = list(filter(lambda a: a not in [Attributes.FREE_SECRET, Attributes.ATTACK_AS_DURABILITY, Attributes.MINIONS_UNKILLABLE], [a for a in Attributes]))
  if random_state.choice([0, 1]) == 0:
    attributes = [random_state.choice(minion_attributes)]
  else:
    attributes = []
  result = {'attributes': attributes, 'temp_attack': random_state.randint(1, 10)}
  condition = random_state.choice([Condition(requirement, result), None])
  return condition
  

def make_random_effect(random_state, card_type):
  all_effects = get_classes(effects)
  special_effects = [effects.ReplaceWithToken, effects.Cantrip, effects.DualEffect, effects.DualEffectSelf, effects.DualEffectSecrets, effects.DualEffectBoard, effects.DynamicChoice, effects.MultiEffectRandom]
  secret_effects = [effects.Redirect, effects.Counterspell, effects.RedirectToToken]
  minion_effects = list(filter(lambda e: e not in special_effects+secret_effects, get_classes(effects)))
 
  if card_type == CardTypes.SECRET:
    EffectType = choice_with_none(minion_effects+secret_effects, random_state)
  else:
    EffectType = choice_with_none(minion_effects, random_state)
  method = choice_with_none(EffectType.available_methods, random_state)
  target = choice_with_none(EffectType.available_targets, random_state)
  owner_filter = choice_with_none(EffectType.available_owner_filters, random_state)
  type_filter = choice_with_none(EffectType.available_type_filters, random_state)
  duration = choice_with_none(EffectType.available_durations, random_state)
  trigger = choice_with_none(EffectType.available_triggers, random_state)
  value = make_dynamic_param(EffectType.param_type, random_state)
  effect = random_state.choice([EffectType(method=method, target=target, owner_filter=owner_filter, type_filter=type_filter, duration=duration, trigger=trigger, value=value), None])
  return effect

def make_random_minion(id, random_state):
  manacost = random_state.randint(0, 10)
  attack = random_state.randint(0, 10)
  health = random_state.randint(1, 10)
  minion_attributes = list(filter(lambda a: a not in [Attributes.FREE_SECRET, Attributes.ATTACK_AS_DURABILITY, Attributes.MINIONS_UNKILLABLE], [a for a in Attributes]))
  if random_state.choice([0, 1]) == 0:
    attributes = [random_state.choice(minion_attributes)]
  else:
    attributes = []
  effect = make_random_effect(random_state, CardTypes.MINION)
  # condition = make_random_condition(random_state)
  creature_type = choice_with_none([c for c in CreatureTypes], random_state)
  rand_minion = Card(f"Generative Minion {id}", card_type=CardTypes.MINION, manacost=manacost, attack=attack, health=health, creature_type=creature_type, attributes=attributes, effect=effect)
  return rand_minion

def make_random_card(id, random_state):
  np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning) 

  card_type = random_state.choice([CardTypes.MINION, CardTypes.SPELL, CardTypes.WEAPON, CardTypes.SECRET]) #not creating random hero powers
  card_type = CardTypes.MINION
  if card_type == CardTypes.MINION:
    rand_card = make_random_minion(id, random_state)
  # print(f"Making card {id}")
  return rand_card

def check_card_effect_valid(card):
  effect = card.effect
  assert effect.method in effect.available_methods or effect.method == None
  assert effect.target in effect.available_targets or effect.target == None
  assert effect.owner_filter in effect.available_owner_filters or effect.owner_filter == None
  assert effect.type_filter in effect.available_type_filters or effect.type_filter == None
  assert effect.trigger in effect.available_triggers or effect.trigger == None
  assert effect.duration in effect.available_durations or effect.duration == None
  if isinstance(effect, effects.Redirect) or isinstance(effect, effects.Counterspell) or isinstance(effect, effects.RedirectToToken):
    assert card.card_type == CardTypes.SECRET

def check_card_attributes_valid(card):
  if card.card_type == CardTypes.MINION:
    assert card.manacost >= 0 and card.manacost <= 20
    assert card.attack >= 0 and card.attack <= 20
    assert card.health >= 0 and card.health <= 20
    for attribute in card.attributes:
      assert attribute in Attributes
      assert attribute not in [Attributes.FREE_SECRET, Attributes.ATTACK_AS_DURABILITY, Attributes.MINIONS_UNKILLABLE]
  elif card.card_type == CardTypes.WEAPON:
    assert card.manacost >= 0 and card.manacost <= 20
    assert card.attack >= 0 and card.attack <= 20
    assert card.health >= 0 and card.health <= 20
    for attribute in card.attributes:
      assert attribute in [Attributes.IMMUNE, Attributes.WINDFURY, Attributes.ATTACK_AS_DURABILITY]
  elif card.card_type == CardTypes.SPELL:
    assert card.manacost >= 0 and card.manacost <= 20
    assert card.attack == None
    assert card.health == None
    assert len(card.attributes) == 0
  elif card.card_type == CardTypes.SECRET:
    assert card.manacost >= 0 and card.manacost <= 20
    assert card.attack == None
    assert card.health == None
    assert len(card.attributes) == 0


def check_card_valid(card):
  check_card_attributes_valid(card)
  check_card_effect_valid(card) if card.effect else True


if __name__ == "__main__":
  card = make_random_card(0, RandomState())
  print(card)
