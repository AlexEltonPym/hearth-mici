from enums import *

from typing import TypeVar

CARD = "CARD"
PLAYER = "PLAYER"
CONSTANT = TypeVar('CONSTANT', int, Attributes, CARD)
CARD_OR_HERO = TypeVar('CARD_OR_HERO', CARD, PLAYER)

## Operators

class Constant(object):
  def __init__(self, constant:CONSTANT):
    self.constant = constant
  def __call__(self, action)->CONSTANT:
    return self.constant

class Multiply(object):
  def __init__(self, A:int, B:int):
    self.A = A
    self.B = B
  def __call__(self, action) -> int:
    return self.A(action) * self.B(action)

class Add(object):
  def __init__(self, A:int, B:int):
    self.A = A
    self.B = B
  def __call__(self, action) -> int:
    return self.A(action) + self.B(action)

class Equals(object):
  def __init__(self, A: int, B: int): #in theoery we could support CONSTANT
    self.A = A
    self.B = B
  def __call__(self, action) -> bool:
    return self.A(action) == self.B(action)

class LessThan(object):
  def __init__(self, A:int, B:int):
    self.A = A
    self.B = B
  def __call__(self, action) -> bool:
    return self.A(action) < self.B(action)

class GreaterThan(object):
  def __init__(self, A:int, B:int):
    self.A = A
    self.B = B
  def __call__(self, action) -> bool:

    return self.A(action) > self.B(action)
  
class Not(object):
  def __init__(self, A:bool):
    self.A = A
  def __call__(self, action) -> bool:
    return not self.A(action)

class And(object):
  def __init__(self, A:bool, B:bool):
    self.A = A
    self.B = B
  def __call__(self, action) -> bool:
    return self.A(action) and self.B(action)

class Or(object):
  def __init__(self, A:bool, B:bool):
    self.A = A
    self.B = B
  def __call__(self, action) -> bool:
    return self.A(action) or self.B(action)

class Minimum(object):
  def __init__(self, A:int, B:int):
    self.A = A
    self.B = B
  def __call__(self, action) -> int:
    return min(self.A(action), self.B(action))

class Maximum(object):
  def __init__(self, A:int, B:int):
    self.A = A
    self.B = B
  def __call__(self, action) -> int:
    return max(self.A(action), self.B(action))

class If(object):
  def __init__(self, condition: bool, result: CONSTANT, alternative: CONSTANT):
    self.condition = condition
    self.result = result
    self.alternative = alternative
  def __call__(self, action) -> CONSTANT:
    if self.condition(action):
      return self.result(action)
    else: 
      return self.alternative(action)

class Source(object):
  def __init__(self):
    pass
  def __call__(self, action) -> CARD_OR_HERO:
    return action.source

class Target(object):
  def __init__(self):
    pass
  def __call__(self, action) -> CARD_OR_HERO:
    return action.targets[0]

## Dynamic values

class NumOtherMinions(object):
  def __init__(self, owner_filter:OwnerFilters):
    self.owner_filter = owner_filter
  def __call__(self, action) -> int:
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      count += len(action.source.owner.board) - 1
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      count += len(action.source.owner.other_player.board)
    return count

class CardsInHand(object):
  def __init__(self, owner_filter:OwnerFilters):
    self.owner_filter = owner_filter
  def __call__(self, action) -> int:
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      count += len(action.source.owner.hand)
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      count += len(action.source.owner.other_player.hand)
    return count

class DamageTaken(object):
  def __init__(self, owner_filter:OwnerFilters):
    self.owner_filter = owner_filter
  def __call__(self, action) -> int:
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      count += 30 - action.source.owner.get_health()
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      count += 30 - action.source.owner.other_player.get_health()
    return count

class PlayerArmor(object):
  def __init__(self, owner_filter:OwnerFilters):
    self.owner_filter = owner_filter
  def __call__(self, action) -> int:
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      count += action.source.owner.armor
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      count += action.source.owner.other_player.armor
    return count

class WeaponAttack(object):
  def __init__(self, owner_filter:OwnerFilters):
    self.owner_filter = owner_filter
  def __call__(self, action) -> int:
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      count += action.source.owner.weapon.get_attack() if action.source.owner.weapon else 0
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      count += action.source.owner.other_player.weapon.get_attack() if action.source.owner.other_player.weapon else 0
    return count

class HasWeapon(object):
  def __init__(self, owner_filter:OwnerFilters):
    self.owner_filter = owner_filter
  def __call__(self, action) -> bool:
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      return action.source.owner.weapon != None
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      return action.source.owner.other_player.weapon != None

