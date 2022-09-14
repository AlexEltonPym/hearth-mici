from enums import *
from copy import deepcopy
from action import Action

class GainMana():
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.X
  available_targets = [Targets.HERO]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = []
  available_durations = [Durations.TURN, Durations.PERMANENTLY]
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))
  def __init__(self, method, value, duration, target, owner_filter, random_count=1, trigger=None, type_filter=None):
    self.targets_hand = False
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.duration = duration
    self.type_filter = type_filter
    self.trigger = trigger

  def resolve_action(self, game, action):
    for target in action.targets:
      if self.duration == Durations.TURN:
        target.current_mana += self.value(action.source)
      elif self.duration == Durations.PERMANENTLY:
        target.current_mana += self.value(action.source)
        target.max_mana += self.value(action.source)

class DealDamage():
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL, Methods.SELF]
  param_type = ParamTypes.X
  available_targets = [Targets.MINION, Targets.HERO, Targets.MINION_OR_HERO]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, method, value, target, owner_filter, random_count=1, trigger=None, type_filter=None, duration=None):
    self.targets_hand = False
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    damage_amount = self.value(action.source) + (action.source.owner.get_spell_damage() if action.source.card_type == CardTypes.SPELL else 0)
    for target in action.targets:
      game.deal_damage(target, damage_amount)

class Destroy():
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL, Methods.SELF]
  param_type = ParamTypes.NONE
  available_targets = [Targets.MINION, Targets.HERO, Targets.MINION_OR_HERO]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, method, target, owner_filter, value=None, random_count=1, trigger=None, type_filter=None, duration=None):
    self.targets_hand = False
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      game.handle_death(target)

class ChangeStats():
  available_methods = [m for m in Methods]
  param_type = ParamTypes.XY
  available_targets = [t for t in Targets]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = [d for d in Durations]
  available_triggers = [t for t in Triggers]
  def __init__(self, value, method, target, owner_filter, random_count=1, duration=None, trigger=None, type_filter=None):
    self.targets_hand = False #this could be changeable
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if self.duration == Durations.TURN:
        target.temp_attack += self.value[0](action.source)
        target.temp_health += self.value[1](action.source)
      elif self.duration == Durations.PERMANENTLY:
        target.perm_attack += self.value[0](action.source)
        target.perm_health += self.value[1](action.source)

class SwapStats():
  available_methods = [m for m in Methods]
  param_type = ParamTypes.NONE
  available_targets = [t for t in Targets]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = [Durations.PERMANENTLY]
  available_triggers = [t for t in Triggers]
  def __init__(self, method, target, owner_filter, value=None, random_count=1, duration=None, trigger=None, type_filter=None):
    self.targets_hand = False #this could be changeable
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      temp = target.get_attack()
      target.attack = target.get_health()
      target.health = temp
      target.max_health = temp

class DrawCards():
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.X
  available_targets = [Targets.HERO]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = []
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, method, value, owner_filter, random_count=1, target=Targets.HERO, trigger=None, type_filter=None, duration=None):
    self.targets_hand = False #draw cards targets a player
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      game.draw(target, self.value(action.source))

class ReturnToHand():
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.NONE
  available_targets = [Targets.MINION] #could theoreticaly do weapons too
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, method, owner_filter, random_count=1, target=Targets.MINION, value=None, trigger=None, type_filter=None, duration=None):
    self.targets_hand = False #targets a card in play
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      target.change_parent(target.parent.parent.hand) #return to targets parent's player's hand (the parent of the board is the player)
      target.reset()

class RestoreHealth():
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL, Methods.SELF]
  param_type = ParamTypes.X
  available_targets = [t for t in Targets]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))
 
  def __init__(self, method, owner_filter, target, value, random_count=1, trigger=None, type_filter=None, duration=None):
    self.targets_hand = False
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      max_healing = target.get_max_health() - target.get_health()
      healing = min(self.value(action.source), max_healing)
      target.health += healing
      if healing > 0:
        game.trigger(target, Triggers.ANY_HEALED)
        game.trigger(target, Triggers.FRIENDLY_HEALED)
        game.trigger(target, Triggers.ENEMY_HEALED)

