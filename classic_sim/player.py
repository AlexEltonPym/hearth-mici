from card_sets import get_hero_power

class Player():
  def __init__(self, player_class, deck, strategy):
    self.player_class = player_class    
    self.deck = deck
    self.strategy = strategy
    self.hero_power = get_hero_power(player_class)
    self.current_mana = 0
    self.max_mana = 0
    self.health = 30
    self.weapon = None
    self.attack = 0
    self.armor = 0
    self.has_attacked = False
    self.used_hero_power = False
    self.hand = []
    self.board = []
    self.graveyard = []
    self.other_player = None
    self.game = None
    self.fatigue_damage = 1

  def __str__(self):
    return str((self.name, self.player_class, str(self.health)))

  def __repr__(self):
    return str((self.name, self.player_class, str(self.health)))
