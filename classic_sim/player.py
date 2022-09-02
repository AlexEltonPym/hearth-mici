from hand import Hand
from board import Board
from graveyard import Graveyard
from copy import deepcopy

class Player():
  def __init__(self, player_class, deck, strategy):
    self.player_class = player_class
    self.deck = deepcopy(deck)
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

     
  def remove(self, card):
    if self.weapon == card:
      self.weapon = None

  def add(self, card):
    self.weapon = card

  def get_attack(self, game):
    return self.attack+self.temp_attack+(self.condition.result['temp_attack'] if self.condition and self.condition.requirement(game, self) else 0)

  
  def has_attribute(self, game, attribute):
    return attribute in self.attributes\
          or (self.condition and attribute in self.condition.result['attributes']\
          and self.condition.requirement(game, self))\

  def __str__(self):
    return str((self.name, self.player_class, str(self.health)))

  def __repr__(self):
    return str((self.name, self.player_class, str(self.health)))
