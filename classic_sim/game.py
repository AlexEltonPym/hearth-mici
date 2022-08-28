from enums import *
from random import choice
from player import Player
from card_sets import get_utility_card, get_hero_power
import copy

class Game():
  def __init__(self, player, enemy):
  
    self.player = copy.deepcopy(player)
    self.enemy = copy.deepcopy(enemy)

    self.player.other_player = self.enemy
    self.player.name = 'player'
    self.enemy.other_player = self.player
    self.enemy.name = 'enemy'

    self.player.deck.update_owner(self.player)
    self.enemy.deck.update_owner(self.enemy)


    self.current_player = choice([self.player, self.enemy])

    self.player.deck.shuffle()
    self.enemy.deck.shuffle()



    self.draw(self.current_player, 4)
    self.mulligan(self.current_player)
    self.draw(self.current_player.other_player, 3)
    self.mulligan(self.current_player.other_player)
    self.add_coin(self.current_player.other_player)
  
  def take_turn(self):
    self.current_player.max_mana += 1
    self.current_player.current_mana = self.current_player.max_mana
    self.draw(self.current_player, 1)
    self.current_player.has_attacked = False
    self.current_player.used_hero_power = False
    for minion in self.current_player.board.get_all():
      minion.has_attacked = False

    turn_passed = False
    while not turn_passed:
      turn_passed = self.current_player.strategy.choose_action(self)
      if turn_passed:
        self.current_player = self.current_player.other_player

  def add_coin(self, player):
    coin = get_utility_card('coin')
    coin.owner = player
    coin.parent = player.hand
    player.hand.add(coin)

  def perform_action(self, action):
    if action['action_type'] == Actions.CAST_MINION:
      self.cast_minion(action)
    elif action['action_type'] == Actions.CAST_SPELL:
      self.cast_spell(action)
    elif action['action_type'] == Actions.ATTACK:
      self.handle_attack(action)
    elif action['action_type'] == Actions.CAST_HERO_POWER:
      self.cast_hero_power(action)
    elif action['action_type'] == Actions.END_TURN:
      return True
    return False

  def cast_hero_power(self, action):
    self.current_player.used_hero_power = True
    self.current_player.current_mana -= action['source'].card_details['mana']
    for effect in action['source'].card_details['effects']:
      self.resolve_effect(effect, action)


  def cast_minion(self, action):
    self.current_player.current_mana -= action['source'].card_details['mana']
    action['source'].parent = self.current_player.board
    self.current_player.board.add(action['source'])
    self.current_player.hand.remove(action['source'])
    for effect in action['source'].card_details['effects']:
      if effect['trigger'] == Triggers.BATTLECRY:
        self.resolve_effect(effect, action)


  def cast_spell(self, action):
    self.current_player.current_mana -= action['source'].card_details['mana']
    self.current_player.hand.remove(action['source'])
    action['source'].parent = self.current_player.graveyard
    self.current_player.graveyard.add(action['source'])
    for effect in action['source'].card_details['effects']:
      self.resolve_effect(effect, action)

  def handle_attack(self, action):
    action['target'].card_details['health'] -= action['source'].card_details['attack']
    action['source'].has_attacked = True

    if type(action['target']) != Player and action['target'].card_details['health'] <= 0:
      action['target'].parent.remove(action['target'])
      action['target'].owner.graveyard.add(action['target'])
      action['target'].parent = action['target'].owner.graveyard



  def resolve_effect(self, effect, action):
    if effect['effect_type'] == EffectType.GAIN_MANA:
      self.gain_mana(effect, action)
    elif effect['effect_type'] == EffectType.DEAL_DAMAGE:
      self.deal_damage(effect, action)


  def deal_damage(self, effect, action):
    action['target'].card_details['health'] -= effect['amount']
    if type(action['target']) != Player and action['target'].card_details['health'] <= 0:
      action['target'].parent.remove(action['target'])
      action['target'].owner.graveyard.add(action['target'])
      action['target'].parent = action['target'].owner.graveyard

  def gain_mana(self, effect, action):
    action['target'].current_mana += effect['amount']

  def get_available_targets(self, card):
    targets = []
    taunt_targets = list(filter(lambda target: Attributes.TAUNT in target.card_details['attributes'], card.owner.other_player.board.get_all()))
    if len(taunt_targets) > 0:
      targets = taunt_targets
    else:
      targets = [card.owner.other_player]
      targets.extend(card.owner.other_player.board.get_all())

    return targets

  def get_playable_spells_actions(self, player):
    playable_spell_actions = []
    for card in filter(lambda card: card.card_details['mana'] <= player.current_mana and card.card_details['card_type'] == CardType.SPELL, player.hand.get_all()):

      for effect in card.card_details['effects']:
        if effect['method'] != Methods.NONE:
          cast_targets = self.get_available_effect_targets(player, card)
          if effect['method'] == Methods.TARGETED:
            for target in cast_targets:
              playable_spell_actions.append({'action_type': Actions.CAST_SPELL, 'source': card, 'target': target})
          elif effect['method'] == Methods.RANDOMLY:
            playable_spell_actions.append({'action_type': Actions.CAST_SPELL, 'source': card, 'target': choice(cast_targets)})
          else:
            playable_spell_actions.append({'action_type': Actions.CAST_SPELL, 'source': card, 'target': player.board})
        else:
          playable_spell_actions.append({'action_type': Actions.CAST_SPELL, 'source': card, 'target': player})
    return playable_spell_actions

  def get_hero_power_actions(self, player):
    hero_power_actions = []
    if player.current_mana >= 2 and not player.used_hero_power:
      hero_power_actions.append({'action_type': Actions.CAST_HERO_POWER, 'source': player.hero_power, 'target': player.other_player})
    return hero_power_actions

  def get_available_actions(self, player):
    available_actions = []

    available_actions.extend(self.get_minion_attack_actions(player))

    available_actions.extend(self.get_hero_attack_actions(player))
    available_actions.extend(self.get_playable_minion_actions(player))
    available_actions.extend(self.get_playable_spells_actions(player))
    available_actions.extend(self.get_hero_power_actions(player))
    available_actions.append({'action_type': Actions.END_TURN, 'source': player, 'target': player.board})
    return available_actions


  def deck_to_hand(self, player):
    new_card = player.deck.pop()
    new_card.parent = player.hand
    player.hand.add(new_card)

  def deck_to_graveyard(self, player):
    new_card = player.deck.pop()
    new_card.parent = player.graveyard
    player.graveyard.add(new_card)

  def draw(self, player, num_to_draw):
    for i in range(num_to_draw):
      if(len(player.deck.get_all()) > 0):
        if(len(player.hand.get_all()) < 10):
          self.deck_to_hand(player)
        else:
          self.deck_to_graveyard(player)
      else:
        player.card_details['health'] -= player.fatigue_damage
        player.fatigue_damage += 1

  def mulligan(self, player):
    mulligan_count = 0
    for card in player.hand.get_all():
      if not player.strategy.mulligan_rule(card):
        player.hand.remove(card)
        card.parent = player.deck
        player.deck.add(card)
        mulligan_count += 1

    player.deck.shuffle()
    self.draw(player, mulligan_count)

  def get_available_effect_targets(self, player, card):
    available_targets = []
    for effect in card.card_details['effects']:
      filters = effect['filter']
      targets = effect['targets']
      if filters == Filters.FRIENDLY or filters == Filters.ALL:
        for card in player.board.get_all():
          if targets == Targets.MINIONS or targets == Targets.MINIONS_OR_HEROES or card.card_details['minion_type'] == targets:
            available_targets.append(card)
        if targets == Targets.HEROES or targets == Targets.MINIONS_OR_HEROES:
          available_targets.append(player)
      if filters == Filters.ENEMY or filters == Filters.ALL:
        for card in player.other_player.board.get_all():
          if targets == Targets.MINIONS or targets == Targets.MINIONS_OR_HEROES or card.card_details['minion_type'] == targets:
            available_targets.append(card)
        if targets == Targets.HEROES or targets == Targets.MINIONS_OR_HEROES:
          available_targets.append(player.other_player)
    return available_targets



  def get_minion_attack_actions(self, player):
    minion_attack_options = []
    for minion in player.board.get_all():
      if not minion.has_attacked:
        for target in self.get_available_targets(minion):
          minion_attack_options.append({'action_type': Actions.ATTACK, 'source': minion, 'target': target})

    return minion_attack_options
  

  def get_hero_attack_actions(self, player):
    hero_attack_options = []
    if player.card_details['attack'] > 0 and not player.has_attacked:
      for target in self.get_available_targets(player):
        hero_attack_options.append({'action_type': Actions.ATTACK, 'source': player, 'target': target})     
    return hero_attack_options


  def get_playable_minion_actions(self, player):
    playable_minion_actions = []
    if len(player.board.get_all()) < 7:
      for card in filter(lambda card: card.card_details['mana'] <= player.current_mana and card.card_details['card_type'] == CardType.MINION, player.hand.get_all()):
        has_battlecry = False
        for effect in card.card_details['effects']:
          if effect['trigger'] == Triggers.BATTLECRY:
            has_battlecry = True
            battlecry_targets = self.get_available_effect_targets(player, card)
            if effect['method'] == Methods.TARGETED:
              for target in battlecry_targets:
                playable_minion_actions.append({'action_type': Actions.CAST_MINION, 'source': card, 'target': target})
            elif effect['method'] == Methods.RANDOMLY:
              playable_minion_actions.append({'action_type': Actions.CAST_MINION, 'source': card, 'target': choice(battlecry_targets)})
            else:
              playable_minion_actions.append({'action_type': Actions.CAST_MINION, 'source': card, 'target': player.board})
        if not has_battlecry:
          playable_minion_actions.append({'action_type': Actions.CAST_MINION, 'source': card, 'target': player.board})
    return playable_minion_actions


  def simulate_game(self):
    for _ in range(8000):

      self.take_turn()

      if(self.player.card_details['health'] <= 0):
        return 0
      elif(self.enemy.card_details['health'] <= 0):
        return 1
