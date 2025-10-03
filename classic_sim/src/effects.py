from enums import *
from copy import deepcopy
from action import Action
from dynamics import *
from player import Player
import inspect


class Effect():
  def __repr__(self):
    return f"{self.__class__.__name__}({self.method}, {self.target}, {self.owner_filter}, {self.type_filter}, {self.trigger}, value={self.value})"
  def __str__(self):
    return self.__repr__()

class GainMana(Effect):
  available_methods = [Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.X
  available_targets = [Targets.HERO]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = []
  available_durations = [Durations.TURN, Durations.PERMANENTLY]
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))
  def __init__(self, method, value, duration, owner_filter, target=Targets.HERO, random_count=1, random_replace=True, trigger=None, type_filter=None):
    self.zone_filter = Zones.BOARD
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.duration = duration
    self.type_filter = type_filter
    self.trigger = trigger

  def resolve_action(self, game, action):
    from card_sets import get_utility_card
    for target in action.targets:
      if self.duration == Durations.TURN:
        target.current_mana += self.value(action)
        target.current_mana = min(target.current_mana, 10)
      elif self.duration == Durations.PERMANENTLY:
        target.max_mana += self.value(action)
        if target.max_mana > 10:
          excess_mana = get_utility_card('Excess Mana')
          excess_mana.set_owner(target)
          excess_mana.set_parent(target.hand)
          target.max_mana = 10
        target.current_mana += self.value(action)
        target.current_mana = min(target.current_mana, 10)

class DealDamage(Effect):
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL, Methods.SELF, Methods.TRIGGERER]
  param_type = ParamTypes.X
  available_targets = [Targets.MINION, Targets.HERO, Targets.MINION_OR_HERO, Targets.WEAPON]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, method, value, target, owner_filter, random_count=1, random_replace=True, hits_adjacent=False, trigger=None, type_filter=None, duration=None):
    self.zone_filter = Zones.BOARD
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = hits_adjacent
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    damage_amount = self.value(action) + (action.source.owner.get_spell_damage() if action.source.card_type == CardTypes.SPELL else 0)

    for target in action.targets:
      # print(f"Dealing {damage_amount} damage to {target}")
      if self.hits_adjacent:
        adjacent_targets = target.parent.get_adjacent(target)
        for adjacent_target in adjacent_targets:
          game.deal_damage(adjacent_target, damage_amount)
      game.deal_damage(target, damage_amount)


class Destroy(Effect):
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL, Methods.SELF, Methods.TRIGGERER]
  param_type = ParamTypes.DYNAMICS
  available_targets = [Targets.MINION, Targets.WEAPON, Targets.SECRET]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, method, target, owner_filter, value=None, random_count=1, random_replace=True, hits_adjacent=False, trigger=None, type_filter=None, duration=None):
    self.zone_filter = Zones.BOARD
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = hits_adjacent
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if (self.value and self.value(Action(Actions.CAST_EFFECT, source=target, targets=[action.source]))) or self.value == None: #still a valid dynamic target
        if self.hits_adjacent:
          adjacent_targets = target.parent.get_adjacent(target)
          for adjacent_target in adjacent_targets:
            game.handle_death(adjacent_target)
        game.handle_death(target)
      

class ChangeStats(Effect):
  available_methods = [m for m in Methods]
  param_type = ParamTypes.XY
  available_targets = [Targets.MINION, Targets.WEAPON, Targets.HERO]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = [d for d in Durations]
  available_triggers = [t for t in Triggers]
  def __init__(self, value, method, target, owner_filter, random_count=1, random_replace=True, hits_adjacent=False, duration=None, trigger=None, type_filter=None, dynamic_filter=None):
    self.zone_filter = Zones.BOARD #this could be changeable
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = hits_adjacent
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration
    self.dynamic_filter = dynamic_filter

  def resolve_action(self, game, action):
    for target in action.targets:
      if self.hits_adjacent:
        adjacent_targets = target.parent.get_adjacent(target)
        for adjacent_target in adjacent_targets:
          if self.duration == Durations.TURN:
            adjacent_target.temp_attack += self.value[0](action)
            adjacent_target.temp_health += self.value[1](action)
          elif self.duration == Durations.PERMANENTLY:
            adjacent_target.perm_attack += self.value[0](action)
            adjacent_target.perm_health += self.value[1](action)
      if self.duration == Durations.TURN:
        target.temp_attack += self.value[0](action)
        target.temp_health += self.value[1](action)
      elif self.duration == Durations.PERMANENTLY:
        target.perm_attack += self.value[0](action)
        target.perm_health += self.value[1](action)

