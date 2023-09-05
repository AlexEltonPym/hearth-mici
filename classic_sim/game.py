from enums import *
from player import Player
from card_sets import get_utility_card, get_hero_power
from effects import *
import copy
from random import uniform
from action import Action
from statistics import mean

class TooManyActions(Exception):
  pass

class PlayerDead(Exception):
  pass

class Game():
  def __init__(self, game_manager):
    self.game_manager = game_manager
  
  def setup_players(self):
    self.player = copy.deepcopy(self.game_manager.player)
    self.enemy = copy.deepcopy(self.game_manager.enemy)

    self.player.game = self
    self.enemy.game = self

    self.player.other_player = self.enemy
    self.enemy.other_player = self.player

    self.player.hero_power = get_hero_power(self.player.player_class)
    self.player.hero_power.set_owner(self.player)
    self.player.hero_power.parent = self.player

    self.enemy.hero_power = get_hero_power(self.enemy.player_class)
    self.enemy.hero_power.set_owner(self.enemy)
    self.enemy.hero_power.parent = self.enemy

  def start_game(self):
    self.player.deck.shuffle()
    self.enemy.deck.shuffle()
    
    self.current_player = self.game_manager.random_state.choice([self.player, self.enemy])
    
    self.draw(self.current_player, 3)
    self.mulligan(self.current_player)

    self.draw(self.current_player.other_player, 4)
    self.mulligan(self.current_player.other_player)
    self.add_coin(self.current_player.other_player)

  def reset_game(self):
    for player in [self.player, self.enemy]:
      all_cards = player.secrets_zone.get_all() + player.graveyard.get_all() + player.board.get_all() + player.hand.get_all()
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
    self.current_player.max_mana = min(self.current_player.max_mana, 10)
    self.current_player.current_mana = self.current_player.max_mana
    self.draw(self.current_player, 1)
    self.current_player.attacks_this_turn = 0
    self.current_player.used_hero_power = False
    for minion in self.current_player.board:
      minion.attacks_this_turn = 0
    self.trigger(self.current_player, Triggers.FRIENDLY_UNTAP)
    self.trigger(self.current_player, Triggers.ENEMY_UNTAP)
    self.trigger(self.current_player, Triggers.ANY_UNTAP)



  def take_turn(self):
    try:
      self.untap()
    except PlayerDead:
      if self.player.health <= 0: #if we only check at turn end is faster?
        return 0
      elif self.enemy.health <= 0:
        return 1
    turn_passed = False
    action_count = 0

    while not turn_passed:
      try:
        action_count += 1
        turn_passed = self.current_player.strategy.choose_action(self)
      except PlayerDead:
        if self.player.health <= 0: #if we only check at turn end is faster?
          return 0
        elif self.enemy.health <= 0:
          return 1

      if self.player.health <= 0: #if we only check at turn end is faster?
        return 0
      elif self.enemy.health <= 0:
        return 1
      if turn_passed:
        try:
          self.end_turn()
        except PlayerDead:
          if self.player.health <= 0: #if we only check at turn end is faster?
            return 0
          elif self.enemy.health <= 0:
            return 1
      if action_count > 50:
        raise TooManyActions("Too many actions without passing")
    return -1

  def end_turn(self):
    self.trigger(self.current_player, Triggers.ANY_END_TURN)
    self.trigger(self.current_player, Triggers.FRIENDLY_END_TURN)
    self.trigger(self.current_player, Triggers.ENEMY_END_TURN)

    self.current_player.temp_attack = 0
    self.current_player.temp_health = 0
    self.current_player.temp_attributes = []
    self.current_player.remove_attribute(Attributes.FROZEN)
  
    self.current_player.other_player.temp_attack = 0
    self.current_player.other_player.temp_health = 0
    self.current_player.other_player.temp_attributes = []

    for minion in self.current_player.board.get_all():
      minion.temp_attack = 0
      minion.temp_health = 0
      minion.temp_attributes = []
      minion.remove_attribute(Attributes.FROZEN)
    
    for minion in self.current_player.other_player.board.get_all():
      minion.temp_attack = 0
      minion.temp_health = 0
      minion.temp_attributes = []
      
    self.current_player.minions_played_this_turn = 0

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
    elif action.action_type == Actions.CAST_SECRET:
      self.cast_secret(action)
    elif action.action_type == Actions.ATTACK:
      self.handle_attack(action)
    elif action.action_type == Actions.CAST_HERO_POWER:
      self.cast_hero_power(action)
    elif action.action_type == Actions.END_TURN:
      return True
    return False

  def cast_hero_power(self, action):
    self.current_player.used_hero_power = True
    self.current_player.current_mana -= action.source.get_manacost()
    action.source.effect.resolve_action(self, action)


  def cast_minion(self, action):
    self.current_player.current_mana -= action.source.get_manacost()
    
    initial_attack_less_than_four = action.source.get_attack() <= 3

    action.source.change_parent(action.source.owner.board)

    if action.source.effect and action.source.effect.trigger == Triggers.BATTLECRY and len(action.targets) > 0:
      action.source.effect.resolve_action(self, action)

    self.current_player.minions_played_this_turn += 1


    self.trigger(action.source, Triggers.ANY_MINION_SUMMONED)
    self.trigger(action.source, Triggers.ANY_SAME_TYPE_SUMMONED)
    self.trigger(action.source, Triggers.FRIENDLY_MINION_SUMMONED)
    self.trigger(action.source, Triggers.FRIENDLY_SAME_TYPE_SUMMONED)
    self.trigger(action.source, Triggers.ENEMY_MINION_SUMMONED)
    self.trigger(action.source, Triggers.ENEMY_SAME_TYPE_SUMMONED)
    self.trigger(action.source, Triggers.ANY_CARD_PLAYED)
    self.trigger(action.source, Triggers.FRIENDLY_CARD_PLAYED)
    self.trigger(action.source, Triggers.ENEMY_CARD_PLAYED)
    if initial_attack_less_than_four:
      self.trigger(action.source, Triggers.FRIENDLY_LESS_THAN_FOUR_ATTACK_SUMMONED)



  def cast_spell(self, action):
    spell_countered = False
    spell_targeted = action.source.effect.method == Methods.TARGETED
    spell_redirected = False
    spell_new_target = None
    for secret in action.source.owner.other_player.secrets_zone:
      if isinstance(secret.effect, Counterspell):
        spell_countered = True
      if spell_targeted and isinstance(secret.effect, RedirectToToken) and secret.effect.value[1](action) is not None:
        for token_number in range(secret.effect.value[0](action)):
          if len(secret.owner.board) >= secret.owner.board.max_entries:
            break
          spell_redirected = True
          spell_new_target = deepcopy(secret.effect.value[1](action))
          spell_new_target.collectable = False
          spell_new_target.set_owner(secret.owner)
          spell_new_target.set_parent(secret.owner.board) #Doesn't trigger battlecry

    self.current_player.current_mana -= action.source.get_manacost()
    action.source.change_parent(action.source.owner.graveyard)

    if spell_countered:
      self.trigger(action.source, Triggers.ENEMY_SPELL_COUNTERED)
    else:
      if spell_redirected:
        action.targets[0] = spell_new_target
        self.trigger(action.source, Triggers.ENEMY_SPELL_REDIRECTED)
      action.source.effect.resolve_action(self, action)

      self.trigger(action.source, Triggers.ANY_SPELL_CAST)
      self.trigger(action.source, Triggers.FRIENDLY_SPELL_CAST)
      self.trigger(action.source, Triggers.ENEMY_SPELL_CAST)
      self.trigger(action.source, Triggers.ANY_CARD_PLAYED)
      self.trigger(action.source, Triggers.FRIENDLY_CARD_PLAYED)
      self.trigger(action.source, Triggers.ENEMY_CARD_PLAYED)
      


  def cast_secret(self, action):
    spell_countered = False
    for secret in action.source.owner.other_player.secrets_zone:
      if isinstance(secret.effect, Counterspell):
        spell_countered = True
    
    self.current_player.current_mana -= action.source.get_manacost()
    self.current_player.remove_attribute(Attributes.FREE_SECRET)

    if spell_countered:
      self.trigger(action.source, Triggers.ENEMY_SPELL_COUNTERED)
      action.source.change_parent(action.source.owner.graveyard)
    else:
      action.source.change_parent(action.source.owner.secrets_zone)
      self.trigger(action.source, Triggers.ANY_SECRET_CAST)
      self.trigger(action.source, Triggers.FRIENDLY_SECRET_CAST)
      self.trigger(action.source, Triggers.ENEMY_SECRET_CAST)
      self.trigger(action.source, Triggers.ANY_SPELL_CAST)
      self.trigger(action.source, Triggers.FRIENDLY_SPELL_CAST)
      self.trigger(action.source, Triggers.ENEMY_SPELL_CAST)
      self.trigger(action.source, Triggers.ANY_CARD_PLAYED)
      self.trigger(action.source, Triggers.FRIENDLY_CARD_PLAYED)
      self.trigger(action.source, Triggers.ENEMY_CARD_PLAYED)

  def cast_effect(self, action):
    action.source.effect.resolve_action(self, action)

  def cast_weapon(self, action):
    self.current_player.current_mana -= action.source.get_manacost()
    action.source.change_parent(action.source.owner)
    if action.source.effect and action.source.effect.trigger == Triggers.BATTLECRY:
      action.source.effect.resolve_action(self, action)

    self.trigger(action.source, Triggers.ANY_WEAPON_PLAYED)
    self.trigger(action.source, Triggers.FRIENDLY_WEAPON_PLAYED)
    self.trigger(action.source, Triggers.ENEMY_WEAPON_PLAYED)
    self.trigger(action.source, Triggers.ANY_CARD_PLAYED)
    self.trigger(action.source, Triggers.FRIENDLY_CARD_PLAYED)
    self.trigger(action.source, Triggers.ENEMY_CARD_PLAYED)

  def handle_attack(self, action):
    if isinstance(action.targets[0], Player):
      for secret in action.targets[0].owner.secrets_zone:
        if isinstance(secret.effect, Redirect):
          player_board = self.player.board.get_all()
          enemy_board = self.player.other_player.board.get_all()
          player_themselves = [self.player]
          enemy_themselves = [self.player.other_player]
          possible_targets = player_board + enemy_board + player_themselves + enemy_themselves
          possible_targets.remove(action.targets[0])
          possible_targets.remove(action.source)
          if len(possible_targets) > 0:
            action.targets[0] = self.game_manager.random_state.choice(possible_targets)
            self.trigger(action.source, Triggers.REDIRECT_SECRET_REVEALED)

        if isinstance(secret.effect, Destroy) and not isinstance(action.source, Player):
          self.handle_death(action.source)
          self.trigger(action.source, Triggers.DESTROY_SECRET_REVEALED)
          return
      self.trigger(action.targets[0], Triggers.HERO_ATTACKED) #this triggers even if redirected to another target
    else:

      self.trigger(action.source, Triggers.ENEMY_ATTACKS_MINION)
    
    if isinstance(action.source, Player) and action.source.weapon:

      damage = action.source.get_attack()

      other_damage = 0 if action.source.weapon.has_attribute(Attributes.IMMUNE) else action.targets[0].get_attack()
      if action.source.weapon.has_attribute(Attributes.ATTACK_AS_DURABILITY) and not isinstance(action.targets[0], Player):
        action.source.weapon.attack -= 1
        action.source.weapon.attack = max(action.source.weapon.attack, 0)
      else:
        action.source.weapon.health -= 1
      self.check_dead(action.source.weapon)
    elif isinstance(action.source, Player) and not action.source.weapon:
      damage = action.source.get_attack()
      other_damage = action.targets[0].get_attack()
    elif not isinstance(action.source, Player):
      damage = action.source.get_attack()
      other_damage = action.targets[0].get_attack()
      self.trigger(action.source, Triggers.ENEMY_MINION_ATTACKS)

    if isinstance(action.targets[0], Player):
      other_damage = 0
    
    self.deal_damage(action.targets[0], damage, poisonous=action.source.has_attribute(Attributes.POISONOUS), freezer=action.source.has_attribute(Attributes.FREEZER))
    self.deal_damage(action.source, other_damage, poisonous=action.targets[0].has_attribute(Attributes.POISONOUS), freezer=action.targets[0].has_attribute(Attributes.FREEZER))
    if action.source.attacks_this_turn == -1: #used charge to attack
      action.source.attacks_this_turn += 2
    else:
      action.source.attacks_this_turn += 1

    action.source.remove_attribute(Attributes.STEALTH)


  def deal_damage(self, target, amount, poisonous=False, freezer=False, fatigue=False):
    if target.has_attribute(Attributes.IMMUNE) and not fatigue:
      return
    elif target.has_attribute(Attributes.DIVINE_SHIELD) and amount > 0:
      target.remove_attribute(Attributes.DIVINE_SHIELD)
    elif amount > 0:
      if isinstance(target, Player):

        new_health = target.health
        new_armor = target.armor
        if new_armor > 0:
          new_armor -= amount
          if new_armor < 0:
            new_health += new_armor #armor is negative here
            new_armor = 0
        else:
          new_health -= amount #no armor to worry about
        if new_health <= 0:
          self.trigger(target, Triggers.LETHAL_DAMAGE)
        if target.has_attribute(Attributes.IMMUNE) and not fatigue:
          return
        else:

          target.health = new_health
          target.armor = new_armor
          if target.health <= 0:
            raise PlayerDead
      else:
        previous_health = target.health
          
        target.health -= amount #minions dont have armor
        if target.owner.has_attribute(Attributes.MINIONS_UNKILLABLE):
          target.health = max(target.health, 1)
        if target.health < previous_health:
          self.trigger(target, Triggers.FRIENDLY_MINION_DAMAGED)
          self.trigger(target, Triggers.ENEMY_MINION_DAMAGED)
          self.trigger(target, Triggers.ANY_MINION_DAMAGED)

      if freezer and not target.has_attribute(Attributes.FROZEN):
        target.perm_attributes.append(Attributes.FROZEN)
      self.trigger(target, Triggers.SELF_DAMAGE_TAKEN)
      self.check_dead(target, poisonous=poisonous)

  def check_dead(self, card, poisonous=False):
    if (poisonous or card.get_health() <= 0) and not isinstance(card, Player):
      self.handle_death(card)
      
  def handle_death(self, card):
    card.change_parent(card.owner.graveyard)
    if card.effect and card.effect.trigger == Triggers.DEATHRATTLE:
      self.resolve_effect(card)
    
    self.trigger(card, Triggers.ANY_MINION_DIES)
    self.trigger(card, Triggers.FRIENDLY_MINION_DIES)
    self.trigger(card, Triggers.ENEMY_MINION_DIES)
    self.trigger(card, Triggers.FRIENDLY_SAME_TYPE_DIES)

          
  def resolve_effect(self, card, triggerer=None):
    # print(f"{triggerer=}")
    if card.card_type == CardTypes.SECRET and card.owner.game.current_player == card.owner:
      return
    targets = self.get_available_effect_targets(card)
    if len(targets) > 0 or card.effect.method == Methods.ALL:
      if card.effect.method == Methods.ALL:

        card.effect.resolve_action(self, Action(Actions.CAST_EFFECT, card, targets))
      elif card.effect.method == Methods.RANDOMLY:
        card.effect.resolve_action(self, Action(Actions.CAST_EFFECT, card, self.game_manager.random_state.choice(targets, card.effect.random_count if card.effect.random_replace else min(len(cast_targets), card.effect.random_count), card.effect.random_replace)))
      elif card.effect.method == Methods.TARGETED:
        card.effect.resolve_action(self, Action(Actions.CAST_EFFECT, card, [targets[0]]))
      elif card.effect.method == Methods.SELF:
        card.effect.resolve_action(self, Action(Actions.CAST_EFFECT, card, [card]))
      elif card.effect.method == Methods.TRIGGERER and triggerer != None:
        if isinstance(triggerer, Player) and not Targets.HERO in card.effect.available_targets or\
          not isinstance(triggerer, Player) and triggerer.card_type == CardTypes.SPELL and not (Targets.SPELL in card.effect.available_targets or Targets.MINION_OR_SPELL in card.effect.available_targets):
          return
        
        card.effect.resolve_action(self, Action(Actions.CAST_EFFECT, card, [triggerer]))

    if card.card_type == CardTypes.SECRET:
      card.change_parent(card.owner.graveyard)
      self.trigger(card, Triggers.ANY_SECRET_REVEALED)


  def trigger(self, triggerer, trigger_type):
    # print(f"{trigger_type=}")
    # print(f"{triggerer=}")
    for player in [self.player, self.enemy]:
      player_weapon = [player.weapon] if player.weapon else []
      for card in player_weapon + player.board.get_all() + player.secrets_zone.get_all():
        if card.effect and trigger_type == card.effect.trigger and triggerer != card:
          if "FRIENDLY" in trigger_type.name and triggerer.owner == card.owner:
            if trigger_type == Triggers.FRIENDLY_MINION_DIES:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.FRIENDLY_HEALED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.FRIENDLY_MINION_SUMMONED:
              self.resolve_effect(card, triggerer)
            elif (trigger_type == Triggers.FRIENDLY_SAME_TYPE_SUMMONED\
                or trigger_type == Triggers.FRIENDLY_SAME_TYPE_DIES)\
               and triggerer.creature_type and card.creature_type\
               and (triggerer.creature_type == CreatureTypes.ALL\
               or card.creature_type == CreatureTypes.ALL\
               or triggerer.creature_type == card.creature_type):
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.FRIENDLY_END_TURN:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.FRIENDLY_SPELL_CAST:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.FRIENDLY_SECRET_CAST:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.FRIENDLY_UNTAP:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.FRIENDLY_WEAPON_PLAYED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.FRIENDLY_CARD_PLAYED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.FRIENDLY_LESS_THAN_FOUR_ATTACK_SUMMONED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.FRIENDLY_MINION_DAMAGED:
              self.resolve_effect(card, triggerer)


          elif "ENEMY" in trigger_type.name and triggerer.owner != card.owner:
            if trigger_type == Triggers.ENEMY_MINION_DIES:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_HEALED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_MINION_SUMMONED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_SAME_TYPE_SUMMONED\
               and triggerer.creature_type and card.creature_type\
               and (triggerer.creature_type == CreatureTypes.ALL\
               or card.creature_type == CreatureTypes.ALL\
               or triggerer.creature_type == card.creature_type):
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_END_TURN:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_SPELL_CAST:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_SECRET_CAST:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_UNTAP:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_WEAPON_PLAYED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_CARD_PLAYED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_MINION_ATTACKS:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_ATTACKS_MINION:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_SPELL_COUNTERED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_SPELL_REDIRECTED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ENEMY_MINION_DAMAGED:
              self.resolve_effect(card, triggerer)
          else:
            if trigger_type == Triggers.ANY_MINION_DIES:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ANY_HEALED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ANY_MINION_SUMMONED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ANY_SAME_TYPE_SUMMONED\
                and triggerer.creature_type and card.creature_type\
                and (triggerer.creature_type == CreatureTypes.ALL\
                or card.creature_type == CreatureTypes.ALL\
                or triggerer.creature_type == card.creature_type):
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ANY_SECRET_CAST:
              self.resolve_effect(card,triggerer)
            elif trigger_type == Triggers.ANY_END_TURN:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ANY_SPELL_CAST:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ANY_UNTAP:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ANY_WEAPON_PLAYED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ANY_CARD_PLAYED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ANY_SECRET_REVEALED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.HERO_ATTACKED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.LETHAL_DAMAGE:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.DESTROY_SECRET_REVEALED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.REDIRECT_SECRET_REVEALED:
              self.resolve_effect(card, triggerer)
            elif trigger_type == Triggers.ANY_MINION_DAMAGED:
              self.resolve_effect(card, triggerer)

        elif card.effect and trigger_type == card.effect.trigger and triggerer == card:
          if trigger_type == Triggers.SELF_DAMAGE_TAKEN:
            self.resolve_effect(card, triggerer)
          if triggerer.owner == card.owner and trigger_type == Triggers.FRIENDLY_MINION_DAMAGED:
            self.resolve_effect(card, triggerer)
          if triggerer.owner != card.owner and trigger_type == Triggers.ANY_MINION_DAMAGED:
            self.resolve_effect(card, triggerer)
          if trigger_type == Triggers.ANY_MINION_DAMAGED:
            self.resolve_effect(card, triggerer)


  def get_available_targets(self, card):
    targets = []
    taunt_targets = list(filter(lambda target: target.has_attribute(Attributes.TAUNT), card.owner.other_player.board))
    if len(taunt_targets) > 0:
      targets = taunt_targets
    else:
      targets = [card.owner.other_player]
      targets.extend(list(filter(lambda card: not card.has_attribute(Attributes.STEALTH), card.owner.other_player.board)))
    return targets

  def get_playable_spells_actions(self, player):
    playable_spell_actions = []
    
    for card in filter(lambda card: card.get_manacost() <= player.current_mana and card.card_type == CardTypes.SPELL, player.hand):
      cast_targets = self.get_available_effect_targets(card)
      if card.effect and (len(cast_targets) > 0 or card.effect.method==Methods.ALL):
        if card.effect.method == Methods.TARGETED:
          for target in filter(lambda target: not (target.has_attribute(Attributes.STEALTH) or target.has_attribute(Attributes.HEXPROOF)), cast_targets):
            playable_spell_actions.append(Action(Actions.CAST_SPELL, card, [target]))
        elif card.effect.method == Methods.RANDOMLY:
          playable_spell_actions.append(Action(Actions.CAST_SPELL, card, self.game_manager.random_state.choice(cast_targets, card.effect.random_count if card.effect.random_replace else min(len(cast_targets), card.effect.random_count), card.effect.random_replace)))
        elif card.effect.method == Methods.ALL:
          playable_spell_actions.append(Action(Actions.CAST_SPELL, card, cast_targets))
    return playable_spell_actions

  def get_playable_secret_actions(self, player):
    playable_secret_actions = []
    if len(player.secrets_zone) < player.secrets_zone.max_entries:
      for card in filter(lambda card: card.get_manacost() <= player.current_mana and card.card_type == CardTypes.SECRET and card.name not in player.secrets_zone.names(), player.hand):
        playable_secret_actions.append(Action(Actions.CAST_SECRET, card, [player.secrets_zone]))
    return playable_secret_actions

  def get_hero_power_actions(self, player):
    hero_power_actions = []
    if player.current_mana >= 2 and not player.used_hero_power:
      cast_targets = self.get_available_effect_targets(player.hero_power)
      if player.hero_power.effect.method == Methods.TARGETED:
        for target in filter(lambda target: not (target.has_attribute(Attributes.STEALTH) or target.has_attribute(Attributes.HEXPROOF)), cast_targets):
          hero_power_actions.append(Action(Actions.CAST_HERO_POWER, player.hero_power, [target]))
      elif player.hero_power.effect.method == Methods.RANDOMLY:
        hero_power_actions.append(Action(Actions.CAST_HERO_POWER, player.hero_power, self.game_manager.random_state.choice(cast_targets, player.hero_power.effect.random_count if player.hero_power.effect.random_replace else min(len(cast_targets), player.hero_power.effect.random_count), player.hero_power.effect.random_replace)))
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
    available_actions.extend(self.get_playable_secret_actions(player))
    available_actions.extend(self.get_hero_power_actions(player))
    available_actions.append(Action(Actions.END_TURN, player, [player]))
    return available_actions

  def deck_to_hand(self, player):
    new_card = player.deck.pop()
    new_card.set_parent(new_card.owner.hand)


  def deck_to_graveyard(self, player):
    new_card = player.deck.pop()
    new_card.set_parent(new_card.owner.graveyard)


  def draw(self, player, num_to_draw):
    for i in range(num_to_draw):
      if(len(player.deck) > 0):
        if(len(player.hand) < player.hand.max_entries):
          self.deck_to_hand(player)
        else:
          self.deck_to_graveyard(player)
      else:
        self.deal_damage(player, player.fatigue_damage, fatigue=True)
        
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
    if card.effect.zone_filter == Zones.BOARD:
      player_weapon = [player.weapon] if player.weapon else []
      enemy_weapon = [player.other_player.weapon] if player.other_player.weapon else []
      player_board = player.board.get_all()
      enemy_board = player.other_player.board.get_all()
      player_themselves = [player]
      enemy_themselves = [player.other_player]
      possible_targets = player_weapon + enemy_weapon + player_board + enemy_board + player_themselves + enemy_themselves
    elif card.effect.zone_filter == Zones.HAND:
      possible_targets = player.hand.get_all() + player.other_player.hand.get_all()

    elif card.effect.zone_filter == Zones.DECK:

      possible_targets = player.deck.get_all() + player.other_player.deck.get_all()
      # [print(possible_target) for possible_target in possible_targets]
      # print('g[etting effect')
      # [print(card) for card in player.deck.get_all()]]
    # [print(possible_target) for possible_target in possible_targets]
   
    for possible_target in possible_targets:
      # print(f"{possible_target=}")
      # print(possible_target.matches_card_requirements(card))
      # print(possible_target.owner)
      # print(card.owner)
      if possible_target.matches_card_requirements(card):
        available_targets.append(possible_target)
    
    if card.effect.method != Methods.SELF and card in available_targets:
      available_targets.remove(card)
    
    if card.effect.method == Methods.SELF:
      available_targets.append(card)
    
    return available_targets



  def get_minion_attack_actions(self, player):
    minion_attack_options = []
    for minion in player.board:
      if (minion.attacks_this_turn == 0 \
          or (minion.attacks_this_turn == -1 and minion.has_attribute(Attributes.CHARGE))\
          or (minion.attacks_this_turn == 1 and minion.has_attribute(Attributes.WINDFURY)))\
          and minion.get_attack() > 0 and not (minion.has_attribute(Attributes.FROZEN) or minion.has_attribute(Attributes.DEFENDER)):
        for target in self.get_available_targets(minion):
          minion_attack_options.append(Action(Actions.ATTACK, minion, [target]))

    return minion_attack_options
  

  def get_hero_attack_actions(self, player):
    hero_attack_options = []
    if (not (player.has_attribute(Attributes.FROZEN) or player.has_attribute(Attributes.DEFENDER))\
        and (player.get_attack() > 0 or player.weapon and player.weapon.attack > 0)\
        and (player.attacks_this_turn == 0 or (player.attacks_this_turn == 1 and (player.has_attribute(Attributes.WINDFURY) or (player.weapon and player.weapon.has_attribute(Attributes.WINDFURY)))))):
      for target in self.get_available_targets(player):
        hero_attack_options.append(Action(Actions.ATTACK, player, [target]))
    return hero_attack_options


  def get_playable_minion_actions(self, player):
    playable_minion_actions = []
    if len(player.board) < player.board.max_entries:
      for card in filter(lambda card: card.get_manacost() <= player.current_mana and card.card_type == CardTypes.MINION, player.hand):
        if card.effect and card.effect.trigger == Triggers.BATTLECRY:
          battlecry_targets = self.get_available_effect_targets(card)
          if len(battlecry_targets) > 0 or card.effect.method == Methods.ALL:
            if card.effect.method == Methods.TARGETED:
              for target in filter(lambda target: not target.has_attribute(Attributes.STEALTH),  battlecry_targets):
                playable_minion_actions.append(Action(Actions.CAST_MINION, card, [target]))
            elif card.effect.method == Methods.RANDOMLY:
              playable_minion_actions.append(Action(Actions.CAST_MINION, card, self.game_manager.random_state.choice(battlecry_targets, card.effect.random_count if card.effect.random_replace else min(len(cast_targets), card.effect.random_count), card.effect.random_replace)))
            elif card.effect.method == Methods.ALL:
              playable_minion_actions.append(Action(Actions.CAST_MINION, card, battlecry_targets))
            elif card.effect.target == Targets.MINION and card.effect.method == Methods.ADJACENT:
              adjacent_minions = list(set(filter(lambda target: target.parent.at_edge(target), battlecry_targets)))
              playable_minion_actions.append(Action(Actions.CAST_MINION, card, adjacent_minions))
            elif card.effect.method == Methods.SELF:
              playable_minion_actions.append(Action(Actions.CAST_MINION, card, [card]))
          else:
            playable_minion_actions.append(Action(Actions.CAST_MINION, card, [])) #if no battlecry targets you can play without picking a target
        else:
          playable_minion_actions.append(Action(Actions.CAST_MINION, card, [])) #normal minion
    return playable_minion_actions

  def get_playable_weapon_actions(self, player):
    playable_weapon_actions = []
    if not player.weapon:
      for card in filter(lambda card: card.get_manacost() <= player.current_mana and card.card_type == CardTypes.WEAPON, player.hand):
        if card.effect and card.effect.trigger == Triggers.BATTLECRY:
          battlecry_targets = self.get_available_effect_targets(card)
          if len(battlecry_targets) > 0 or card.effect.method == Methods.ALL:
            if card.effect.method == Methods.TARGETED:
              for target in filter(lambda target: not target.has_attribute(Attributes.STEALTH), battlecry_targets):
                playable_weapon_actions.append(Action(Actions.CAST_WEAPON, card, [target]))
            elif card.effect.method == Methods.RANDOMLY:
              playable_weapon_actions.append(Action(Actions.CAST_WEAPON, card, self.game_manager.random_state.choice(battlecry_targets, card.effect.random_count if card.effect.random_replace else min(len(cast_targets), card.effect.random_count), card.effect.random_replace)))
            elif card.effect.method == Methods.ALL:
              playable_weapon_actions.append(Action(Actions.CAST_WEAPON, card, battlecry_targets))
          else:
            playable_weapon_actions.append(Action(Actions.CAST_WEAPON, card, []))
        else:
          playable_weapon_actions.append(Action(Actions.CAST_WEAPON, card, []))
    return playable_weapon_actions

  def play_game(self):
    game_status = -1
    turn = 0
    player_cards_in_hand = []
    enemy_cards_in_hand = []
    while game_status == -1:
      turn+=1
      game_status = self.take_turn()
      player_cards_in_hand.append(len(self.player.hand))
      enemy_cards_in_hand.append(len(self.enemy.hand))

    return (game_status, self.player.health-self.enemy.health, mean(player_cards_in_hand), turn, self.enemy.health-self.player.health, mean(enemy_cards_in_hand))