from enums import *
from effects import *

class Card():
  def __init__(self, name, card_type, manacost, collectable=True, creature_type=None, attack=None, health=None, attributes=[], effect=None, condition=None):
    self.name = name
    self.card_type = card_type
    self.creature_type = creature_type
    self.original_health = health #used for reseting games and return to hand, never changes
    self.max_health = health #used during the game as the max health for healing, enrage etc, can change
    self.health = health #used during game as current health
    self.original_attack = attack
    self.attack = attack
    self.original_manacost = manacost
    self.manacost = manacost
    self.attributes = attributes
    self.effect = effect
    self.original_attributes = deepcopy(attributes)
    self.original_effect = deepcopy(effect)
    self.original_condition = deepcopy(condition)
    self.condition = condition
    self.owner = None
    self.attacks_this_turn = -1
    self.parent = None
    self.temp_attack = 0
    self.temp_health = 0
    self.perm_attack = 0
    self.perm_health = 0
    self.temp_attributes = []
    self.perm_attributes = []
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

  def get_manacost(self):
    manacost = self.manacost
    if self.effect and isinstance(self.effect, ChangeCost) and self.effect.trigger == Triggers.AURA and self.effect.method == Methods.SELF:
      manacost += self.effect.value(self)
    
    for card in self.owner.board.get_all():
      if card.effect and isinstance(card.effect, ChangeCost) and card.effect.trigger == Triggers.AURA and card.effect.method == Methods.ALL:
        if self.matches_card_requirements(card):
          manacost += card.effect.value(card)

    return max(manacost, 0)

  def matches_card_requirements(self, card):
    effect = card.effect
    type_okay = (self.card_type==CardTypes.MINION and (effect.target == Targets.MINION or effect.target == Targets.MINION_OR_HERO or effect.target==Targets.MINION_OR_SPELL))\
    or (self.card_type==CardTypes.WEAPON and (effect.target == Targets.WEAPON))\
    or (self.card_type==CardTypes.SPELL and (effect.target == Targets.SPELL or effect.target== Targets.MINION_OR_SPELL))

    owner_okay = (self.owner == card.owner and effect.owner_filter == OwnerFilters.FRIENDLY)\
    or (self.owner == card.owner.other_player and effect.owner_filter == OwnerFilters.ENEMY)\
    or (effect.owner_filter == OwnerFilters.ALL)
    
    creature_type_okay = (effect.type_filter == None or effect.type_filter == CreatureTypes.ALL)\
    or effect.type_filter == self.creature_type
    
    return type_okay and owner_okay and creature_type_okay

  def has_attribute(self, attribute):
    return attribute in self.attributes or attribute in self.temp_attributes or attribute in self.perm_attributes\
          or (self.condition and attribute in self.condition.result['attributes'] and self.condition.requirement(self.owner.game, self))
  
  def get_attack(self):
    
    aura_attack, _ = self.get_aura_stats()
    condition_attack = self.condition.result['temp_attack'] if self.condition and self.condition.requirement(self.owner.game, self) else 0
    return self.attack+self.perm_attack+self.temp_attack+condition_attack+aura_attack

  def get_health(self):
    _, aura_health = self.get_aura_stats()
    return self.health+self.temp_health+self.perm_health+aura_health

  def get_max_health(self):
    _, aura_health = self.get_aura_stats()
    return self.max_health+self.temp_health+self.perm_health+aura_health
    
  def get_aura_stats(self):
    aura_attack = 0
    aura_health = 0
    board = self.owner.board.get_all()
    last_index = len(board)-1
    for index, card in enumerate(board):
      if card.effect and card.effect.trigger == Triggers.AURA and self.matches_card_requirements(card):
        adjacent = False
        if self.parent == self.owner.board:
          my_index = self.parent.index_of(self)
          adjacent = card.effect.method == Methods.ADJACENT and (my_index == index-1 or my_index == index+1 or (my_index == 0 and index == last_index) or (my_index == last_index and index == 0))
        if card.effect.method == Methods.ALL or adjacent:
          if isinstance(card.effect, ChangeStats):
            aura_attack += card.effect.value[0]
            aura_health += card.effect.value[1]
        
    for card in self.parent.parent.other_player.board.get_all():
      if card.effect and card.effect.trigger == Triggers.AURA and self.matches_card_requirements(card):
        if card.effect.method == Methods.ALL:
          if isinstance(card.effect, ChangeStats):
            aura_attack += card.effect.value[0]
            aura_health += card.effect.value[1]

    return aura_attack, aura_health

  def reset(self):
    self.attacks_this_turn = -1
    self.temp_attack = 0
    self.temp_health = 0
    self.perm_attack = 0
    self.perm_health = 0 
    self.temp_attributes = []
    self.perm_attributes = []
    self.health = self.original_health
    self.effect = deepcopy(self.original_effect)
    self.attributes = deepcopy(self.original_attributes)
    self.condition = deepcopy(self.original_condition)
    self.manacost = self.original_manacost


  def get_string(self):
    if(self.card_type == CardTypes.MINION):
      return str((id(self), self.owner.name if self.owner else None, self.parent.name if self.parent else None, self.name, self.manacost, self.effect, str(self.attack+self.temp_attack)+"/"+str(self.health+self.temp_health)))
    else:
      return str((id(self), self.owner.name if self.owner else None, self.parent.name if self.parent else None, self.name, self.manacost, self.effect))

  def __str__(self):
    return self.get_string()

  def __repr__(self):
    return self.get_string()