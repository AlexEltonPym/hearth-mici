from enums import *
from random import choice
from player import Player

class Game():
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy
        self.player.other_player = self.enemy
        self.player.name = 'player'
        self.enemy.other_player = self.player
        self.enemy.name = 'enemy'
        self.player.game = self
        self.enemy.game = self
        self.current_player = None

        for card in self.player.deck.deck:
            card.owner = self.player
        for card in self.enemy.deck.deck:
            card.owner = self.enemy

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
            self.current_player = self.current_player.other_player
            return True
        return False

    def cast_hero_power(self, action):
        self.current_player.used_hero_power = True
        for effect in action['source'].card_details['effects']:
            self.resolve_effect(effect, action)


    def cast_minion(self, action):
        self.current_player.current_mana -= action['source'].card_details['mana']
        action['source'].parent = self.current_player.board
        self.current_player.board.append(action['source'])
        self.current_player.hand.remove(action['source'])
        for effect in action['source'].card_details['effects']:
            if effect['trigger'] == Triggers.BATTLECRY:
                self.resolve_effect(effect, action)

    def cast_spell(self, action):
        self.current_player.current_mana -= action['source'].card_details['mana']
        self.current_player.hand.remove(action['source'])
        action['source'].parent = self.current_player.graveyard
        for effect in action['source'].card_details['effects']:
            self.resolve_effect(effect, action)

    def handle_attack(self, action):
        action['target'].card_details['health'] -= action['source'].card_details['attack']
        action['source'].has_attacked = True


    def resolve_effect(self, effect, action):
        if effect['effect_type'] == 'deal_damage':
            if type(action['target']) == Player:
                action['target'].health -= effect['amount']
            else:
                action['target'].card_details['health'] -= effect['amount']
                if action['target'].card_details['health'] <= 0:
                    action['target'].parent.remove(action['target'])
                    action['target'].owner.graveyard.append(action['target'])

    def get_available_targets(self, card):
        targets = []
        taunt_targets = list(filter(lambda target: Attributes.TAUNT in target.card_details['attributes'], card.owner.other_player.board))
        if len(taunt_targets) > 0:
            targets = taunt_targets
        else:
            targets = card.other_player + card.other_player.board
        return targets

    def initalise_game(self):
        self.current_player = choice([self.player, self.enemy])

        self.player.deck.shuffle()
        self.enemy.deck.shuffle()

        self.current_player.draw(4)
        self.current_player.mulligan()
        self.current_player.other_player.draw(3)
        self.current_player.other_player.mulligan()
        self.current_player.other_player.add_coin()
        

    def simulate_game(self):
        
        self.initalise_game()
        
        for _ in range(8000):
            self.current_player.take_turn()

        if(self.player.health <= 0):
            return 0
        elif(self.enemy.health <= 0):
            return 1