class SetStats(Effect):
  available_methods = [m for m in Methods]
  param_type = ParamTypes.XY
  available_targets = [t for t in Targets]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = []
  available_triggers = [t for t in Triggers]
  def __init__(self, value, method, target, owner_filter, random_count=1, random_replace=True, hits_adjacent=False, duration=None, trigger=None, type_filter=None):
    self.zone_filter = Zones.BOARD #this could be changeable
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = hits_adjacent
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if self.hits_adjacent:
        adjacent_targets = target.parent.get_adjacent(target)
        for adjacent_target in adjacent_targets:
          if self.value[0] != None:
            adjacent_target.temp_attack = 0
            adjacent_target.perm_attack = 0
            adjacent_target.attack = self.value[0](action)
          if self.value[1] != None:
            adjacent_target.temp_health = 0
            adjacent_target.perm_health = 0
            adjacent_target.health = self.value[1](action)
            adjacent_target.max_health = target.health
      if self.value[0] != None:
        target.temp_attack = 0
        target.perm_attack = 0
        target.attack = self.value[0](action)
      if self.value[1] != None:
        target.temp_health = 0
        target.perm_health = 0
        target.health = self.value[1](action)
        target.max_health = target.health


class SwapStats(Effect):
  available_methods = [m for m in Methods]
  param_type = ParamTypes.NONE
  available_targets = [Targets.MINION, Targets.WEAPON]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = [Durations.PERMANENTLY]
  available_triggers = [t for t in Triggers]
  def __init__(self, method, target, owner_filter, value=None, random_count=1, random_replace=True, hits_adjacent=False, duration=None, trigger=None, type_filter=None):
    self.zone_filter = Zones.BOARD #this could be changeable
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = hits_adjacent
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if self.hits_adjacent:
        adjacent_targets = target.parent.get_adjacent(target)
        for adjacent_target in adjacent_targets:
          temp = adjacent_target.get_attack()
          adjacent_target.attack = adjacent_target.get_health()
          adjacent_target.health = temp
          adjacent_target.max_health = temp
      temp = target.get_attack()
      target.attack = target.get_health()
      target.health = temp
      target.max_health = temp

class GainArmor(Effect):
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.X
  available_targets = [Targets.HERO]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = []
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, method, value, owner_filter, random_count=1, random_replace=True, target=Targets.HERO, trigger=None, type_filter=None, duration=None):
    self.zone_filter = Zones.BOARD #draw cards targets a player
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      target.armor += self.value(action)
      # print(f"{target} gaining {self.value(action)} armor")
      target.armor = max(target.armor, 0) #prevent negative armor

class DrawCards(Effect):
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.X
  available_targets = [t for t in Targets]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = []
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, method, value, owner_filter, random_count=1, random_replace=True, target=Targets.HERO, trigger=None, type_filter=None, duration=None):
    self.zone_filter = Zones.BOARD #draw cards targets a player, or if it targets a minion: the sources owner
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if isinstance(target, Player):
        game.draw(target, self.value(action))
      else:
        game.draw(action.source.owner, self.value(action))


class Tutor(Effect):
  available_methods = [Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.NONE
  available_targets = [Targets.MINION, Targets.SPELL, Targets.MINION_OR_SPELL, Targets.SECRET, Targets.WEAPON]
  available_owner_filters = [OwnerFilters.FRIENDLY]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, method, owner_filter, value=None, random_count=1, random_replace=True, target=Targets.HERO, trigger=None, type_filter=None, duration=None):
    self.zone_filter = Zones.DECK
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if len(action.source.owner.hand) < action.source.owner.hand.max_entries:
        target.change_parent(action.source.owner.hand)
      else:
        target.change_parent(action.source.owner.graveyard) #mill if hand is full, need to playtest this

