class WeaponAttack(object):
  def __init__(self):
    pass
  def __call__(self, card):
    if card.owner.weapon:
      return card.owner.weapon.get_attack()
    else:
      return 0

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

class Tuplify(object):
  def __init__(self, fn):
    self.fn = fn
  def __call__(self, card):
    res = self.fn(card)
    return (res, res)