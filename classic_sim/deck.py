import random
import copy

class Deck():
  def __init__(self):
    self.name = 'deck'
    self.deck = []
    self.owner = None
    self.parent = None

  def generate_random(self, available_cards):
    while len(self.deck) < 30:
      rand_card = copy.copy(random.choice(available_cards))
      rand_card.parent = self
      self.deck.append(rand_card)
      self.deck.append(rand_card)
    return self
    
  def update_owner(self, owner):
    self.owner = owner
    self.parent = owner

  def remove(self, card):
    self.deck.remove(card)

  def add(self, card):
    self.deck.append(card)

  def get_all(self):
    return self.deck

  def pop(self, card):
    return self.deck.pop(card)

  def __str__(self):
    return str(self.deck)

  def shuffle(self):
    random.shuffle(self.deck)