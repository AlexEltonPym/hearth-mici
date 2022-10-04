from copy import deepcopy

class ZoneIterator():
  def __init__(self, zone):
    self.zone = zone.zone
    self.index = 0
  
  def __next__(self):
    try:
      result = self.zone[self.index]
    except IndexError:
      raise StopIteration
    self.index += 1
    return result

class Zone(object):
  def __init__(self, name, max_entries, parent):
    self.name = name
    self.max_entries = max_entries
    self.parent = parent
    self.zone = []

  def remove(self, card):
    self.zone.remove(card)

  def add(self, card):
    # if len(self.zone) == self.max_entries:
    #   raise Exception(f"Tried to add more than {self.max_entries} cards to {self.name}")
    self.zone.append(card)

  def pop(self):
    return self.zone.pop()

  def get_all(self):
    return self.zone

  def clear(self):
    self.zone.clear()

  def index_of(self, key):
    return self.zone.index(key)
  
  def at_edge(self, key):
    key_index = self.zone.index(key)
    return key_index == 0 or key_index == len(self.zone)-1

  def get_adjacent(self, key):
    if self.name != 'board': #adjacency only for board
      return []
    key_index = self.zone.index(key)
    adjacent_set = set()
    adjacent_set.add(self.zone[key_index-1])
    adjacent_set.add(self.zone[(key_index+1)%len(self.zone)])
    if self.zone[key_index] in adjacent_set: adjacent_set.remove(self.zone[key_index])
    return list(adjacent_set)
    

  def __len__(self):
    return len(self.zone)

  def __contains__(self, key):
    return key in self.zone
  
  def __iter__(self):
    return ZoneIterator(self)

  def __str__(self):
    return str((self.name, self.parent.name))

  def __repr__(self):
    return str((self.name, self.parent.name))

class SecretsZone(Zone):
  def __init__(self, parent):
    super().__init__('secrets', 5, parent)

class Board(Zone):
  def __init__(self, parent):
    super().__init__('board', 7, parent)

class Hand(Zone):
  def __init__(self, parent):
    super().__init__('hand', 10, parent)

class Graveyard(Zone):
  def __init__(self, parent):
    super().__init__('graveyard', 100, parent)

class Deck(Zone):
  def __init__(self, parent):
    super().__init__('deck', 30, parent)

  def generate_random(player):
    new_deck = Deck(player)
    available_cards = player.game_manager.get_player_pool() if player.name == "player" else player.game_manager.get_enemy_pool()
    
    id = 0
    while len(new_deck) < 30:
      rand_card = deepcopy(player.game_manager.random_state.choice(available_cards))
      rand_card.parent = new_deck
      rand_card.id = id
      new_deck.add(rand_card)
      id += 1
    return new_deck
    
  def update_owner(self, owner):
    for card in self:
      card.owner = owner

  def shuffle(self):
    self.parent.game_manager.random_state.shuffle(self.zone)