class ReturnToHand(Effect):
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL, Methods.TRIGGERER]
  param_type = ParamTypes.NONE
  available_targets = [Targets.MINION] #could theoreticaly do weapons too
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, method, owner_filter, random_count=1, random_replace=True, hits_adjacent=False, target=Targets.MINION, value=None, trigger=None, type_filter=None, duration=None):
    self.zone_filter = Zones.BOARD #targets a card in play
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = hits_adjacent
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if not isinstance(target, Player):
        if self.hits_adjacent:
          adjacent_targets = target.parent.get_adjacent(target)
          for adjacent_target in adjacent_targets:
            adjacent_target.change_parent(adjacent_target.parent.parent.hand) #return to targets parent's player's hand (the parent of the board is the player)
            adjacent_target.return_to_hand_reset()

        target.change_parent(target.parent.parent.hand) #return to targets parent's player's hand (the parent of the board is the player)
        target.return_to_hand_reset()

class RestoreHealth(Effect):
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL, Methods.SELF]
  param_type = ParamTypes.X
  available_targets = [t for t in Targets]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))
 
  def __init__(self, method, owner_filter, target, value, random_count=1, random_replace=True, hits_adjacent=False, trigger=None, type_filter=None, duration=None):
    self.zone_filter = Zones.BOARD
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = hits_adjacent
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if self.hits_adjacent:
        adjacent_targets = target.parent.get_adjacent(target)
        for adjacent_target in adjacent_targets:
          max_healing = adjacent_target.get_max_health() - adjacent_target.get_health()
          healing = min(self.value(action), max_healing)
          adjacent_target.health += healing
          if healing > 0:
            game.trigger(adjacent_target, Triggers.ANY_HEALED)
            game.trigger(adjacent_target, Triggers.FRIENDLY_HEALED)
            game.trigger(adjacent_target, Triggers.ENEMY_HEALED)
      max_healing = target.get_max_health() - target.get_health()
      healing = min(self.value(action), max_healing)
      target.health += healing
      if healing > 0:
        game.trigger(target, Triggers.ANY_HEALED)
        game.trigger(target, Triggers.FRIENDLY_HEALED)
        game.trigger(target, Triggers.ENEMY_HEALED)

class GiveAttribute(Effect):
  available_methods = [m for m in Methods]
  param_type = ParamTypes.KEYWORD
  available_targets = [t for t in Targets]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = [d for d in Durations]
  available_triggers = [t for t in Triggers]
  def __init__(self, value, method, target, owner_filter, random_count=1, random_replace=True, hits_adjacent=False, duration=None, trigger=None, type_filter=None):
    self.zone_filter = Zones.BOARD #could be changeable
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = hits_adjacent
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if self.hits_adjacent:
        adjacent_targets = target.parent.get_adjacent(target)
        for adjacent_target in adjacent_targets:
          if self.duration == Durations.TURN and not self.value in adjacent_target.temp_attributes:
            adjacent_target.temp_attributes.append(self.value(action))
          elif self.duration == Durations.PERMANENTLY and not self.value in adjacent_target.perm_attributes:
            adjacent_target.perm_attributes.append(self.value(action))
      if self.duration == Durations.TURN and not self.value in target.temp_attributes:
        target.temp_attributes.append(self.value(action))
      elif self.duration == Durations.PERMANENTLY and not self.value in target.perm_attributes:
        target.perm_attributes.append(self.value(action))

class RemoveAttribute(Effect):
  available_methods = [m for m in Methods]
  param_type = ParamTypes.KEYWORD
  available_targets = [t for t in Targets]
  available_owner_filters = [f for f in OwnerFilters]
  available_type_filters = [c for c in CreatureTypes]
  available_durations = []
  available_triggers = [t for t in Triggers]
  def __init__(self, value, method, target, owner_filter, random_count=1, random_replace=True, hits_adjacent=False, duration=None, trigger=None, type_filter=None):
    self.zone_filter = Zones.BOARD #could be changeable
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = hits_adjacent
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if self.hits_adjacent:
        adjacent_targets = target.parent.get_adjacent(target)
        for adjacent_target in adjacent_targets:
          adjacent_target.remove_attribute(self.value(action))
      target.remove_attribute(self.value(action))
  

