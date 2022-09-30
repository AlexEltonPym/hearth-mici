from utilities import get_classes, choice_with_none


from enums import *
import effects
from card import Card
from condition import Condition
import numpy as np

def make_random_card(id, random_state):
  np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning) 

  _card_type = random_state.choice([CardTypes.MINION, CardTypes.SPELL, CardTypes.WEAPON]) #not creating random hero powers
  _manacost = random_state.randint(0, 10)
  _attack = random_state.randint(0, 10)
  _health = random_state.randint(1, 10)
  _attributes = random_state.choice([[random_state.choice([a for a in Attributes])], []])
  EffectType = random_state.choice([None] + list(filter(lambda effect_type: effect_type != effects.DualEffect and effect_type != effects.SummonToken, get_classes(effects))))
  requirement = random_state.choice(Condition.get_available_conditions())
  result = {'attributes': [random_state.choice([a for a in Attributes])], 'temp_attack': random_state.randint(0, 10), 'temp_health': random_state.randint(0, 10)}
  _condition = random_state.choice([Condition(requirement=requirement, result=result), None])
  if EffectType == effects.ReturnToHand and _manacost == 0: #prevent infintite loops
    _manacost=1
  if EffectType == effects.GainMana: #prevent infinite loops
    _card_type = CardTypes.SPELL
  if EffectType:
    if EffectType.param_type == ParamTypes.X:
      _value = random_state.randint(1, 10)
    elif EffectType.param_type == ParamTypes.XY:
      _value = (random_state.randint(1, 10), random_state.randint(1, 10))
    elif EffectType.param_type == ParamTypes.NONE:
      _value = None
    elif EffectType.param_type == ParamTypes.KEYWORD:
      _value = random_state.choice([a for a in Attributes])
    _method = choice_with_none(EffectType.available_methods)
    _target = choice_with_none(EffectType.available_targets)
    _owner_filter = choice_with_none(EffectType.available_owner_filters)
    _type_filter = choice_with_none(EffectType.available_type_filters)
    _duration = choice_with_none(EffectType.available_durations)
    _trigger = choice_with_none(EffectType.available_triggers)

    rand_card = Card(f"Random Card {id}", card_type=_card_type, mana=_manacost, attack=_attack, health=_health, attributes=_attributes, condition=_condition,\
      effect=EffectType(value=_value, method=_method, target=_target, owner_filter=_owner_filter, type_filter=_type_filter, duration=_duration, trigger=_trigger)
    )
  else:
    rand_card = Card(f"Random Card {id}", card_type=CardTypes.MINION, mana=_manacost, attack=_attack, health=_health, condition=_condition, attributes=_attributes)

  return rand_card


