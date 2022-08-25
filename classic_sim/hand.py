class Hand():
  def __init__(self, parent):
    self.name = 'hand'
    self.parent = parent
    self.hand = []

    
  def remove(self, card):
    self.hand.remove(card)

  def add(self, card):
    self.hand.append(card)

  def get_all(self):
    return self.hand

  def __contains__(self, key):
    return key in self.hand

  def __str__(self):
    return str((self.name, self.parent.name, self.hand))

  def __repr__(self):
    return str((self.name, self.parent.name, self.hand))