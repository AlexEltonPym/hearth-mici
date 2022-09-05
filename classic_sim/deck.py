import copy

class Deck():
  def __init__(self, random_state):
    self.name = 'deck'
    self.__deck = []
    self.random_state = random_state

  def generate_random(self, available_cards):
    id = 0
    while len(self.__deck) < 30:
      rand_card = copy.deepcopy(self.random_state.choice(available_cards))
      rand_card.parent = self
      rand_card.id = id
      self.__deck.append(rand_card)
      id += 1
    return self
    
  def update_owner(self, owner):
    for card in self.__deck:
      card.owner = owner

  def remove(self, card):
    self.__deck.remove(card)

  def add(self, card):
    self.__deck.append(card)

  def get_all(self):
    return self.__deck

  def pop(self):
    return self.__deck.pop()

  def __str__(self):
    return str(self.__deck)

  def shuffle(self):
    self.random_state.shuffle(self.__deck)