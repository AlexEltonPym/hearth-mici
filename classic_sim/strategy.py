from random import choice

class GreedyAction():
    def mulligan_rule(card):
        return card.card_details['mana'] < 3
    
    def choose_action(actions):
        return choice(actions)