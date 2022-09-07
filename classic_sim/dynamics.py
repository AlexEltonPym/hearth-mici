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