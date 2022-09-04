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
    my_index = self.parent.index_of(self)
    board = self.owner.board.get_all()
    board_len = len(board)
    
    for index, card in enumerate(board):
      if card.effect and card.effect.trigger == Triggers.AURA:
        correct_target = self.card_type== (CardTypes.MINION and (card.effect.target == Targets.MINIONS or card.effect.target == Targets.MINIONS_OR_HEROES)) or (self.card_type == CardTypes.WEAPON and card.effect.target == Targets.WEAPONS)
        correct_owner = card.effect.owner_filter == OwnerFilters.FRIENDLY or card.effect.owner_filter == OwnerFilters.ALL
        correct_creature_type = card.effect.type_filter == None or card.effect.type_filter == CardTypes.ALL or card.effect.type_filter == self.creature_type
        if correct_target and correct_owner and correct_creature_type\
           and (card.method == Methods.ALL
           or (card.method == Methods.ADJACENT\
           and my_index == index-1 or my_index == index+1\
           or (my_index == 0 and index == board_len)\
           or (my_index == board_len and index == 0))):
          if isinstance(card.effect, ChangeStats):
            aura_attack += card.effect.attack_value
      
    for card in self.parent.parent.other_player.board:
      if card.effect and card.effect.trigger == Triggers.AURA:
        correct_target = self.card_type == (CardTypes.MINION and (card.effect.target == Targets.MINIONS or card.effect.target == Targets.MINIONS_OR_HEROES)) or (self.card_type == CardTypes.WEAPON and card.effect.target == Targets.WEAPONS)
        correct_owner = card.effect.owner_filter == OwnerFilters.ENEMY or card.effect.owner_filter == OwnerFilters.ALL
        correct_creature_type = card.effect.type_filter == None or card.effect.type_filter == CardTypes.ALL or card.effect.type_filter == self.creature_type
        if correct_target and correct_owner and correct_creature_type and card.method == Methods.ALL:
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