class SummonToken(Effect): #summon minion for target player
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL, Methods.TRIGGERER]
  param_type = ParamTypes.X_TOKENS
  available_targets = [Targets.HERO]
  available_owner_filters = [o for o in OwnerFilters]
  available_type_filters = []
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, value, method, owner_filter, target=Targets.HERO, random_count=1, random_replace=True, duration=None, trigger=None, type_filter=None):
    self.zone_filter = Zones.BOARD #could be changed to make this add tokens to hand
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    if self.value[1](action) is None:
      return
    token_count = self.value[0](action)
    summoned_card = self.value[1](action)

    new_owner = action.targets[0].owner.other_player if self.method == Methods.TRIGGERER else action.targets[0]
    for token_number in range(token_count):
      if summoned_card.card_type == CardTypes.MINION:
        if len(new_owner.board) >= new_owner.board.max_entries:
          break
        new_minion_token = deepcopy(summoned_card)
        new_minion_token.collectable = False
        new_minion_token.set_owner(new_owner)
        new_minion_token.set_parent(new_owner.board) #Doesn't trigger battlecry
      elif summoned_card.card_type == CardTypes.WEAPON: 
        # weapons override their zone so we need to destroy exising weapon
        if new_owner.weapon: game.handle_death(new_owner.weapon)
        new_weapon_token = deepcopy(summoned_card)
        new_weapon_token.collectable = False
        new_weapon_token.set_owner(new_owner)
        new_weapon_token.set_parent(new_owner) #Doesn't trigger battlecry

class ReplaceWithToken(Effect): #replace minion with summoned token
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.X_TOKENS
  available_targets = [Targets.MINION]
  available_owner_filters = [o for o in OwnerFilters]
  available_type_filters = []
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, value, method, owner_filter, target=Targets.MINION, random_count=1, random_replace=True, duration=None, trigger=None, type_filter=None):
    self.zone_filter = Zones.BOARD #could be changed to make this add tokens to hand
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    if len(action.targets) == 0 or self.value[1](action) is None:
      return
    for target in action.targets:
      target.change_parent(target.owner.graveyard)

      for token_number in range(self.value[0](action)):
        if len(target.owner.board) >= target.owner.board.max_entries:
          break
        new_token = deepcopy(self.value[1](action))

        new_token.collectable = False
        new_token.set_owner(target.owner)
        new_token.set_parent(target.owner.board) #Doesn't trigger battlecry
        new_token.attacks_this_turn = 2 #prevent infinite attacks, new summon should have SS

class RedirectToToken(Effect): #change the target of spell to summoned token 
  available_methods = [Methods.ALL]
  param_type = ParamTypes.X_TOKENS
  available_targets = [Targets.HERO]
  available_owner_filters = [OwnerFilters.FRIENDLY]
  available_type_filters = []
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))

  def __init__(self, value, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY, target=Targets.HERO, random_count=1, random_replace=True, duration=None, trigger=None, type_filter=None):
    self.zone_filter = Zones.BOARD #could be changed to make this add tokens to hand
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration
  def resolve_action(self, game, action):
    pass

class Silence(Effect):
  available_methods = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.NONE
  available_targets = [Targets.MINION, Targets.WEAPON]
  available_owner_filters = [o for o in OwnerFilters]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = list(filter(lambda t: t != Triggers.AURA, [t for t in Triggers]))
  
  def __init__(self, method, owner_filter, target, value=None, random_count=1, random_replace=True, hits_adjacent=False, duration=None, trigger=None, type_filter=None):
    self.zone_filter = Zones.BOARD
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = hits_adjacent
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      if self.hits_adjacent:
        adjacent_targets = target.parent.get_adjacent(target)
        for adjacent_target in adjacent_targets:
          adjacent_target.temp_attack = 0
          adjacent_target.temp_health = 0
          adjacent_target.temp_attributes = []
          adjacent_target.perm_attack = 0
          adjacent_target.perm_health = 0
          adjacent_target.perm_attributes = []
          adjacent_target.attributes = []
          adjacent_target.effect = None
          adjacent_target.condition = None
      target.temp_attack = 0
      target.temp_health = 0
      target.temp_attributes = []
      target.perm_attack = 0
      target.perm_health = 0
      target.perm_attributes = []
      target.attributes = []
      target.effect = None
      target.condition = None
      
