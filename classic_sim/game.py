from enums import *
from numpy import unique
from player import Player
from card_sets import get_utility_card, get_hero_power
from effects import *
import copy
from action import Action

class Game():
  def __init__(self, _player, _enemy, random_state):
    self.random_state = random_state

    self.player = copy.deepcopy(_player)
    self.enemy = copy.deepcopy(_enemy)

    self.setup_players()
    self.start_game()

  
  def setup_players(self):
    self.player.game = self
    self.enemy.game = self

    self.player.other_player = self.enemy
    self.enemy.other_player = self.player

    self.player.name = 'player'
    self.enemy.name = 'enemy'



    self.player.hero_power = get_hero_power(self.player.player_class)
    self.player.hero_power.set_owner(self.player)
    self.player.hero_power.parent = self.player

    self.enemy.hero_power = get_hero_power(self.enemy.player_class)
    self.enemy.hero_power.set_owner(self.enemy)
    self.enemy.hero_power.parent = self.enemy

  def start_game(self):
    self.player.deck.shuffle()
    self.enemy.deck.shuffle()
    
    self.current_player = self.random_state.choice([self.player, self.enemy])

    self.draw(self.current_player, 3)
    self.mulligan(self.current_player)

    self.draw(self.current_player.other_player, 4)
    self.mulligan(self.current_player.other_player)
    self.add_coin(self.current_player.other_player)

  def reset_game(self):
    for player in [self.player, self.enemy]:
      all_cards = player.graveyard.get_all() + player.board.get_all() + player.hand.get_all()
      if player.weapon:
        all_cards.append(player.weapon)
        player.weapon = None
      for card in all_cards:
        if card.collectable:
          card.reset()
          card.change_parent(card.owner.deck)
        else:
          card.parent.remove(card)
          del card
      player.reset()

  def untap(self):
    self.current_player.max_mana += 1
    self.current_player.current_mana = self.current_player.max_mana
    self.draw(self.current_player, 1)
    self.current_player.attacks_this_turn = 0
    self.current_player.used_hero_power = False
    for minion in self.current_player.board.get_all():
      minion.attacks_this_turn = 0



  def take_turn(self):
    self.untap()
    turn_passed = False

    while not turn_passed:
      turn_passed = self.current_player.strategy.choose_action(self)
      if self.player.health <= 0:
        return 0
      elif self.enemy.health <= 0:
        return 1
      if turn_passed:
        self.end_turn()
    return -1

  def end_turn(self):
    self.current_player.temp_attack = 0
    self.current_player.temp_health = 0
    self.current_player.temp_attributes = []
  
    for minion in self.current_player.board.get_all():
      minion.temp_attack = 0
      minion.temp_health = 0
      minion.temp_attributes = []

    self.current_player = self.current_player.other_player


  def add_coin(self, player):
    coin = get_utility_card('Coin')
    coin.set_owner(player)
    coin.set_parent(coin.owner.hand)

  def perform_action(self, action):
    if action.action_type == Actions.CAST_MINION:
      self.cast_minion(action)
    elif action.action_type == Actions.CAST_SPELL:
      self.cast_spell(action)
    elif action.action_type == Actions.CAST_EFFECT:
      self.cast_effect(action)
    elif action.action_type == Actions.CAST_WEAPON:
      self.cast_weapon(action)
    elif action.action_type == Actions.ATTACK:
      self.handle_attack(action)
    elif action.action_type == Actions.CAST_HERO_POWER:
      self.cast_hero_power(action)
    elif action.action_type == Actions.END_TURN:
      return True
    return False

  def cast_hero_power(self, action):
    self.current_player.used_hero_power = True
    self.current_player.current_mana -= action.source.mana
    action.source.effect.resolve_action(self, action)


  def cast_minion(self, action):
    self.current_player.current_mana -= action.source.mana
    action.source.change_parent(action.source.owner.board)

    if action.source.effect and action.source.effect.trigger == Triggers.BATTLECRY:
      action.source.effect.resolve_action(self, action)


  def cast_spell(self, action):
    self.current_player.current_mana -= action.source.mana
    action.source.change_parent(action.source.owner.graveyard)
    action.source.effect.resolve_action(self, action)

  def cast_effect(self, action):
    action.source.effect.resolve_action(self, action)

  def cast_weapon(self, action):
    self.current_player.current_mana -= action.source.mana
    action.source.change_parent(action.source.owner)
    if action.source.effect and action.source.effect.trigger == Triggers.BATTLECRY:
      action.source.effect.resolve_action(self, action)

  def handle_attack(self, action):
    if isinstance(action.source, Player) and action.source.weapon:
      damage = action.source.get_attack() + action.source.weapon.attack
      other_damage = action.targets[0].get_attack()
      action.source.weapon.health -= 1
      self.check_dead(action.source.weapon)
    else:
      damage = action.source.get_attack()
      other_damage = action.targets[0].get_attack()
    self.deal_damage(action.targets[0], damage)
    self.deal_damage(action.source, other_damage)
    if action.source.attacks_this_turn == -1: #used charge to attack
      action.source.attacks_this_turn += 2
    else:
      action.source.attacks_this_turn += 1
    if Attributes.STEALTH in action.source.attributes:
      action.source.attributes.remove(Attributes.STEALTH)


  def deal_damage(self, target, amount):
    if Attributes.DIVINE_SHIELD in target.attributes:
      target.attributes.remove(Attributes.DIVINE_SHIELD)
    else:
      target.health -= amount
      self.check_dead(target)

  def check_dead(self, card):
    if card.get_health() <= 0 and not isinstance(card, Player):
      card.change_parent(card.owner.graveyard)
      if card.effect and card.effect.trigger == Triggers.DEATHRATTLE:
        self.resolve_effect(card)
        
      for other_card in card.owner.board.get_all():
        if other_card.effect and (other_card.effect.trigger == Triggers.ANY_MINION_DIES or other_card.effect.trigger == Triggers.FRIENDLY_MINION_DIES):
          self.resolve_effect(other_card)
      for other_card in card.owner.other_player.board.get_all():
        if other_card.effect and (other_card.effect.trigger == Triggers.ANY_MINION_DIES or other_card.effect.trigger == Triggers.ENEMY_MINION_DIES):
          self.resolve_effect(other_card)
          
  def resolve_effect(self, card):
    targets = self.get_available_effect_targets(card)
    if len(targets) > 0:
      if card.effect.method == Methods.ALL:
        card.effect.resolve_action(self, Action(Actions.CAST_EFFECT, card, targets))
      elif card.effect.method == Methods.RANDOMLY:
        card.effect.resolve_action(self, Action(Actions.CAST_EFFECT, card, self.random_state.choice(targets, card.effect.random_count)))
      elif card.effect.method == Methods.TARGETED:
        card.effect.resolve_action(self, Action(Actions.CAST_EFFECT, card, [targets[0]]))
      elif card.effect.method == Methods.SELF:
        card.effect.resolve_action(self, Action(Actions.CAST_EFFECT, card, [card]))



  def get_available_targets(self, card):
    targets = []
    taunt_targets = list(filter(lambda target: target.has_attribute(Attributes.TAUNT), card.owner.other_player.board.get_all()))
    if len(taunt_targets) > 0:
      targets = taunt_targets
    else:
      targets = [card.owner.other_player]
      targets.extend(list(filter(lambda card: not card.has_attribute(Attributes.STEALTH), card.owner.other_player.board.get_all())))
    return targets

  def get_playable_spells_actions(self, player):
    playable_spell_actions = []
    for card in filter(lambda card: card.mana <= player.current_mana and card.card_type == CardTypes.SPELL, player.hand.get_all()):
      cast_targets = self.get_available_effect_targets(card)
      if card.effect and len(cast_targets) > 0:
        if card.effect.method == Methods.TARGETED:
          for target in filter(lambda target: not (target.has_attribute(Attributes.STEALTH) or target.has_attribute(Attributes.HEXPROOF)), cast_targets):
            playable_spell_actions.append(Action(Actions.CAST_SPELL, card, [target]))
        elif card.effect.method == Methods.RANDOMLY:
          playable_spell_actions.append(Action(Actions.CAST_SPELL, card, [self.random_state.choice(cast_targets)]))
        elif card.effect.method == Methods.ALL:
          playable_spell_actions.append(Action(Actions.CAST_SPELL, card, cast_targets))
    return playable_spell_actions

  def get_hero_power_actions(self, player):
    hero_power_actions = []
    if player.current_mana >= 2 and not player.used_hero_power:
      cast_targets = self.get_available_effect_targets(player.hero_power)
      if player.hero_power.effect.method == Methods.TARGETED:
        for target in filter(lambda target: not (target.has_attribute(Attributes.STEALTH) or target.has_attribute(Attributes.HEXPROOF)), cast_targets):
          hero_power_actions.append(Action(Actions.CAST_HERO_POWER, player.hero_power, [target]))
      elif player.hero_power.effect.method == Methods.RANDOMLY:
        hero_power_actions.append(Action(Actions.CAST_HERO_POWER, player.hero_power, self.random_state.choice(cast_targets, player.hero_power.effect.random_count)))
      elif player.hero_power.effect.method == Methods.ALL:
        hero_power_actions.append(Action(Actions.CAST_HERO_POWER, player.hero_power, cast_targets))

    return hero_power_actions
    

  def get_available_actions(self, player):
    available_actions = []

    available_actions.extend(self.get_minion_attack_actions(player))
    available_actions.extend(self.get_hero_attack_actions(player))
    available_actions.extend(self.get_playable_minion_actions(player))
    available_actions.extend(self.get_playable_spells_actions(player))
    available_actions.extend(self.get_playable_weapon_actions(player))
    available_actions.extend(self.get_hero_power_actions(player))
    available_actions.append(Action(Actions.END_TURN, player, [player.board]))
    return available_actions

  def deck_to_hand(self, player):
    new_card = player.deck.pop()
    new_card.set_parent(new_card.owner.hand)


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

  def get_available_effect_targets(self, card):
    available_targets = []
    player = card.owner
    owner_filter = card.effect.owner_filter
    type_filter = card.effect.type_filter
    target = card.effect.target
    
    if owner_filter == OwnerFilters.FRIENDLY or owner_filter == OwnerFilters.ALL:
      if target == Targets.MINION or target == Targets.MINION_OR_HERO:
        for minion in player.board.get_all():
          if type_filter == None or type_filter == CreatureTypes.ALL or type_filter == minion.creature_type:
            available_targets.append(minion) 
      if target == Targets.HERO or target == Targets.MINION_OR_HERO:
        available_targets.append(player)
      if target == Targets.WEAPON and player.weapon:
        available_targets.append(player.weapon)
    if owner_filter == OwnerFilters.ENEMY or owner_filter == OwnerFilters.ALL:
      if target == Targets.MINION or target == Targets.MINION_OR_HERO:
        for minion in player.other_player.board.get_all():
          if type_filter == None or type_filter == CreatureTypes.ALL or type_filter == minion.creature_type:
            available_targets.append(minion)
      if target == Targets.HERO or target == Targets.MINION_OR_HERO:
        available_targets.append(player.other_player)
      if target == Targets.WEAPON and player.other_player.weapon:
        available_targets.append(player.other_player.weapon)
    if card.effect.method != Methods.SELF and card in available_targets:
      available_targets.remove(card)

    return available_targets



  def get_minion_attack_actions(self, player):
    minion_attack_options = []
    for minion in player.board.get_all():
      if  (minion.attacks_this_turn == 0 \
          or (minion.attacks_this_turn == -1 and minion.has_attribute(Attributes.CHARGE))\
          or (minion.attacks_this_turn == 1 and minion.has_attribute(Attributes.WINDFURY)))\
          and minion.get_attack() > 0:
        for target in self.get_available_targets(minion):
          minion_attack_options.append(Action(Actions.ATTACK, minion, [target]))

    return minion_attack_options
  

  def get_hero_attack_actions(self, player):
    hero_attack_options = []
    if (player.get_attack() > 0
        or (player.weapon and player.weapon.attack > 0))\
        and (player.attacks_this_turn == 0\
        or (player.attacks_this_turn == 1 and player.has_attribute(Attributes.WINDFURY))):
      for target in self.get_available_targets(player):
        hero_attack_options.append(Action(Actions.ATTACK, player, [target]))
    return hero_attack_options


  def get_playable_minion_actions(self, player):
    playable_minion_actions = []

    if len(player.board.get_all()) < 7:
      for card in filter(lambda card: card.mana <= player.current_mana and card.card_type == CardTypes.MINION, player.hand.get_all()):
        if card.effect and card.effect.trigger == Triggers.BATTLECRY:
          battlecry_targets = self.get_available_effect_targets(card)
          if len(battlecry_targets) > 0:
            if card.effect.method == Methods.TARGETED:
              for target in filter(lambda target: not target.has_attribute(Attributes.STEALTH),  battlecry_targets):
                playable_minion_actions.append(Action(Actions.CAST_MINION, card, [target]))
            elif card.effect.method == Methods.RANDOMLY:
              playable_minion_actions.append(Action(Actions.CAST_MINION, card, self.random_state.choice(battlecry_targets, card.effect.random_count)))
            elif card.effect.method == Methods.ALL:
              playable_minion_actions.append(Action(Actions.CAST_MINION, card, battlecry_targets))
            elif card.effect.target == Targets.MINION and card.effect.method == Methods.ADJACENT:
              adjacent_minions = unique(list(filter(lambda target: target.parent.at_edge(target), battlecry_targets)))
              playable_minion_actions.append(Action(Actions.CAST_MINION, card, adjacent_minions))
            elif card.effect.target == Targets.SELF:
              playable_minion_actions.append(Action(Actions.CAST_MINION, card, [card]))
        else:
          playable_minion_actions.append(Action(Actions.CAST_MINION, card, [player.board]))
    return playable_minion_actions

  def get_playable_weapon_actions(self, player):
    playable_weapon_actions = []
    if not player.weapon:
      for card in filter(lambda card: card.mana <= player.current_mana and card.card_type == CardTypes.WEAPON, player.hand.get_all()):
        if card.effect and card.effect.trigger == Triggers.BATTLECRY:
          battlecry_targets = self.get_available_effect_targets(card)
          if len(battlecry_targets) > 0:
            if card.effect.method == Methods.TARGETED:
              for target in filter(lambda target: not target.has_attribute(Attributes.STEALTH), battlecry_targets):
                playable_weapon_actions.append(Action(Actions.CAST_WEAPON, card, [target]))
            elif card.effect.method == Methods.RANDOMLY:
              playable_weapon_actions.append(Action(Actions.CAST_WEAPON, card, self.random_state.choice(battlecry_targets, card.effect.random_count)))
            elif card.effect.method == Methods.ALL:
              playable_weapon_actions.append(Action(Actions.CAST_WEAPON, card, battlecry_targets))
        else:
          playable_weapon_actions.append(Action(Actions.CAST_WEAPON, card, [player]))
    return playable_weapon_actions

  def simulate_game(self):
    self.start_game()

    game_status = -1

    while game_status == -1:
      game_status = self.take_turn()
      
    return game_status