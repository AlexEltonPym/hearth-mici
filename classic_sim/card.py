from enums import *
from effects import *

class Card():
  def __init__(self, name, card_type, mana, collectable=True, creature_type=None, attack=None, health=None, attributes=[], effect=None, condition=None):
    self.name = name
    self.card_type = card_type
    self.creature_type = creature_type
    self.original_health = health #used for reseting games and return to hand, never changes
    self.max_health = health #used during the game as the max health for healing, enrage etc, can change
    self.health = health #used during game as current health
    self.original_attack = attack
    self.attack = attack
    self.mana = mana
    self.attributes = attributes
    self.effect = effect
    self.condition = condition
    self.owner = None
    self.attacks_this_turn = -1
    self.parent = None
    self.temp_attack = 0
    self.temp_health = 0
    self.perm_attack = 0
    self.perm_health = 0
    self.collectable = collectable

  def set_owner(self, owner):
    self.owner = owner
  
  def set_parent(self, parent):
    self.parent = parent
    self.parent.add(self)

  def change_parent(self, new_parent):
    self.parent.remove(self)
    self.parent = new_parent
    self.parent.add(self)

  def has_attribute(self, attribute):
    return attribute in self.attributes\
          or (self.condition and attribute in self.condition.result['attributes']\
          and self.condition.requirement(self.owner.game, self))\
  
  def get_attack(self):
    aura_attack = 0
    for card in filter(lambda card: card.effect and card.effect.trigger == Triggers.AURA, self.owner.board.get_all()):
      if isinstance(card.effect, ChangeStats):
        aura_attack += card.effect.attack_value

    condition_attack = self.condition.result['temp_attack'] if self.condition and self.condition.requirement(self.owner.game, self) else 0
    return self.attack+self.perm_attack+self.temp_attack+condition_attack+aura_attack
    
  def clear_buffs(self):
    self.attacks_this_turn = -1
    self.temp_attack = 0
    self.temp_health = 0
    self.perm_attack = 0
    self.perm_health = 0 
    self.health = self.original_health    


  def get_string(self):
    if(self.card_type == CardTypes.MINION):
      return str((id(self), self.owner.name if self.owner else None, self.parent.name if self.parent else None, self.name, self.mana, self.effect, str(self.attack+self.temp_attack)+"/"+str(self.health+self.temp_health)))
    else:
      return str((id(self), self.owner.name if self.owner else None, self.parent.name if self.parent else None, self.name, self.mana, self.effect))

  def __str__(self):
    return self.get_string()

  def __repr__(self):
    return self.get_string()