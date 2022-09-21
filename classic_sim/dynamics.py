## Operators
from enums import *

class Constant(object):
  def __init__(self, constant):
    self.constant = constant
  def __call__(self, card):
    return self.constant

class Multiply(object):
  def __init__(self, A, B):
    self.A = A
    self.B = B
  def __call__(self, card):
    return self.A(card) * self.B(card)

class Add(object):
  def __init__(self, A, B):
    self.A = A
    self.B = B
  def __call__(self, card):
    return self.A(card) + self.B(card)

class Equals(object):
  def __init__(self, A, B):
    self.A = A
    self.B = B
  def __call__(self, card):
    return self.A(card) == self.B(card)

class LessThan(object):
  def __init__(self, A, B):
    self.A = A
    self.B = B
  def __call__(self, card):
    return self.A(card) < self.B(card)

class GreaterThan(object):
  def __init__(self, A, B):
    self.A = A
    self.B = B
  def __call__(self, card):
    return self.A(card) > self.B(card)

class If(object):
  def __init__(self, condition, result, alternative):
    self.condition = condition
    self.result = result
    self.alternative = alternative
  def __call__(self, card):
    if self.condition(card):
      return self.result(card)
    else: 
      return self.alternative(card)

## Dynamic values

class NumOtherMinions(object):
  def __init__(self, owner_filter):
    self.owner_filter = owner_filter
  def __call__(self, card):
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      count += len(card.owner.board) - 1
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      count += len(card.owner.other_player.board)
    return count

class CardsInHand(object):
  def __init__(self, owner_filter):
    self.owner_filter = owner_filter
  def __call__(self, card):
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      count += len(card.owner.hand)
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      count += len(card.owner.other_player.hand)
    return count

class DamageTaken(object):
  def __init__(self, owner_filter):
    self.owner_filter = owner_filter
  def __call__(self, card):
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      count += 30 - card.owner.get_health()
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      count += 30 - card.owner.other_player.get_health()
    return count

class FriendlyWeaponAttack(object):
  def __init__(self):
    pass
  def __call__(self, card):
    return card.owner.weapon.get_attack() if card.owner.weapon else 0

class MinionsPlayed(object):
  def __init__(self):
    pass
  def __call__(self, card):
    return card.owner.minions_played_this_turn

class NumCardsInHand(object):
  def __init__(self):
    pass
  def __call__(self, card):
    return len(card.owner.hand)

class AttackValue(object):
  def __init__(self):
    pass
  def __call__(self, card):
    return card.get_attack()

class Damaged(object):
  def __init__(self):
    pass
  def __call__(self, card):
    return card.get_health() < card.get_max_health()

class NumWithAttribute(object):
  def __init__(self, attribute, owner_filter):
    self.attribute = attribute
    self.owner_filter = owner_filter
  def __call__(self, card):
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      for minion in card.owner.board:
        if minion.has_attribute(self.attribute):
          count += 1
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      for minion in card.owner.other_player.board:
        if minion.has_attribute(self.attribute):
          count += 1
    return count

class NumWithCreatureType(object):
  def __init__(self, creature_type, owner_filter):
    self.creature_type = creature_type
    self.owner_filter = owner_filter
  def __call__(self, card):
    count = 0
    if self.owner_filter == OwnerFilters.FRIENDLY or self.owner_filter == OwnerFilters.ALL:
      for minion in card.owner.board:
        if minion.creature_type == self.creature_type:
          count += 1
    if self.owner_filter == OwnerFilters.ENEMY or self.owner_filter == OwnerFilters.ALL:
      for minion in card.owner.other_player.board:
        if minion.creature_type == self.creature_type:
          count += 1
    return count