class GiveKeyword():
  available_methods = [m for m in Methods]
  param_type = ParamTypes.KEYWORD
  available_targets = [t for t in Targets]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = [d for d in Durations]
  available_triggers = [t for t in Triggers]
  def __init__(self, value, method, target, owner_filter, random_count=1, duration=None, trigger=None, type_filter=None):
    self.targets_hand = False #could be changeable
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      print(f"{target=}")
      if self.duration == Durations.TURN:
        target.temp_attributes.append(self.value)
      elif self.duration == Durations.PERMANENTLY:
        target.perm_attributes.append(self.value)

class SummonToken(): #summon minion for target player
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.TOKEN
  available_targets = [Targets.HERO]
  available_owner_filters = []
  available_type_filters = []
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, value, method, owner_filter, target=Targets.HERO, random_count=1, duration=None, trigger=None, type_filter=None):
    self.targets_hand = False #could be changed to make this add tokens to hand
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      new_token = deepcopy(self.value)
      #Doesn't trigger battlecry
      if len(target.board) < target.board.max_entries:
        new_token.set_owner(target)
        new_token.set_parent(target.board)
      
class Silence():
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.NONE
  available_targets = [Targets.MINION, Targets.WEAPON]
  available_owner_filters = [o for o in OwnerFilters]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))
  
  def __init__(self, method, owner_filter, target, value=None, random_count=1, duration=None, trigger=None, type_filter=None):
    self.targets_hand = False
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      target.temp_attack = 0
      target.temp_health = 0
      target.temp_attributes = []
      target.perm_attack = 0
      target.perm_health = 0
      target.perm_attributes = []
      target.attributes = []
      target.effect = None
      target.condition = None
      
class ChangeCost():
  available_methods = [Methods.SELF, Methods.ALL, Methods.TARGETED]
  param_type = ParamTypes.DYNAMIC
  available_targets = [Targets.MINION, Targets.WEAPON]
  available_owner_filters = [o for o in OwnerFilters]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = [t for t in Triggers]
  
  def __init__(self, method, owner_filter, target, value, random_count=1, duration=None, trigger=None, type_filter=None):
    self.targets_hand = True
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration
  
  def resolve_action(self, game, action):
    for target in action.targets:
      target.manacost += self.value(action.source)

class SwapWithMinion():
  available_methods = [Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.NONE
  available_targets = [Targets.MINION, Targets.WEAPON, Targets.SPELL, Targets.SECRET, Targets.MINION_OR_SPELL]
  available_owner_filters = [o for o in OwnerFilters]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = [t for t in Triggers]
  
  def __init__(self, method, owner_filter, target, value=None, random_count=1, duration=None, trigger=None, type_filter=None):
    self.targets_hand = True
    self.method = method
    self.value = value
    self.random_count = random_count
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      print(target)
      target.change_parent(target.owner.board)
      action.source.change_parent(action.source.owner.hand)

class DuelAction():
  def __init__(self, first_effect, second_effect):
    self.first_effect = first_effect
    self.second_effect = second_effect
    self.method = first_effect.method
    self.value = first_effect.value
    self.param_type = first_effect.param_type
    self.target = first_effect.target
    self.owner_filter = first_effect.owner_filter
    self.type_filter = first_effect.type_filter
    self.duration = first_effect.duration
    self.trigger = first_effect.trigger
    self.targets_hand = first_effect.targets_hand
  
  def resolve_action(self, game, action):
    self.first_effect.resolve_action(game, action)
    self.second_effect.resolve_action(game, action)

class DuelActionSelf():
  def __init__(self, first_effect, second_effect):
    self.first_effect = first_effect
    self.second_effect = second_effect
    self.method = first_effect.method
    self.value = first_effect.value
    self.param_type = first_effect.param_type
    self.target = first_effect.target
    self.owner_filter = first_effect.owner_filter
    self.type_filter = first_effect.type_filter
    self.duration = first_effect.duration
    self.trigger = first_effect.trigger
    self.targets_hand = first_effect.targets_hand
  
  def resolve_action(self, game, action):
    self.first_effect.resolve_action(game, action)
    self.second_effect.resolve_action(game, Action(action_type=Actions.CAST_EFFECT, source=action.source, targets=[action.source]))

