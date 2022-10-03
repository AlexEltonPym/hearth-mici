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
      manacost += self.effect.value(Action(Actions.GET_MANACOST, self, [self])) #dyanmics require actions by default so we need to wrap this inside one.
    
    for card in self.owner.board.get_all() + self.owner.other_player.board.get_all():
      if card.effect and isinstance(card.effect, ChangeCost) and card.effect.trigger == Triggers.AURA and card.effect.method == Methods.ALL:
        if self.matches_card_requirements(card):
          manacost += card.effect.value(Action(Actions.GET_MANACOST, card, [card])) #dyanmics require actions by default so we need to wrap this inside one.

    return max(manacost, 0)

  def matches_card_requirements(self, card):
    effect = card.effect
    type_okay = (self.card_type==CardTypes.MINION and (effect.target == Targets.MINION or effect.target == Targets.MINION_OR_HERO or effect.target==Targets.MINION_OR_SPELL))\
    or (self.card_type==CardTypes.WEAPON and (effect.target == Targets.WEAPON))\
    or (self.card_type==CardTypes.SPELL and (effect.target == Targets.SPELL or effect.target== Targets.MINION_OR_SPELL))\
    or (self.card_type==CardTypes.SECRET and (effect.target == Targets.SECRET or effect.target==Targets.SPELL or effect.target==Targets.MINION_OR_SPELL))

    # print(effect.owner_filter)
    # print(id(self.owner))
    # print(id(card.owner))
    # print(self.owner == card.owner)

    owner_okay = (self.owner == card.owner and effect.owner_filter == OwnerFilters.FRIENDLY)\
    or (self.owner == card.owner.other_player and effect.owner_filter == OwnerFilters.ENEMY)\
    or (effect.owner_filter == OwnerFilters.ALL)
    
    creature_type_okay = (effect.type_filter == None or effect.type_filter == CreatureTypes.ALL)\
    or effect.type_filter == self.creature_type


    try:
      dynamics_okay = effect.dynamic_filter == None or effect.dynamic_filter(Action(Actions.CAST_EFFECT, self, [card]))
    except AttributeError:
      dynamics_okay = True
        
    # print(f"{type_okay=}")
    # print(f"{owner_okay=}")
    # print(f"{creature_type_okay=}")
    # print(f"{dynamics_okay=}")

    return type_okay and owner_okay and creature_type_okay and dynamics_okay

  def has_attribute(self, attribute):
    return attribute in self.attributes or attribute in self.temp_attributes or attribute in self.perm_attributes\
          or (self.condition and attribute in self.condition.result['attributes'] and self.condition.requirement(self.owner.game, self))\
          or attribute in self.get_aura_attributes()
  
  def remove_attribute(self, attribute):
    if attribute in self.attributes: self.attributes.remove(attribute)
    if attribute in self.temp_attributes: self.temp_attributes.remove(attribute)
    if attribute in self.perm_attributes: self.perm_attributes.remove(attribute)

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
    
  def get_aura_attributes(self):
    aura_attributes = []
    board = self.owner.board
    last_index = len(board)-1
    for index, card in enumerate(board):
      if card != self and card.effect and card.effect.trigger == Triggers.AURA and self.matches_card_requirements(card):
        adjacent = False
        if self.parent == self.owner.board:
          my_index = self.parent.index_of(self)
          adjacent = card.effect.method == Methods.ADJACENT and (my_index == index-1 or my_index == index+1 or (my_index == 0 and index == last_index) or (my_index == last_index and index == 0))
        if card.effect.method == Methods.ALL or adjacent:
          if isinstance(card.effect, GiveAttribute):
            aura_attributes.append(card.effect.value)
        
    for card in self.parent.parent.other_player.board:
      if card.effect and card.effect.trigger == Triggers.AURA and self.matches_card_requirements(card):
        if card.effect.method == Methods.ALL:
          if isinstance(card.effect, GiveAttribute):
            aura_attributes.append(card.effect.value)

    return aura_attributes

  def get_aura_stats(self):
    aura_attack = 0
    aura_health = 0
    board = self.owner.board
    last_index = len(board)-1
    for index, card in enumerate(board):
      if card != self and card.effect and card.effect.trigger == Triggers.AURA and self.matches_card_requirements(card):
        adjacent = False
        if self.parent == self.owner.board:
          my_index = self.parent.index_of(self)
          adjacent = card.effect.method == Methods.ADJACENT and (my_index == index-1 or my_index == index+1 or (my_index == 0 and index == last_index) or (my_index == last_index and index == 0))
        if card.effect.method == Methods.ALL or adjacent:
          if isinstance(card.effect, ChangeStats):
            aura_attack += card.effect.value[0](Action(Actions.CAST_EFFECT, card, [self]))
            aura_health += card.effect.value[1](Action(Actions.CAST_EFFECT, card, [self]))
        
    for card in self.parent.parent.other_player.board:
      if card.effect and card.effect.trigger == Triggers.AURA and self.matches_card_requirements(card):
        if card.effect.method == Methods.ALL:
          if isinstance(card.effect, ChangeStats):
            aura_attack += card.effect.value[0](Action(Actions.CAST_EFFECT, card, [self]))
            aura_health += card.effect.value[1](Action(Actions.CAST_EFFECT, card, [self]))

    return aura_attack, aura_health

  def return_to_hand_reset(self):
    self.attacks_this_turn = -1
    self.attack = self.original_attack
    self.temp_attack = 0
    self.temp_health = 0
    self.perm_attack = 0
    self.perm_health = 0 
    self.temp_attributes = []
    self.perm_attributes = []
    self.max_health = self.original_health
    self.health = self.max_health
    self.effect = deepcopy(self.original_effect)
    self.attributes = deepcopy(self.original_attributes)
    self.condition = deepcopy(self.original_condition)
    #dont change manacost so that freezing trap works, all other change cost effects are auras

  def reset(self):
    self.attacks_this_turn = -1
    self.attack = self.original_attack
    self.temp_attack = 0
    self.temp_health = 0
    self.perm_attack = 0
    self.perm_health = 0 
    self.temp_attributes = []
    self.perm_attributes = []
    self.max_health = self.original_health
    self.health = self.max_health
    self.effect = deepcopy(self.original_effect)
    self.attributes = deepcopy(self.original_attributes)
    self.condition = deepcopy(self.original_condition)
    self.manacost = self.original_manacost #when reseting for making new games, mana must be reset

  def get_string(self):
    if(self.card_type == CardTypes.MINION):
      return str((id(self), self.owner.name if self.owner else None, self.parent.name if self.parent else None, self.name, self.manacost, self.effect, str(self.attack+self.temp_attack)+"/"+str(self.health+self.temp_health)))
    else:
      return str((id(self), self.owner.name if self.owner else None, self.parent.name if self.parent else None, self.name, self.manacost, self.effect))

  def __str__(self):
    return self.get_string()

  def __repr__(self):
    return self.get_string()