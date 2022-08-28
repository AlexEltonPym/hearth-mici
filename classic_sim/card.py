from enums import *

class Card():
  def __init__(self, name, card_type, mana, creature_type=None, attack=None, health=None, attributes=[], effects=[]):
    self.name = name
    self.card_type = card_type
    self.creature_type = creature_type
    self.attack = attack
    self.health = health
    self.mana = mana
    self.attributes = attributes
    self.effects = effects
    self.owner = None
    self.has_attacked = True
    self.parent = None
    self.temp_attack=0
    self.temp_health=0

  def get_string(self):
    if(self.card_type == CardTypes.MINION):
      return str((self.owner.name, self.parent.name, self.name, self.mana, str(self.attack+self.temp_attack)+"/"+str(self.health+self.temp_health)))
    else:
      return str((self.owner.name, self.parent.name, self.name, self.mana))

  def change_parent(self, new_parent):
    self.parent = new_parent

  def __str__(self):
    return self.get_string()

  def __repr__(self):
    return self.get_string()

  def __eq__(self, other):
    return self.name == other.name
