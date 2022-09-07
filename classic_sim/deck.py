import copy

class Deck():
  def __init__(self, game_manager):
    self.name = 'deck'
    self.__deck = []
    self.game_manager = game_manager

  def generate_random(player):
    new_deck = Deck(player.game_manager)
    available_cards = player.game_manager.player_pool if player.name == "player" else player.game_manager.enemy_pool
    
    id = 0
    while len(new_deck.__deck) < 30:
      rand_card = copy.deepcopy(new_deck.game_manager.random_state.choice(available_cards))
      rand_card.parent = new_deck
      rand_card.id = id
      new_deck.add(rand_card)
      id += 1
    return new_deck
    
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
    self.game_manager.random_state.shuffle(self.__deck)