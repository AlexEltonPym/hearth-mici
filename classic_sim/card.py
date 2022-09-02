from enums import *

class Card():
  def __init__(self, name, card_type, mana, collectable=True, creature_type=None, attack=None, health=None, attributes=[], effect=None, condition=None):
    self.name = name
    self.card_type = card_type
    self.creature_type = creature_type
    self.original_health = health
    self.attack = attack
    self.health = health
    self.mana = mana
    self.attributes = attributes
    self.effect = effect
    self.condition = condition
    self.owner = None
    self.attacks_this_turn = -1
    self.parent = None
    self.temp_attack = 0
    self.temp_health = 0
    self.collectable = collectable
    

  def get_string(self):
    if(self.card_type == CardTypes.MINION):
      return str((id(self), self.owner.name, self.parent.name, self.name, self.mana, str(self.attack+self.temp_attack)+"/"+str(self.health+self.temp_health)))
    else:
      return str((id(self), self.owner.name, self.parent.name, self.name, self.mana))

  def set_owner(self, owner):
    self.owner = owner
  
  def set_parent(self, parent):
    self.parent = parent
    self.parent.add(self)

  def change_parent(self, new_parent):
    self.parent.remove(self)
    self.parent = new_parent
    self.parent.add(self)

  def __str__(self):
    return self.get_string()

  def __repr__(self):
    return self.get_string()