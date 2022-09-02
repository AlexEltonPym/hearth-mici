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

     
  def remove(self, card):
    if self.weapon == card:
      self.weapon = None

  def add(self, card):
    self.weapon = card
  
  def __str__(self):
    return str((self.name, self.player_class, str(self.health)))

  def __repr__(self):
    return str((self.name, self.player_class, str(self.health)))
