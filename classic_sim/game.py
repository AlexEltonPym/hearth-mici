from enums import *
from random import choice
from player import Player

class Game():
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy
        self.player.other_player = self.enemy
        self.enemy.other_player = self.player
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
            
    def cast_minion(self, action):
        action['source'].parent = self.current_player.board
        self.current_player.board.append(action['source'])
        self.current_player.hand.remove(action['source'])
        for effect in action['source'].card_details['effects']:
            if effect['trigger'] == Triggers.BATTLECRY:
                self.resolve_effect(effect, action)

    def resolve_effect(effect, action):
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
        taunt_targets = filter(lambda target: Attributes.TAUNT in target['attributes'], card.owner.other_player.board)
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
        
        for _ in range(8):
            self.current_player.take_turn()

        if(self.player.health <= 0):
            return 0
        elif(self.enemy.health <= 0):
            return 1
