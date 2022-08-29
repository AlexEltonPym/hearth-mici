from enums import *
from random import choice
from player import Player
from card_sets import get_utility_card, get_hero_power
from effects import *
import copy

class Game():
  def __init__(self, _player, _enemy):
    self.original_player = _player
    self.original_enemy = _enemy

    self.setup_players()
    self.start_game()

  
  def setup_players(self):

    self.player = copy.deepcopy(self.original_player)
    self.enemy = copy.deepcopy(self.original_enemy)
    self.player.other_player = self.enemy
    self.enemy.other_player = self.player

    self.player.name = 'player'
    self.enemy.name = 'enemy'

    self.player.deck.update_owner(self.player)
    self.enemy.deck.update_owner(self.enemy)

    self.player.hero_power = get_hero_power(self.player.player_class)
    self.player.hero_power.set_owner(self.player)
    self.player.hero_power.parent = self.player

    self.enemy.hero_power = get_hero_power(self.enemy.player_class)
    self.enemy.hero_power.set_owner(self.enemy)
    self.enemy.hero_power.parent = self.enemy

  def start_game(self):
    self.player.deck.shuffle()
    self.enemy.deck.shuffle()
    
    self.current_player = choice([self.player, self.enemy])

    self.draw(self.current_player, 4)
    self.mulligan(self.current_player)

    self.draw(self.current_player.other_player, 3)
    self.mulligan(self.current_player.other_player)
    self.add_coin(self.current_player.other_player)

  def reset_game(self):

    for player in [self.player, self.enemy]:
      player.health = 30
      player.weapon = None
      player.had_attacked = False

      all_cards = player.graveyard.get_all() + player.board.get_all() + player.hand.get_all()
      for card in all_cards:
        card.has_attacked = False
        card.health = card.original_health
        card.change_parent(card.owner.deck)

  def untap(self):
    self.current_player.max_mana += 1
    self.current_player.current_mana = self.current_player.max_mana
    self.draw(self.current_player, 1)
    self.current_player.has_attacked = False
    self.current_player.used_hero_power = False
    for minion in self.current_player.board.get_all():
      minion.has_attacked = False
      minion.temp_attack = 0
      minion.temp_health = 0


  def take_turn(self):
    self.untap()
    turn_passed = False

    while not turn_passed:

      turn_passed = self.current_player.strategy.choose_action(self)
      if turn_passed:
        self.current_player = self.current_player.other_player

  def add_coin(self, player):
    coin = get_utility_card('coin')
    coin.set_owner(player)
    coin.set_parent(coin.owner.hand)

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
    self.current_player.current_mana -= action['source'].mana
    for effect in action['source'].effects:
      effect.resolve_action(self, action)


  def cast_minion(self, action):
    self.current_player.current_mana -= action['source'].mana
    # print(f"casting {action['source']}")
    action['source'].change_parent(action['source'].owner.board)

    for effect in action['source'].effects:
      if effect.trigger == Triggers.BATTLECRY:
        effect.resolve_action(self, action)


  def cast_spell(self, action):
    self.current_player.current_mana -= action['source'].mana
    action['source'].change_parent(action['source'].owner.graveyard)
    for effect in action['source'].effects:
      effect.resolve_action(self, action)

  def handle_attack(self, action):
    self.deal_damage(action['target'], action['source'].attack + action['source'].temp_attack)
    self.deal_damage(action['source'], action['target'].attack + action['target'].temp_attack)
    action['source'].has_attacked = True

  def deal_damage(self, target, amount):
    if Attributes.DIVINE_SHIELD in target.attributes:
      target.attributes.remove(Attributes.DIVINE_SHIELD)
    else:
      target.health -= amount
      self.check_dead(target)

  def check_dead(self, card):
    if card.health <= 0 and not isinstance(card, Player):
      card.change_parent(card.owner.graveyard)

  def get_available_targets(self, card):
    targets = []
    taunt_targets = list(filter(lambda target: Attributes.TAUNT in target.attributes, card.owner.other_player.board.get_all()))
    if len(taunt_targets) > 0:
      targets = taunt_targets
    else:
      targets = [card.owner.other_player]
      targets.extend(card.owner.other_player.board.get_all())

    return targets

  def get_playable_spells_actions(self, player):
    playable_spell_actions = []
    for card in filter(lambda card: card.mana <= player.current_mana and card.card_type == CardTypes.SPELL, player.hand.get_all()):
      for effect in card.effects:
        if effect.method == Methods.SELF:
          playable_spell_actions.append({'action_type': Actions.CAST_SPELL, 'source': card, 'target': player})
        else:
          cast_targets = self.get_available_effect_targets(player, card)
          if effect.method == Methods.TARGETED or effect.method == Methods.ALL:
            for target in cast_targets:
              playable_spell_actions.append({'action_type': Actions.CAST_SPELL, 'source': card, 'target': target})
          elif effect.method == Methods.RANDOMLY:
            playable_spell_actions.append({'action_type': Actions.CAST_SPELL, 'source': card, 'target': choice(cast_targets)})
    return playable_spell_actions

  def get_hero_power_actions(self, player):
    hero_power_actions = []
    if player.current_mana >= 2 and not player.used_hero_power:

      for effect in player.hero_power.effects:
        if effect.method == Methods.SELF:
          hero_power_actions.append({'action_type': Actions.CAST_HERO_POWER, 'source': player.hero_power, 'target': player})
        else:
          cast_targets = self.get_available_effect_targets(player, player.hero_power)
          if effect.method == Methods.TARGETED or effect.method == Methods.ALL:
            for target in cast_targets:
              hero_power_actions.append({'action_type': Actions.CAST_HERO_POWER, 'source': player.hero_power, 'target': target})
          elif effect.method == Methods.RANDOMLY:
            hero_power_actions.append({'action_type': Actions.CAST_HERO_POWER, 'source': player.hero_power, 'target': choice(cast_targets)})
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
    new_card.set_parent(new_card.owner.hand)
    # print(f"drawing {new_card}")


  def deck_to_graveyard(self, player):
    new_card = player.deck.pop()
    new_card.set_parent(new_card.owner.graveyard)

  def draw(self, player, num_to_draw):
    for i in range(num_to_draw):
      if(len(player.deck.get_all()) > 0):
        if(len(player.hand.get_all()) < 10):
          self.deck_to_hand(player)
        else:
          self.deck_to_graveyard(player)
      else:
        player.health -= player.fatigue_damage
        player.fatigue_damage += 1

  def mulligan(self, player):
    mulligan_count = 0
    for card in player.hand.get_all():
      if not player.strategy.mulligan_rule(card):
        card.change_parent(card.owner.deck)
        mulligan_count += 1

    player.deck.shuffle()
    self.draw(player, mulligan_count)

  def get_available_effect_targets(self, player, card):
    available_targets = []
    for effect in card.effects:
      owner_filter = effect.owner_filter
      type_filter = effect.type_filter
      target = effect.target
      if owner_filter == OwnerFilters.FRIENDLY or owner_filter == OwnerFilters.ALL:
        if target == Targets.MINIONS or target == Targets.MINIONS_OR_HEROES:
          for minion in player.board.get_all():
            if type_filter == None or type_filter == CreatureTypes.ALL or type_filter == minion.creature_type:
              available_targets.append(minion) 
        if target == Targets.HEROES or target == Targets.MINIONS_OR_HEROES:
          available_targets.append(player)
        if target == Targets.WEAPONS:
          available_targets.append(player.weapon)
      if owner_filter == OwnerFilters.ENEMY or owner_filter == OwnerFilters.ALL:
        if target == Targets.MINIONS or target == Targets.MINIONS_OR_HEROES:
          for minion in player.other_player.board.get_all():
            if type_filter == None or type_filter == CreatureTypes.ALL or type_filter == minion.creature_type:
              available_targets.append(minion)
        if target == Targets.HEROES or target == Targets.MINIONS_OR_HEROES:
          available_targets.append(player.other_player)
        if target == Targets.WEAPONS:
          available_targets.append(player.other_player.weapon)
    return available_targets



  def get_minion_attack_actions(self, player):
    minion_attack_options = []
    for minion in player.board.get_all():
      if not minion.has_attacked and minion.attack+minion.temp_attack > 0:
        for target in self.get_available_targets(minion):
          minion_attack_options.append({'action_type': Actions.ATTACK, 'source': minion, 'target': target})

    return minion_attack_options
  

  def get_hero_attack_actions(self, player):
    hero_attack_options = []
    if player.attack > 0 and not player.has_attacked:
      for target in self.get_available_targets(player):
        hero_attack_options.append({'action_type': Actions.ATTACK, 'source': player, 'target': target})     
    return hero_attack_options


  def get_playable_minion_actions(self, player):
    playable_minion_actions = []
    # print(len(player.hand.get_all()))
    # print(player.hand.get_all())
    # for index, card in enumerate(player.hand.get_all()):
    #   print(index, card)

    if len(player.board.get_all()) < 7:
      for card in filter(lambda card: card.mana <= player.current_mana and card.card_type == CardTypes.MINION, player.hand.get_all()):
        has_battlecry = False
        for effect in card.effects:
          if effect.trigger == Triggers.BATTLECRY:
            has_battlecry = True
            battlecry_targets = self.get_available_effect_targets(player, card)
            if effect.method == Methods.TARGETED or effect.method == Methods.ALL:
              for target in battlecry_targets:
                playable_minion_actions.append({'action_type': Actions.CAST_MINION, 'source': card, 'target': target})
            elif effect.method == Methods.RANDOMLY:
              playable_minion_actions.append({'action_type': Actions.CAST_MINION, 'source': card, 'target': choice(battlecry_targets)})
        if not has_battlecry:
          playable_minion_actions.append({'action_type': Actions.CAST_MINION, 'source': card, 'target': player.board})
    return playable_minion_actions


  def simulate_game(self):
    for _ in range(100):

      self.take_turn()
      if(self.player.health <= 0):
        return 0
      elif(self.enemy.health <= 0):
        return 1
