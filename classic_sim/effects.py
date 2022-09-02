from enums import *

class GainMana():
  available_methods = [m for m in Methods]
  param_type = ParamTypes.X
  available_targets = [Targets.HEROES]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = []
  available_durations = [Durations.TURN, Durations.PERMANENTLY]
  available_triggers = [Triggers.BATTLECRY, Triggers.DEATHRATTLE]
  def __init__(self, method, value, duration, target, owner_filter, trigger=None, type_filter=None):
    self.method = method
    self.value = value
    self.target = target
    self.owner_filter = owner_filter
    self.duration = duration
    self.type_filter = type_filter
    self.trigger = trigger

  def resolve_action(self, game, action):
    for target in action.targets:
      if self.duration == Durations.TURN:
        target.current_mana += self.value
      elif self.duration == Durations.PERMANENTLY:
        target.current_mana += self.value
        target.max_mana += self.value


class DealDamage():
  available_methods = [m for m in Methods]
  param_type = ParamTypes.X
  available_targets = [Targets.MINIONS, Targets.HEROES, Targets.MINIONS_OR_HEROES]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = []
  available_triggers = [Triggers.BATTLECRY, Triggers.DEATHRATTLE]

  def __init__(self, method, value, target, owner_filter, trigger=None, type_filter=None, duration=None):
    self.method = method
    self.value = value
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      game.deal_damage(target, self.value)

  def __str__(self):
    return str((self.method, self.value, self.target, self.owner_filter, self.type_filter, self.trigger))
    
  
  def __repr__(self):
    return str((self.method, self.value, self.target, self.owner_filter, self.type_filter, self.trigger))
    

class ChangeStats():
  available_methods = [m for m in Methods]
  param_type = ParamTypes.XY
  available_targets = [t for t in Targets]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = [d for d in Durations]
  available_triggers = [t for t in Triggers]
  def __init__(self, value, method=None, target=None, owner_filter=None, duration=None, trigger=None, type_filter=None):
    self.method = method
    self.attack_value, self.health_value = value
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if self.duration == Durations.TURN:
        target.temp_attack += self.attack_value
        target.temp_health += self.health_value
      elif self.duration == Durations.PERMANENTLY:
        target.attack += self.attack_value
        target.health += self.health_value



class GainWeaponAttack():
  available_methods = [m for m in Methods]
  param_type = ParamTypes.NONE
  available_targets = [Targets.WEAPONS]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = []
  available_durations = [Durations.TURN, Durations.PERMANENTLY]
  available_triggers = [Triggers.BATTLECRY]
  def __init__(self, method, owner_filter, duration, value=None, target=Targets.WEAPONS, trigger=Triggers.BATTLECRY, type_filter=None):
    self.method = method
    self.value = value
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    if self.duration == Durations.TURN:
      for target in action.targets:
        action.source.temp_attack += target.attack + target.temp_attack
    elif self.duration == Durations.PERMANENTLY:
      for target in action.targets:
        action.source.attack += target.attack + target.temp_attack

