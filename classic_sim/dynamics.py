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

class NumOtherFriendlyMinions(object):
  def __init__(self):
    pass
  def __call__(self, card):
    return len(card.owner.board) - 1

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