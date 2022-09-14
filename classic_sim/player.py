
from zones import SecretsZone, Hand, Board, Graveyard
from copy import deepcopy
from enums import *

class Player():
  def __init__(self, name, game_manager, player_class, deck_constructor, strategy):
    self.name = name
    self.game_manager = game_manager
    self.player_class = player_class
    self.deck = deepcopy(deck_constructor(self))
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
    self.secrets_zone = SecretsZone(self)
    self.other_player = None
    self.game = None
    self.fatigue_damage = 1
    self.owner = self
    self.parent = self
    self.condition = None

    self.pool = None
    self.minions_played_this_turn = 0

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
    self.fatigue_damage = 1
    self.current_mana = 0
    self.max_mana = 0
    self.minions_played_this_turn = 0

  def remove(self, card):
    if self.weapon == card:
      self.weapon = None

  def add(self, card):
    self.weapon = card

  def matches_card_requirements(self, card):
    effect = card.effect
    type_okay = effect.target == Targets.HERO or effect.target == Targets.MINION_OR_HERO

    owner_okay = (self == card.owner and effect.owner_filter == OwnerFilters.FRIENDLY)\
    or (self == card.owner.other_player and effect.owner_filter == OwnerFilters.ENEMY)\
    or (effect.owner_filter == OwnerFilters.ALL)
    
    return type_okay and owner_okay


  def get_attack(self):
    conditional_attack = self.condition.result['temp_attack'] if self.condition and self.condition.requirement(self.game, self) else 0
    return self.attack+self.temp_attack+self.perm_attack+conditional_attack

  def get_health(self):
    return self.health + self.temp_health + self.perm_health

  def get_max_health(self):
    return self.max_health+self.temp_health+self.perm_health
  
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

  def get_spell_damage(self):
    spell_damage_bonus = 0
    for card in self.board:
      if card.has_attribute(Attributes.SPELL_DAMAGE):
        spell_damage_bonus += 1
    if self.has_attribute(Attributes.SPELL_DAMAGE):
      spell_damage_bonus += 1
    return spell_damage_bonus

  def __str__(self):
    return str((self.name, self.player_class, str(self.health)))

  def __repr__(self):
    return str((self.name, self.player_class, str(self.health)))