class ChangeCost(Effect):
  available_methods = [Methods.SELF, Methods.ALL, Methods.TARGETED]
  param_type = ParamTypes.X
  available_targets = [Targets.MINION, Targets.WEAPON, Targets.SPELL, Targets.SECRET]
  available_owner_filters = [o for o in OwnerFilters]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = [t for t in Triggers]
  
  def __init__(self, method, owner_filter, target, value, random_count=1, random_replace=True, duration=None, trigger=None, type_filter=None):
    self.zone_filter = Zones.HAND
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration
  
  def resolve_action(self, game, action):
    for target in action.targets:
      target.manacost += self.value(action)

class SwapWithMinion(Effect):
  available_methods = [Methods.RANDOMLY, Methods.ALL]
  param_type = ParamTypes.NONE
  available_targets = [Targets.MINION]
  available_owner_filters = [o for o in OwnerFilters]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = [t for t in Triggers]
  
  def __init__(self, method, owner_filter, target, value=None, random_count=1, random_replace=True, duration=None, trigger=None, type_filter=None):
    self.zone_filter = Zones.HAND
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      target.change_parent(target.owner.board)
      action.source.change_parent(action.source.owner.hand)

class CopyMinion(Effect):
  available_methods = [Methods.RANDOMLY, Methods.TARGETED]
  param_type = ParamTypes.NONE
  available_targets = [Targets.MINION]
  available_owner_filters = [o for o in OwnerFilters]
  available_type_filters = [t for t in CreatureTypes]
  available_durations = []
  available_triggers = [t for t in Triggers]
  
  def __init__(self, method, owner_filter, target=Targets.MINION, value=None, random_count=1, random_replace=True, duration=None, trigger=None, type_filter=None):
    self.zone_filter = Zones.BOARD
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action):
    for target in action.targets:
      action.source.manacost = target.manacost
      action.source.attack = target.attack
      action.source.health = target.health
      action.source.creature_type = target.creature_type
      action.source.max_health = target.max_health
      action.source.temp_attack = target.temp_attack
      action.source.temp_health = target.temp_health
      action.source.perm_attack = target.perm_attack
      action.source.perm_health = target.perm_health
      action.source.effect = deepcopy(target.effect)
      action.source.condition = deepcopy(target.condition)
      action.source.attributes = deepcopy(target.attributes)
      action.source.temp_attributes = deepcopy(target.temp_attributes)
      action.source.perm_attributes = deepcopy(target.perm_attributes)

class Redirect(Effect):
  available_methods = [Methods.ALL]
  param_type = ParamTypes.NONE
  available_targets = [Targets.MINION]
  available_owner_filters = [OwnerFilters.ENEMY]
  available_type_filters = []
  available_durations = []
  available_triggers = [Triggers.ENEMY_MINION_ATTACKS]
  available_card_types = [CardTypes.SECRET]
  
  def __init__(self, method=Methods.ALL, owner_filter=OwnerFilters.ENEMY, target=Targets.MINION, value=None, random_count=1, random_replace=True, duration=None, trigger=Triggers.ENEMY_MINION_ATTACKS, type_filter=None):
    self.zone_filter = Zones.BOARD
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action): #handled seperatly in attack action resolver
    return

class Counterspell(Effect):
  available_methods = [Methods.ALL]
  param_type = ParamTypes.NONE
  available_targets = [Targets.SPELL]
  available_owner_filters = [OwnerFilters.ENEMY]
  available_type_filters = []
  available_durations = []
  available_triggers = [Triggers.ENEMY_SPELL_COUNTERED]
  available_card_types = [CardTypes.SECRET]
  
  def __init__(self, method=Methods.ALL, owner_filter=OwnerFilters.ENEMY, target=Targets.SPELL, value=None, random_count=1, random_replace=True, duration=None, trigger=Triggers.ENEMY_SPELL_COUNTERED, type_filter=None):
    self.zone_filter = Zones.BOARD
    self.method = method
    self.value = value
    self.random_count = random_count
    self.random_replace = random_replace
    self.hits_adjacent = False
    self.target = target
    self.owner_filter = owner_filter
    self.type_filter = type_filter
    self.trigger = trigger
    self.duration = duration

  def resolve_action(self, game, action): #handled seperatly in spell action resolver
    return

