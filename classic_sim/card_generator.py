from utilities import get_classes, choice_with_none
from random import randint, choice

from enums import *
import effects
from card import Card

def make_random_card(id):
  _card_type = choice(list(CardTypes))
  _mana = randint(0, 10)
  _attack = randint(0, 10)
  _health = randint(1, 10)
  _attributes = choice([[choice([a for a in Attributes])], []])
  EffectType = choice([None] + get_classes(effects))
  if EffectType == effects.ReturnToHand and _mana == 0: #prevent infintite loops
    _mana=1
  if EffectType:
    if EffectType.param_type == ParamTypes.X:
      _value = randint(1, 10)
    elif EffectType.param_type == ParamTypes.XY:
      _value = (randint(1, 10), randint(1, 10))
    elif EffectType.param_type == ParamTypes.NONE:
      _value = None
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


