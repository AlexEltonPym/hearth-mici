

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

class Equals(object):
  def __init__(self, A, B):
    self.A = A
    self.B = B
  def __call__(self, card):
    return self.A(card) == self.B(card)

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