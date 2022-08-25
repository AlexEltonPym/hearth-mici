import random
import copy

class Deck():
  def __init__(self):
    self.name = 'deck'
    self.deck = []

  def generate_random(self, available_cards):
    id = 0
    while len(self.deck) < 30:
      rand_card = copy.copy(random.choice(available_cards))
      rand_card.parent = self
      rand_card.id = id
      self.deck.append(rand_card)
      id += 1
    return self
    
  def update_owner(self, owner):
    for card in self.deck:
      card.owner = owner

  def remove(self, card):
    self.deck.remove(card)

  def add(self, card):
    self.deck.append(card)

  def get_all(self):
    return self.deck

  def pop(self):
    return self.deck.pop()

  def __str__(self):
    return str(self.deck)

  def shuffle(self):
    random.shuffle(self.deck)