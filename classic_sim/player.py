from hand import Hand
from board import Board
from graveyard import Graveyard
from copy import deepcopy

class Player():
  def __init__(self, player_class, deck, strategy):
    self.player_class = player_class
    self.deck = deepcopy(deck)
    self.deck.update_owner(self)
    self.strategy = strategy
    self.hero_power = None

    self.max_health = 30
    self.health = 30
    self.weapon = None
    self.attack = 0
    self.armor = 0
    self.attributes = []
    self.temp_attack = 0
    self.temp_health = 0
    self.perm_attack = 0
    self.perm_health = 0
    self.temp_attributes = []
    self.perm_attributes = []

    self.current_mana = 0
    self.max_mana = 0
   
    self.attacks_this_turn = 0
    self.used_hero_power = False
    self.hand = Hand(self)
    self.board = Board(self)
    self.graveyard = Graveyard(self)
    self.other_player = None
    self.game = None
    self.fatigue_damage = 1
    self.owner = self
    self.condition = None


  def reset(self):
    self.attacks_this_turn = 0
    self.temp_attack = 0
    self.temp_health = 0
    self.perm_attack = 0
    self.perm_health = 0
    self.temp_attributes = []
    self.perm_attributes = []
    self.health = 30
    self.armor = 0
    self.attack = 0


  def remove(self, card):
    if self.weapon == card:
      self.weapon = None

  def add(self, card):
    self.weapon = card

  def get_attack(self):
    conditional_attack = self.condition.result['temp_attack'] if self.condition and self.condition.requirement(self.game, self) else 0
    return self.attack+self.temp_attack+self.perm_attack+conditional_attack

  def get_health(self):
    conditional_health = self.condition.result['temp_health'] if self.condition and self.condition.requirement(self.game, self) else 0
    return self.health + self.temp_health + self.perm_health + conditional_health

  def get_max_health(self):
    conditional_health = self.condition.result['temp_health'] if self.condition and self.condition.requirement(self.game, self) else 0
    return self.max_health+self.temp_health+self.perm_health+conditional_health
  
  def has_attribute(self, attribute):
    player_has = attribute in self.attributes\
          or (self.condition and attribute in self.condition.result['attributes']\
          and self.condition.requirement(self.game, self))
    weapon_has = self.weapon and (attribute in self.weapon.attributes\
          or (self.weapon.condition and attribute in self.weapon.condition.result['attributes']\
            and self.weapon.condition.requirement(self.game, self)))
    temp_attributes_has = attribute in self.temp_attributes
    perm_attributes_has = attribute in self.perm_attributes
    return player_has or weapon_has or temp_attributes_has or perm_attributes_has

  def __str__(self):
    return str((self.name, self.player_class, str(self.health)))

  def __repr__(self):
    return str((self.name, self.player_class, str(self.health)))
