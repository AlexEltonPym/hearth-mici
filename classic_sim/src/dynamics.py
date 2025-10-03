from enums import *

from typing import Callable
CARD = "CARD"
## Operators

class Dynamics(object):
  def __repr__(self):
    try:
      return f"{self.__class__.__name__}({self.constant})"
    except AttributeError:
      try:
        return f"{self.__class__.__name__}({self.A}, {self.B})"
      except AttributeError:
        try:
          return f"{self.__class__.__name__}({self.condition}, {self.result}, {self.alternative})"
        except AttributeError as e:
          return f"{self.__class__.__name__}()"
class RandomInt(Dynamics):
  def __init__(self, A: Callable[..., int], B: Callable[..., int]):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., int]:
    return action.owner.game.game_manager.random_state.randint(self.A(action), self.B(action))


class ConstantInt(Dynamics):
  def __init__(self, constant:int):
    self.constant = constant
  def __call__(self, action)->Callable[..., int]:
    return self.constant

class ConstantBool(Dynamics):
  def __init__(self, constant:bool):
    self.constant = constant
  def __call__(self, action)->Callable[..., bool]:
    return self.constant

class ConstantCard(Dynamics):
  def __init__(self, constant:CARD):
    self.constant = constant
  def __call__(self, action)->Callable[..., CARD]:
    return self.constant
  

class ConstantAttribute(Dynamics):
  def __init__(self, constant:Attributes):
    self.constant = constant
  def __call__(self, action)->Callable[..., Attributes]:
    return self.constant
  # def __repr__(self):
  #   return f"{self.__class__.__name__}ConstantAttribute({self.constant})"


class ConstantCreatureTypes(Dynamics):
  def __init__(self, constant:CreatureTypes):
    self.constant = constant
  def __call__(self, action)->Callable[..., CreatureTypes]:
    return self.constant

class Multiply(Dynamics):
  def __init__(self, A: Callable[..., int], B: Callable[..., int]):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., int]:
    return self.A(action) * self.B(action)

class Add(Dynamics):
  def __init__(self, A: Callable[..., int], B: Callable[..., int]):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., int]:
    return self.A(action) + self.B(action)

class Minimum(Dynamics):
  def __init__(self, A: Callable[..., int], B: Callable[..., int]):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., int]:
    return min(self.A(action), self.B(action))

class Maximum(Dynamics):
  def __init__(self, A: Callable[..., int], B: Callable[..., int]):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., int]:
    return max(self.A(action), self.B(action))


class Equals(Dynamics):
  def __init__(self, A: Callable[..., int], B: Callable[..., int]): #in theoery we could support CONSTANT
    self.A = A
    self.B = B
  def __call__(self, action) ->  Callable[..., bool]:
    return self.A(action) == self.B(action)

class LessThan(Dynamics):
  def __init__(self, A: Callable[..., int], B: Callable[..., int]):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., bool]:
    return self.A(action) < self.B(action)

class GreaterThan(Dynamics):
  def __init__(self, A: Callable[..., int], B: Callable[..., int]):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., bool]:

    return self.A(action) > self.B(action)
  
class Not(Dynamics):
  def __init__(self, A: Callable[..., bool]):
    self.A = A
  def __call__(self, action) -> Callable[..., bool]:
    return not self.A(action)

class And(Dynamics):
  def __init__(self, A: Callable[..., bool], B: Callable[..., bool]):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., bool]:
    return self.A(action) and self.B(action)

class Or(Dynamics):
  def __init__(self, A: Callable[..., bool], B: Callable[..., bool]):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., bool]:
    return self.A(action) or self.B(action)


class IfInt(Dynamics):
  def __init__(self, condition: Callable[..., bool], result: Callable[..., int], alternative: Callable[..., int]):
    self.condition = condition
    self.result = result
    self.alternative = alternative
  def __call__(self, action) -> Callable[..., int]:
    if self.condition(action):
      return self.result(action)
    else: 
      return self.alternative(action)

class IfCard(Dynamics):
  def __init__(self, condition: Callable[..., bool], result: Callable[..., CARD], alternative: Callable[..., CARD]):
    self.condition = condition
    self.result = result
    self.alternative = alternative
  def __call__(self, action) -> Callable[..., CARD]:
    if self.condition(action):
      return self.result(action)
    else: 
      return self.alternative(action)

class IfAttribute(Dynamics):
  def __init__(self, condition: Callable[..., bool], result: Callable[..., Attributes], alternative: Callable[..., Attributes]):
    self.condition = condition
    self.result = result
    self.alternative = alternative
  def __call__(self, action) -> Callable[..., Attributes]:
    if self.condition(action):
      return self.result(action)
    else: 
      return self.alternative(action)

