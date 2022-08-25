class Board():
  def __init__(self, parent):
    self.name = 'board'
    self.parent = parent
    self.board = []

    
  def remove(self, card):
    self.board.remove(card)

  def add(self, card):
    self.board.append(card)

  def get_all(self):
    return self.board

  def __contains__(self, key):
    return key in self.board

  def __str__(self):
    return str((self.name, self.parent.name))

  def __repr__(self):
    return str((self.name, self.parent.name))