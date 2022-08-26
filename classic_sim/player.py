from card_sets import get_hero_power
from hand import Hand
from board import Board
from graveyard import Graveyard
import cython

class Player():
  def __init__(self, player_class, deck, strategy):
    self.player_class = player_class
    self.deck = deck
    self.strategy = strategy
    self.hero_power = get_hero_power(player_class)
    self.hero_power.owner = self
    self.hero_power.parent = self
    self.card_details = {
      'health': 30,
      'weapon': None,
      'attack': 0,
      'armor': 0
    }
    self.current_mana: cython.int = 0
    self.max_mana = 0
   
    self.has_attacked = False
    self.used_hero_power = False
    self.hand = Hand(self)
    self.board = Board(self)
    self.graveyard = Graveyard(self)
    self.other_player = None
    self.game = None
    self.fatigue_damage = 1

  def __str__(self):
    return str((self.name, self.player_class, str(self.card_details['health'])))

  def __repr__(self):
    return str((self.name, self.player_class, str(self.card_details['health'])))
