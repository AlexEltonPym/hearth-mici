import random

class Deck():
    def __init__(self):
        self.deck = []

    def generate_random(self, available_cards):
        while len(self.deck) < 30:
            rand_card = random.choice(available_cards)
            rand_card.parent = self
            self.deck.append(rand_card)
            self.deck.append(rand_card)
        return self
        
    def __str__(self):
        return str(self.deck)

    def shuffle(self):
        random.shuffle(self.deck)