class IfCreatureType(Dynamics):
  def __init__(self, condition: Callable[..., bool], result: Callable[..., CreatureTypes], alternative: Callable[..., CreatureTypes]):
    self.condition = condition
    self.result = result
    self.alternative = alternative
  def __call__(self, action) -> Callable[..., CreatureTypes]:
    if self.condition(action):
      return self.result(action)
    else: 
      return self.alternative(action)
    
class Source(Dynamics):
  def __init__(self):
    pass
  def __call__(self, action) -> Callable[..., CARD]:
    try:
      if action.source.card_type == CardTypes.MINION or action.source.card_type == CardTypes.WEAPON:
        return action.source
      else:
        return None
    except AttributeError:
      return None
    

class Target(Dynamics):
  def __init__(self):
    pass
  def __call__(self, action) -> Callable[..., CARD]:
    try:
      if action.targets[0].card_type == CardTypes.MINION or action.targets[0].card_type == CardTypes.WEAPON:
        return action.targets[0]
      else:
        return None
    except AttributeError:
      return None
    
## Dynamic values

class NumOtherMinions(Dynamics):
  def __init__(self, constant:OwnerFilters):
    self.constant = constant
  def __call__(self, action) -> Callable[..., int]:
    count = 0
    if self.constant == OwnerFilters.FRIENDLY or self.constant == OwnerFilters.ALL:
      count += len(action.source.owner.board) - 1
    if self.constant == OwnerFilters.ENEMY or self.constant == OwnerFilters.ALL:
      count += len(action.source.owner.other_player.board)
    return count

class CardsInHand(Dynamics):
  def __init__(self, constant:OwnerFilters):
    self.constant = constant
  def __call__(self, action) -> Callable[..., int]:
    count = 0
    if self.constant == OwnerFilters.FRIENDLY or self.constant == OwnerFilters.ALL:
      count += len(action.source.owner.hand)
    if self.constant == OwnerFilters.ENEMY or self.constant == OwnerFilters.ALL:
      count += len(action.source.owner.other_player.hand)
    return count

class DamageTaken(Dynamics):
  def __init__(self, constant:OwnerFilters):
    self.constant = constant
  def __call__(self, action) -> Callable[..., int]:
    count = 0
    if self.constant == OwnerFilters.FRIENDLY or self.constant == OwnerFilters.ALL:
      count += 30 - action.source.owner.get_health()
    if self.constant == OwnerFilters.ENEMY or self.constant == OwnerFilters.ALL:
      count += 30 - action.source.owner.other_player.get_health()
    return count

class PlayerArmor(Dynamics):
  def __init__(self, constant:OwnerFilters):
    self.constant = constant
  def __call__(self, action) -> Callable[..., int]:
    count = 0
    if self.constant == OwnerFilters.FRIENDLY or self.constant == OwnerFilters.ALL:
      count += action.source.owner.armor
    if self.constant == OwnerFilters.ENEMY or self.constant == OwnerFilters.ALL:
      count += action.source.owner.other_player.armor
    return count

class WeaponAttack(Dynamics):
  def __init__(self, constant:OwnerFilters):
    self.constant = constant
  def __call__(self, action) -> Callable[..., int]:
    count = 0
    if self.constant == OwnerFilters.FRIENDLY or self.constant == OwnerFilters.ALL:
      count += action.source.owner.weapon.get_attack() if action.source.owner.weapon else 0
    if self.constant == OwnerFilters.ENEMY or self.constant == OwnerFilters.ALL:
      count += action.source.owner.other_player.weapon.get_attack() if action.source.owner.other_player.weapon else 0
    return count

class HasWeapon(Dynamics):
  def __init__(self, constant:OwnerFilters):
    self.constant = constant
  def __call__(self, action) -> Callable[..., bool]:
    if self.constant == OwnerFilters.FRIENDLY or self.constant == OwnerFilters.ALL:
      return action.source.owner.weapon != None
    if self.constant == OwnerFilters.ENEMY or self.constant == OwnerFilters.ALL:
      return action.source.owner.other_player.weapon != None

class MinionsPlayed(Dynamics):
  def __init__(self, constant:OwnerFilters):
    self.constant = constant

  def __call__(self, action) -> Callable[..., int]:
    count = 0
    if self.constant == OwnerFilters.FRIENDLY or self.constant == OwnerFilters.ALL:
      count += action.source.owner.minions_played_this_turn
    if self.constant == OwnerFilters.ENEMY or self.constant == OwnerFilters.ALL:
      count += action.source.owner.other_player.minions_played_this_turn
    return count

class NumCardsInHand(Dynamics):
  def __init__(self, constant:OwnerFilters):
    self.constant=constant
  def __call__(self, action) -> Callable[..., int]:
    count = 0
    if self.constant == OwnerFilters.FRIENDLY or self.constant == OwnerFilters.ALL:
      count += len(action.source.owner.hand)
    if self.constant == OwnerFilters.ENEMY or self.constant == OwnerFilters.ALL:
      count += len(action.source.owner.other_player.hand)
    return count

