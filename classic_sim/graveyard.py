class Graveyard():
  def __init__(self, parent):
    self.name = 'graveyard'
    self.parent = parent
    self.graveyard = []

    
  def remove(self, card):
    self.graveyard.remove(card)

  def add(self, card):
    self.graveyard.append(card)


  def get_all(self):
    return self.graveyard

  def __str__(self):
    return str((self.name, self.parent.name))