class MinionsPlayed(object):
  def __init__(self, owner_filter:OwnerFilters):
    self.owner_filter = owner_filter

  def __call__(self, action) -> int:
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      count += action.source.owner.minions_played_this_turn
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      count += action.source.owner.other_player.minions_played_this_turn
    return count

class NumCardsInHand(object):
  def __init__(self, owner_filter:OwnerFilters):
    self.owner_filter=owner_filter
  def __call__(self, action) -> int:
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      count += len(action.source.owner.hand)
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      count += len(action.source.owner.other_player.hand)
    return count

class AttackValue(object):
  def __init__(self):
    pass
  def __call__(self, action) -> int:
    return action.source.get_attack()

class HealthValue(object):
  def __init__(self):
    pass
  def __call__(self, action) -> int:
    return action.source.get_health()

class Damaged(object):
  def __init__(self):
    pass
  def __call__(self, action) -> bool:
    return action.source.get_health() < action.source.get_max_health()

class NumWithAttribute(object):
  def __init__(self, attribute:Attributes, owner_filter:OwnerFilters):
    self.attribute = attribute
    self.owner_filter = owner_filter
  def __call__(self, action) -> int:
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      for minion in action.source.owner.board:
        if minion.has_attribute(self.attribute(action)):
          count += 1
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      for minion in action.source.owner.other_player.board:
        if minion.has_attribute(self.attribute(action)):
          count += 1
    return count

class NumWithCreatureType(object):
  def __init__(self, creature_type:CreatureTypes, owner_filter:OwnerFilters):
    self.creature_type = creature_type
    self.owner_filter = owner_filter
  def __call__(self, action) -> int:
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      for minion in action.source.owner.board:
        if minion.creature_type == self.creature_type:
          count += 1
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      for minion in action.source.owner.other_player.board:
        if minion.creature_type == self.creature_type:
          count += 1
    return count

class NumDamaged(object):
  def __init__(self, owner_filter:OwnerFilters):
    self.owner_filter = owner_filter
  def __call__(self, action) -> int:
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      for minion in action.source.owner.board:
        if minion.get_health() < minion.get_max_health():
          count += 1
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      for minion in action.source.owner.other_player.board:
        if minion.get_health() < minion.get_max_health():
          count += 1
    return count

class TargetFrozen(object):
  def __init__(self):
    pass
  def __call__(self, action) -> bool:
    return action.targets[0].has_attribute(Attributes.FROZEN)

class PlayerHasAttribute(object):
  def __init__(self, attribute:Attributes, owner_filter:OwnerFilters):
    self.attribute = attribute
    self.owner_filter = owner_filter
  def __call__(self, action) -> bool:
    if self.owner_filter == OwnerFilters.FRIENDLY:
      return action.source.owner.has_attribute(self.attribute(action))
    elif self.owner_filter == OwnerFilters.ENEMY:
      return action.source.owner.other_player.has_attribute(self.attribute(action))
    elif self.owner_filter == OwnerFilters.ANY:
      return action.source.owner.has_attribute(self.attribute(action)) or action.source.owner.other_player.has_attribute(self.attribute(action))

class SourceHasAttribute(object):
  def __init__(self, attribute:Attributes):
    self.attribute = attribute
  def __call__(self, action) -> bool:
    return action.source.has_attribute(self.attribute(action))


class HasSecret(object):
  def __init__(self, owner_filter:OwnerFilters):
    self.owner_filter = owner_filter
  def __call__(self, action) -> bool:
    if self.owner_filter == OwnerFilters.FRIENDLY:
      return len(action.source.owner.secrets_zone) > 0
    elif self.owner_filter == OwnerFilters.ENEMY:
      return len(action.source.owner.other_player.secrets_zone) > 0
    elif self.owner_filter == OwnerFilters.ANY:
      return (len(action.source.owner.secrets_zone) + len(action.source.owner.other_player.secrets_zone)) > 0

class TargetAlive(object):
  def __init__(self):
    pass
  def __call__(self, action) -> bool:
    return action.targets[0].get_health() > 0


__all__ = ["Constant", "Multiply", "Add", "Equals", "LessThan", "GreaterThan", "Not", "And", "Or", "Minimum", "Maximum", "If", "Source", "Target", "NumOtherMinions", "CardsInHand", "DamageTaken", "PlayerArmor", "WeaponAttack", "HasWeapon", "MinionsPlayed", "NumCardsInHand", "AttackValue", "HealthValue", "Damaged", "NumWithAttribute", "NumWithCreatureType", "NumDamaged", "TargetFrozen", "PlayerHasAttribute", "SourceHasAttribute", "HasSecret", "TargetAlive"]