class AttackValue(Dynamics):
  def __init__(self):
    pass
  def __call__(self, action) -> Callable[..., int]:
    return action.source.get_attack()



class HealthValue(Dynamics):
  def __init__(self):
    pass
  def __call__(self, action) -> Callable[..., int]:
    return action.source.get_health()

class Damaged(Dynamics):
  def __init__(self):
    pass
  def __call__(self, action) -> Callable[..., bool]:
    return action.source.get_health() < action.source.get_max_health()

class NumWithAttribute(Dynamics):
  def __init__(self, A: Callable[..., Attributes], B:OwnerFilters):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., int]:
    count = 0
    if self.B == OwnerFilters.FRIENDLY or self.B == OwnerFilters.ALL:
      for minion in action.source.owner.board:
        if minion.has_attribute(self.A(action)):
          count += 1
    if self.B == OwnerFilters.ENEMY or self.B == OwnerFilters.ALL:
      for minion in action.source.owner.other_player.board:
        if minion.has_attribute(self.A(action)):
          count += 1
    return count

class NumWithCreatureType(Dynamics):
  def __init__(self, A:CreatureTypes, B:OwnerFilters):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., int]:
    count = 0
    if self.B == OwnerFilters.FRIENDLY or self.B == OwnerFilters.ALL:
      for minion in action.source.owner.board:
        if minion.creature_type == self.A:
          count += 1
    if self.B == OwnerFilters.ENEMY or self.B == OwnerFilters.ALL:
      for minion in action.source.owner.other_player.board:
        if minion.creature_type == self.A:
          count += 1
    return count

class NumDamaged(Dynamics):
  def __init__(self, constant:OwnerFilters):
    self.constant = constant
  def __call__(self, action) -> Callable[..., int]:
    count = 0
    if self.constant == OwnerFilters.FRIENDLY or self.constant == OwnerFilters.ALL:
      for minion in action.source.owner.board:
        if minion.get_health() < minion.get_max_health():
          count += 1
    if self.constant == OwnerFilters.ENEMY or self.constant == OwnerFilters.ALL:
      for minion in action.source.owner.other_player.board:
        if minion.get_health() < minion.get_max_health():
          count += 1
    return count

class TargetFrozen(Dynamics):
  def __init__(self):
    pass
  def __call__(self, action) -> Callable[..., bool]:
    return len(action.targets) > 0 and action.targets[0].has_attribute(Attributes.FROZEN)

class PlayerHasAttribute(Dynamics):
  def __init__(self, A:Callable[..., Attributes], B:OwnerFilters):
    self.A = A
    self.B = B
  def __call__(self, action) -> Callable[..., bool]:
    if self.B == OwnerFilters.FRIENDLY:
      return action.source.owner.has_attribute(self.A(action))
    elif self.B == OwnerFilters.ENEMY:
      return action.source.owner.other_player.has_attribute(self.A(action))
    elif self.B == OwnerFilters.ALL:
      return action.source.owner.has_attribute(self.A(action)) or action.source.owner.other_player.has_attribute(self.A(action))

class SourceHasAttribute(Dynamics):
  def __init__(self, constant:Callable[..., Attributes]):
    self.constant = constant
  def __call__(self, action) -> Callable[..., bool]:
    return action.source.has_attribute(self.constant(action))


class HasSecret(Dynamics):
  def __init__(self, constant:OwnerFilters):
    self.constant = constant
  def __call__(self, action) -> Callable[..., bool]:
    if self.constant == OwnerFilters.FRIENDLY:
      return len(action.source.owner.secrets_zone) > 0
    elif self.constant == OwnerFilters.ENEMY:
      return len(action.source.owner.other_player.secrets_zone) > 0
    elif self.constant == OwnerFilters.ALL:
      return (len(action.source.owner.secrets_zone) + len(action.source.owner.other_player.secrets_zone)) > 0

class TargetAlive(Dynamics):
  def __init__(self):
    pass
  def __call__(self, action) -> Callable[..., bool]:
    return len(action.targets) > 0 and action.targets[0].get_health() > 0


__all__ = ["RandomInt", "ConstantInt", "ConstantBool", "ConstantCard", "ConstantAttribute", "ConstantCreatureTypes", "Multiply", "Add", "Equals", "LessThan", "GreaterThan", "Not", "And", "Or", "Minimum", "Maximum", "IfInt", "IfCard", "IfAttribute", "IfCreatureType", "Source", "Target", "NumOtherMinions", "CardsInHand", "DamageTaken", "PlayerArmor", "WeaponAttack", "HasWeapon", "MinionsPlayed", "NumCardsInHand", "AttackValue", "HealthValue", "Damaged", "NumWithAttribute", "NumWithCreatureType", "NumDamaged", "TargetFrozen", "PlayerHasAttribute", "SourceHasAttribute", "HasSecret", "TargetAlive"]