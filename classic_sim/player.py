from card_sets import get_utility_card, get_hero_power
from enums import *
import random

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

  def add_coin(self):
    coin = get_utility_card('coin')
    coin.parent = self.hand
    self.hand.append(coin)

  def deck_to_hand(self):
    new_card = self.deck.deck.pop()
    new_card.parent = self.hand
    self.hand.append(new_card)

  def deck_to_graveyard(self):
    new_card = self.deck.deck.pop()
    new_card.parent = self.graveyard
    self.graveyard.append(new_card)

  def draw(self, num_to_draw):
    for i in range(num_to_draw):
      if(len(self.deck.deck) > 0):
        if(len(self.hand) < 10):
          self.deck_to_hand()
        else:
          self.deck_to_graveyard()
      else:
        self.health -= self.fatigue_damage
        self.fatigue_damage += 1
      
  
  def mulligan(self):
    mulligan_count = 0
    for card in self.hand:
      if not self.strategy.mulligan_rule(card):
        self.hand.remove(card)
        card.parent = self.deck.deck
        self.deck.deck.append(card)
        mulligan_count += 1

    self.deck.shuffle()
    self.draw(mulligan_count)
        
  def take_turn(self):
    self.max_mana += 1
    self.current_mana = self.max_mana
    self.draw(1)
    self.has_attacked = False
    self.used_hero_power = False
    for minion in self.board:
      minion.has_attacked = False

    turn_passed = False
    while not turn_passed:
      available_actions = self.get_available_actions()
      next_action = self.strategy.choose_action(available_actions)
      turn_passed = self.game.perform_action(next_action)
    

  def get_available_effect_targets(self, card):
    available_targets = []
    for effect in card.card_details['effects']:
      filters = effect['filter']
      targets = effect['targets']
      if filters == Filters.FRIENDLY or filters == Filters.ALL:
        for card in self.board:
          if targets == Targets.MINIONS or targets == Targets.MINIONS_OR_HEROES or card.card_details['minion_type'] == targets:
            available_targets.append(card)
        if targets == Targets.HEROES or targets == Targets.MINIONS_OR_HEROES:
          available_targets.append(self)
      if filters == Filters.ENEMY or filters == Filters.ALL:
        for card in self.other_player.board:
          if targets == Targets.MINIONS or targets == Targets.MINIONS_OR_HEROES or card.card_details['minion_type'] == targets:
            available_targets.append(card)
        if targets == Targets.HEROES or targets == Targets.MINIONS_OR_HEROES:
          available_targets.append(self.other_player)
    return available_targets


  def get_minion_attack_actions(self):
    minion_attack_options = []
    for minion in self.board:
      if not minion.has_attacked:
        for target in self.game.get_available_targets(minion):
          minion_attack_options.append({'action_type': Actions.ATTACK, 'source': minion, 'target': target})
    return minion_attack_options
  
  def get_hero_attack_actions(self):
    hero_attack_options = []
    if self.attack > 0 and not self.has_attacked:
      for target in self.game.get_available_targets(self):
        hero_attack_options.append({'action_type': Actions.ATTACK, 'source': self, 'target': target})     
    return hero_attack_options

  def get_playable_minion_actions(self):
    playable_minion_actions = []
    if len(self.board) < 7:
      for card in filter(lambda card: card.card_details['mana'] <= self.current_mana and card.card_details['card_type'] == 'minion', self.hand):
        has_battlecry = False
        for effect in card.card_details['effects']:
          if effect['trigger'] == Triggers.BATTLECRY:
            has_battlecry = True
            battlecry_targets = self.get_available_effect_targets(card)
            if effect['method'] == Methods.TARGETED:
              for target in battlecry_targets:
                playable_minion_actions.append({'action_type': Actions.CAST_MINION, 'source': card, 'target': target})
            elif effect['method'] == Methods.RANDOMLY:
              playable_minion_actions.append({'action_type': Actions.CAST_MINION, 'source': card, 'target': random.choice(battlecry_targets)})
            else:
              playable_minion_actions.append({'action_type': Actions.CAST_MINION, 'source': card, 'target': 'board'})
        if not has_battlecry:
          playable_minion_actions.append({'action_type': Actions.CAST_MINION, 'source': card, 'target': 'board'})
    return playable_minion_actions


  def get_playable_spells_actions(self):
    playable_spell_actions = []
    for card in filter(lambda card: card.card_details['mana'] <= self.current_mana and card.card_details['card_type'] == 'spell', self.hand):
      for effect in card.card_details['effects']:
        if effect['method'] != Methods.NONE:
          cast_targets = self.get_available_effect_targets(card)
          if effect['method'] == Methods.TARGETED:
            for target in cast_targets:
              playable_spell_actions.append({'action_type': Actions.CAST_SPELL, 'source': card, 'target': target})
          elif effect['method'] == Methods.RANDOMLY:
            playable_spell_actions.append({'action_type': Actions.CAST_SPELL, 'source': card, 'target': random.choice(cast_targets)})
          else:
            playable_spell_actions.append({'action_type': Actions.CAST_SPELL, 'source': card, 'target': 'board'})
    return playable_spell_actions

  def get_hero_power_actions(self):
    hero_power_actions = []
    if self.current_mana >= 2 and not self.used_hero_power:
      hero_power_actions.append({'action_type': Actions.CAST_HERO_POWER, 'source': self.hero_power, 'target': self.other_player})
    return hero_power_actions

  def get_available_actions(self):
    available_actions = []

    available_actions.extend(self.get_minion_attack_actions())
    available_actions.extend(self.get_hero_attack_actions())
    available_actions.extend(self.get_playable_minion_actions())
    available_actions.extend(self.get_playable_spells_actions())
    available_actions.extend(self.get_hero_power_actions())
    available_actions.append({'action_type': Actions.END_TURN, 'source': self, 'target': 'board'})
    return available_actions

  def __str__(self):
    return str((self.name, self.player_class, str(self.health)))

  def __repr__(self):
    return str((self.name, self.player_class, str(self.health)))
