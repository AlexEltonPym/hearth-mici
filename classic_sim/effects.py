from enums import *
from player import Player

class GainMana():
  available_methods = [Methods.SELF, Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.X
  available_targets = [Targets.HEROES]
  available_filters = [f for f in OwnerFilters]
  available_type_filters = []
  available_durations = [Durations.TURN, Durations.PERMANENTLY]
  available_triggers = [Triggers.BATTLECRY, Triggers.DEATHRATTLE]
  def __init__(self, method, amount, duration, trigger, target=None, owner_filter=None):

    self.method = method
    self.amount = amount
    self.target = target
    self.owner_filter = owner_filter
    self.duration = duration
    self.trigger = trigger

  def resolve_action(self, game, action):
    if self.duration == Durations.TURN:
      action['target'].current_mana += self.amount
    elif self.duration == Durations.PERMANENTLY:
      action['target'].current_mana += self.amount
      action['target'].max_mana += self.amount


class DealDamage():
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.X
  available_targets = [Targets.MINIONS, Targets.HEROES, Targets.MINIONS_OR_HEROES]
  available_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = []
  available_triggers = [Triggers.BATTLECRY, Triggers.DEATHRATTLE]

  def __init__(self, method, amount, target, owner_filter, trigger, type_filter=None):
    self.method = method
    self.amount = amount
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger

  def resolve_action(self, game, action):
    game.deal_damage(action['target'], self.amount)
    

class ChangeStats():
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.XY
  available_targets = [Targets.MINIONS, Targets.HEROES, Targets.MINIONS_OR_HEROES, Targets.WEAPONS]
  available_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = [Durations.TURN, Durations.PERMANENTLY]
  available_triggers = [Triggers.BATTLECRY]
  def __init__(self, method, attack_amount, health_amount, target, owner_filter, type_filter, trigger, duration):
    self.method = method
    self.attack_amount = attack_amount
    self.health_amount = health_amount
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    if self.duration == Durations.TURN:
      action['target'].temp_attack += self.attack_amount
      action['target'].temp_health += self.health_amount
    else:
      action['target'].attack += self.attack_amount
      action['target'].health += self.health_amount

