from enums import *
from player import Player

class GainMana():
  def __init__(self, method, amount, duration, trigger, target=None, owner_filter=None):
    self.available_methods = [Methods.SELF, Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
    self.param_type = ParamTypes.X
    self.available_targets = [Targets.HEROES]
    self.available_filters = [f for f in OwnerFilters]
    self.available_type_filters = []
    self.available_durations = [Durations.TURN, Durations.PERMANENTLY]
    self.available_triggers = [Triggers.BATTLECRY, Triggers.DEATHRATTLE]

    self.method = method
    self.amount = amount
    self.target = target
    self.owner_filter = owner_filter
    self.duration = duration
    self.trigger = trigger

  def resolve_action(self, action):
    if self.duration == Durations.TURN:
      action['target'].current_mana += self.amount
    elif self.duration == Durations.PERMANENTLY:
      action['target'].current_mana += self.amount
      action['target'].max_mana += self.amount


class DealDamage():
  def __init__(self, method, amount, target, owner_filter, trigger, type_filter=None):
    self.available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
    self.param_type = ParamTypes.X
    self.available_targets = [Targets.MINIONS, Targets.HEROES, Targets.MINIONS_OR_HEROES]
    self.available_filters = [f for f in OwnerFilters]
    self.available_type_filters = [c for c in CreatureTypes]
    self.available_durations = []
    self.available_triggers = [Triggers.BATTLECRY, Triggers.DEATHRATTLE]

    self.method = method
    self.amount = amount
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger

  def resolve_action(self, action):
    action['target'].health -= self.amount
    if not isinstance(action['target'], Player) and action['target'].health <= 0:
      action['target'].parent.remove(action['target'])
      action['target'].owner.graveyard.add(action['target'])
      action['target'].parent = action['target'].owner.graveyard


class ChangeStats():
  def __init__(self, method, attack_amount, health_amount, target, owner_filter, type_filter, trigger, duration):
    self.available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
    self.param_type = ParamTypes.XY
    self.available_targets = [Targets.MINIONS, Targets.HEROES, Targets.MINIONS_OR_HEROES, Targets.WEAPONS]
    self.available_filters = [f for f in OwnerFilters]
    self.available_type_filters = [c for c in CreatureTypes]
    self.available_durations = [Durations.TURN, Durations.PERMANENTLY]
    self.available_triggers = [Triggers.BATTLECRY]

    self.method = method
    self.attack_amount = attack_amount
    self.health_amount = health_amount
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, action):
    if self.duration == Durations.TURN:
      action['target'].temp_attack += self.attack_amount
      action['target'].temp_health += self.health_amount
    else:
      action['target'].attack += self.attack_amount
      action['target'].health += self.health_amount