class Cantrip(Effect): #performs first effect + draw a card
  def __init__(self, first_effect):
    self.available_methods = first_effect.available_methods
    self.param_type = first_effect.param_type
    self.available_targets = first_effect.available_targets
    self.available_owner_filters = first_effect.available_owner_filters
    self.available_type_filters = first_effect.available_type_filters
    self.available_durations =first_effect.available_durations
    self.available_triggers = first_effect.available_triggers
    self.first_effect = first_effect
    self.second_effect = DrawCards(value=ConstantInt(1), method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY)
    self.method = first_effect.method
    self.random_count = first_effect.random_count
    self.random_replace = first_effect.random_replace
    self.hits_adjacent = first_effect.hits_adjacent
    self.value = first_effect.value
    self.param_type = first_effect.param_type
    self.target = first_effect.target
    self.owner_filter = first_effect.owner_filter
    self.type_filter = first_effect.type_filter
    self.duration = first_effect.duration
    self.trigger = first_effect.trigger
    self.zone_filter = first_effect.zone_filter
  
  def resolve_action(self, game, action):
    self.first_effect.resolve_action(game, action)
    self.second_effect.resolve_action(game, Action(action_type=Actions.CAST_EFFECT, source=action.source, targets=[action.source.owner]))

class DualEffect(Effect): #second effect will recieve the same action as the first effect
  def __init__(self, first_effect, second_effect):
    self.available_methods = first_effect.available_methods
    self.param_type = first_effect.param_type
    self.available_targets = first_effect.available_targets
    self.available_owner_filters = first_effect.available_owner_filters
    self.available_type_filters = first_effect.available_type_filters
    self.available_durations =first_effect.available_durations
    self.available_triggers = first_effect.available_triggers
    self.first_effect = first_effect
    self.second_effect = second_effect
    self.method = first_effect.method
    self.random_count = first_effect.random_count
    self.random_replace = first_effect.random_replace
    self.hits_adjacent = first_effect.hits_adjacent
    self.value = first_effect.value
    self.param_type = first_effect.param_type
    self.target = first_effect.target
    self.owner_filter = first_effect.owner_filter
    self.type_filter = first_effect.type_filter
    self.duration = first_effect.duration
    self.trigger = first_effect.trigger
    self.zone_filter = first_effect.zone_filter
  
  def resolve_action(self, game, action):
    self.first_effect.resolve_action(game, action)
    self.second_effect.resolve_action(game, action)

class DualEffectSelf(Effect): #second effect will target self
  def __init__(self, first_effect, second_effect, first_effect_first=True):
    self.available_methods = first_effect.available_methods
    self.param_type = first_effect.param_type
    self.available_targets = first_effect.available_targets
    self.available_owner_filters = first_effect.available_owner_filters
    self.available_type_filters = first_effect.available_type_filters
    self.available_durations =first_effect.available_durations
    self.available_triggers = first_effect.available_triggers
    self.first_effect = first_effect
    self.second_effect = second_effect
    self.first_effect_first = first_effect_first
    self.method = first_effect.method
    self.random_count = first_effect.random_count
    self.random_replace = first_effect.random_replace
    self.hits_adjacent = first_effect.hits_adjacent
    self.value = first_effect.value
    self.param_type = first_effect.param_type
    self.target = first_effect.target
    self.owner_filter = first_effect.owner_filter
    self.type_filter = first_effect.type_filter
    self.duration = first_effect.duration
    self.trigger = first_effect.trigger
    self.zone_filter = first_effect.zone_filter
  
  def resolve_action(self, game, action):
    if self.first_effect_first:
      self.first_effect.resolve_action(game, action)
      self.second_effect.resolve_action(game, Action(action_type=Actions.CAST_EFFECT, source=action.source, targets=[action.source]))
    else:
      self.second_effect.resolve_action(game, Action(action_type=Actions.CAST_EFFECT, source=action.source, targets=[action.source]))
      self.first_effect.resolve_action(game, action)

class DualEffectSecrets(Effect): #second effect will target all enemy secrets
  def __init__(self, first_effect, second_effect):
    self.available_methods = first_effect.available_methods
    self.param_type = first_effect.param_type
    self.available_targets = first_effect.available_targets
    self.available_owner_filters = first_effect.available_owner_filters
    self.available_type_filters = first_effect.available_type_filters
    self.available_durations =first_effect.available_durations
    self.available_triggers = first_effect.available_triggers
    self.first_effect = first_effect
    self.second_effect = second_effect
    self.method = first_effect.method
    self.random_count = first_effect.random_count
    self.random_replace = first_effect.random_replace
    self.hits_adjacent = first_effect.hits_adjacent
    self.value = first_effect.value
    self.param_type = first_effect.param_type
    self.target = first_effect.target
    self.owner_filter = first_effect.owner_filter
    self.type_filter = first_effect.type_filter
    self.duration = first_effect.duration
    self.trigger = first_effect.trigger
    self.zone_filter = first_effect.zone_filter
  
  def resolve_action(self, game, action):
    self.first_effect.resolve_action(game, action)
    self.second_effect.resolve_action(game, Action(action_type=Actions.CAST_EFFECT, source=action.source, targets=action.source.owner.other_player.secrets_zone.get_all()))

class DualEffectBoard(Effect): #second effect will target all minions
  def __init__(self, first_effect, second_effect):
    self.available_methods = first_effect.available_methods
    self.param_type = first_effect.param_type
    self.available_targets = first_effect.available_targets
    self.available_owner_filters = first_effect.available_owner_filters
    self.available_type_filters = first_effect.available_type_filters
    self.available_durations =first_effect.available_durations
    self.available_triggers = first_effect.available_triggers
    self.first_effect = first_effect
    self.second_effect = second_effect
    self.method = first_effect.method
    self.random_count = first_effect.random_count
    self.random_replace = first_effect.random_replace
    self.hits_adjacent = first_effect.hits_adjacent
    self.value = first_effect.value
    self.param_type = first_effect.param_type
    self.target = first_effect.target
    self.owner_filter = first_effect.owner_filter
    self.type_filter = first_effect.type_filter
    self.duration = first_effect.duration
    self.trigger = first_effect.trigger
    self.zone_filter = first_effect.zone_filter
  
  def resolve_action(self, game, action):
    self.first_effect.resolve_action(game, action)
    board = action.source.owner.board.get_all() + action.source.owner.other_player.board.get_all()
    self.second_effect.resolve_action(game, Action(action_type=Actions.CAST_EFFECT, source=action.source, targets=board))


class DynamicChoice(Effect): #second effect will target all enemy secrets
  def __init__(self, condition, first_effect, second_effect):
    self.available_methods = first_effect.available_methods
    self.param_type = first_effect.param_type
    self.available_targets = first_effect.available_targets
    self.available_owner_filters = first_effect.available_owner_filters
    self.available_type_filters = first_effect.available_type_filters
    self.available_durations =first_effect.available_durations
    self.available_triggers = first_effect.available_triggers
    self.condition = condition
    self.first_effect = first_effect
    self.second_effect = second_effect
    self.method = first_effect.method
    self.random_count = first_effect.random_count
    self.random_replace = first_effect.random_replace
    self.hits_adjacent = first_effect.hits_adjacent
    self.value = first_effect.value
    self.param_type = first_effect.param_type
    self.target = first_effect.target
    self.owner_filter = first_effect.owner_filter
    self.type_filter = first_effect.type_filter
    self.duration = first_effect.duration
    self.trigger = first_effect.trigger
    self.zone_filter = first_effect.zone_filter
  
  def resolve_action(self, game, action):
    if self.condition(action):
      self.first_effect.resolve_action(game, action)
    else:
      self.second_effect.resolve_action(game, action)


class MultiEffectRandom(Effect): #one effect from list is chosen, same target as first effect
  def __init__(self, effects):
    self.available_methods = effects[0].available_methods
    self.param_type = effects[0].param_type
    self.available_targets = effects[0].available_targets
    self.available_owner_filters = effects[0].available_owner_filters
    self.available_type_filters = effects[0].available_type_filters
    self.available_durations =effects[0].available_durations
    self.available_triggers = effects[0].available_triggers
    self.effects = effects
    self.method = effects[0].method
    self.random_count = effects[0].random_count
    self.random_replace = effects[0].random_replace
    self.hits_adjacent = effects[0].hits_adjacent
    self.value = effects[0].value
    self.param_type = effects[0].param_type
    self.target = effects[0].target
    self.owner_filter = effects[0].owner_filter
    self.type_filter = effects[0].type_filter
    self.duration = effects[0].duration
    self.trigger = effects[0].trigger
    self.zone_filter = effects[0].zone_filter
  def resolve_action(self, game, action):
    chosen_effect = game.game_manager.random_state.choice(self.effects)
    chosen_effect.resolve_action(game, action)