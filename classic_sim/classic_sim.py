import random
from enum import Enum


class Attributes(Enum):
  TAUNT = 0
  LIFESTEAL = 1

class Triggers(Enum):
  BATTLECRY = 0
  DEATHRATTLE = 1

class Actions(Enum):
  ATTACK = 0
  CAST_MINION = 1
  CAST_HERO_POWER = 2
  CAST_SPELL = 3

class Targets(Enum):
  MINIONS = 0
  HEROES = 1
  MINIONS_OR_HEROES = 2
  PIRATES = 3
  BEASTS = 4
  ELEMENTALS = 5
  TOTEMS = 6
  WEAPONS = 7

class Filters(Enum):
  FRIENDLY = 0 
  ENEMY = 1
  ALL = 2

class Durations(Enum):
  TURN = 0 
  PERMANENTLY = 1

class Methods(Enum):
  TARGETED = 0
  RANDOMLY = 1
  ALL = 2
  NONE = 3

def perform_action(action):
  if action['action_type'] == Actions.CAST_MINION:
    action['source'].parent = current_player.board
    current_player.board.append(action['source'])
    current_player.hand.remove(action['source'])
    for effect in action['source'].card_details['effects']:
      if effect['trigger'] == Triggers.BATTLECRY:
        resolve_effect(effect, action['target'])
  
def resolve_effect(effect, target):
  if effect['effect_type'] == 'deal_damage':
    if type(target) == Player:
      target.health -= effect['amount']
    else:
      target.card_details['health'] -= effect['amount']
      if target.card_details['health'] <= 0:
        target.parent.remove(target)
        target.owner.graveyard.append(target)



def create_classic_cards():
  hunter_hero_power = Card(-1, 'Hunter hero power', {'mana': 2, 'effects':[{'effect_type': 'deal_damage', 'filter': 'enemy hero'}]})
  elven_archer = Card(0, 'Elven archer', {'card_type': 'minion', 'mana': 1, 'attack':1, 'health':1, 'effects':[{'effect_type': 'deal_damage', 'amount': 1, 'method': Methods.TARGETED,'targets': Targets.MINIONS_OR_HEROES, 'filter': Filters.ALL, 'trigger': Triggers.BATTLECRY}]})
  basic_minion = Card(1, 'Basic minion', {'card_type': 'minion', 'minion_type': Targets.ELEMENTALS, 'mana': 4, 'attack':5, 'health':5, 'effects':[]})
  taunt_minion = Card(2, 'Taunt minion', {'card_type': 'minion', 'mana': 4, 'attack':5, 'health':5, 'effects':[], 'attributes': [Attributes.TAUNT]})
  the_coin = Card(3, 'The coin', {'card_type': 'spell', 'mana': 0, 'effects': [{'effect_type': 'gain_mana', 'method': Methods.NONE, 'duration': Durations.TURN, 'trigger': Triggers.BATTLECRY}]} )


  hunter_cards = [elven_archer, basic_minion, taunt_minion]
  mage_cards = []
  warrior_cards = []
  hero_powers = {'hunter': hunter_hero_power}
  utility_cards = {'coin': the_coin}

  return hero_powers, hunter_cards, mage_cards, warrior_cards, utility_cards


def simulate_game(player, enemy):

  global current_player

  player.deck.shuffle()
  enemy.deck.shuffle()



  current_player.draw(4)
  current_player.mulligan()
  current_player.other_player.draw(3)
  current_player.other_player.mulligan()
  current_player.other_player.add_coin()
 
  for i in range(8):
    current_player.take_turn()

  if(player.health <= 0):
    return 0
  elif(enemy.health <= 0):
    return 1

class Deck():
  def __init__(self, starting_deck):
    self.deck = starting_deck

  def generate_random(self, owner, other_player):
    while len(self.deck) < 30:
      rand_card = random.choice(hunter_cards)
      rand_card.owner = owner
      rand_card.other_player = other_player
      rand_card.parent = self
      self.deck.append(rand_card)
      self.deck.append(rand_card)

  def __str__(self):
    return str(self.deck)

  def shuffle(self):
    random.shuffle(self.deck)

class Card():
  def __init__(self, id, name, card_details):
    self.id = id
    self.name = name
    self.card_details = card_details
    self.available_targets = []
    self.owner = None
    self.other_player = None
    self.has_attacked = True
    self.parent = None

  def get_available_targets(self):
    targets = []
    taunt_targets = filter(lambda target: Attributes.TAUNT in target['attributes'], self.other_player.board)
    if len(taunt_targets) > 0:
      targets = taunt_targets
    else:
      targets = self.other_player.board + self.other_player
    return targets

  def __str__(self):
    return str((self.name, self.card_details['attack'], self.card_details['health']))

  def __repr__(self):
    return str((self.name, self.card_details['attack'], self.card_details['health']))

class Player():
  def __init__(self, player_class, name):
    self.player_class = player_class
    self.hero_power = hero_powers[player_class]
    self.current_mana = 10
    self.health = 30
    self.weapon = None
    self.attack = 0
    self.armor = 0
    self.has_attacked = False
    self.deck = Deck([])
    self.hand = []
    self.board = []
    self.graveyard = []
    self.other_player = None
    self.name = name

  def add_coin(self):
    coin = utility_cards['coin']
    coin.parent = self.hand
    self.hand.append(coin)

  def generate_random_deck(self):
    self.deck.generate_random(self, self.other_player)
  
  def draw(self, num_to_draw):
    for i in range(num_to_draw):
      new_card = self.deck.deck.pop()
      new_card.parent = self.hand
      self.hand.append(new_card)
  
  def mulligan(self):
    new_hand = []
    for card in self.hand:
      if card.card_details['mana'] > 3:
        new_card = self.deck.deck.pop()
        new_card.parent = self.hand
        new_hand.append(new_card)
        card.parent = self.deck.deck
        self.deck.deck.append(card)
      else:
        card.parent = self.hand
        new_hand.append(card)
    self.hand = new_hand
    self.deck.shuffle()

  def take_turn(self):
    global current_player
    self.current_mana = 10
    if(len(self.hand) < 10):
      self.draw(1)
    available_actions = self.get_available_actions()
    state = perform_action(random.choice(available_actions))
    current_player = current_player.other_player



  def get_available_battlecry_targets(self, card):

    available_targets = []
    for effect in card.card_details['effects']:
      filters = effect['filter']
      targets = effect['targets']
      if filters == Filters.FRIENDLY or filters == Filters.ALL:
        for card in self.board:
          if targets == Targets.MINIONS or targets == Targets.MINIONS_OR_HEROES or card.card_details['minion_type'] == targets:
            available_targets.append(card)
        if targets == Targets.HEROES or targets == Targets.MINIONS_OR_HEROES:
          available_targets.append(self)
      if filters == Filters.ENEMY or filters == Filters.ALL:
        for card in self.other_player.board:
          if targets == Targets.MINIONS or targets == Targets.MINIONS_OR_HEROES or card.card_details['minion_type'] == targets:
            available_targets.append(card)
        if targets == Targets.HEROES or targets == Targets.MINIONS_OR_HEROES:
          available_targets.append(self.other_player)
    return available_targets

  def get_available_actions(self):
    available_actions = []
    for minion in self.board:
      if not minion.has_attacked:
        for target in minion.get_available_targets():
          available_actions.append({'action_type': Actions.ATTACK, 'source': minion, 'target': target})

    if self.attack > 0 and not self.has_attacked:
      for target in minion.get_available_targets():
        available_actions.append({'action_type': Actions.ATTACK, 'source': self, 'target': target})

    if len(self.board) < 7:
      for card in filter(lambda card: card.card_details['mana'] <= self.current_mana, self.hand):
        has_battlecry = False
        for effect in card.card_details['effects']:
          if Triggers.BATTLECRY == effect['trigger']:
            has_battlecry = True
            if Methods.TARGETED == effect['method']:
              for target in self.get_available_battlecry_targets(card):
                available_actions.append({'action_type': Actions.CAST_MINION if card.card_details['card_type'] == 'minion' else Actions.CAST_SPELL, 'source': card, 'target': target})
            elif Methods.RANDOMLY == effect['method']:
              available_actions.append(random.choice(self.get_available_battlecry_targets(card)))
            else:
              available_actions.append({'action_type': Actions.CAST_MINION if card.card_details['card_type'] == 'minion' else Actions.CAST_SPELL, 'source': card, 'target': 'board'})
        if not has_battlecry:
          available_actions.append({'action_type': Actions.CAST_MINION if card.card_details['card_type'] == 'minion' else Actions.CAST_SPELL, 'source': card, 'target': 'board'})

    if self.current_mana >= 2:
      available_actions.append({'action_type': Actions.CAST_HERO_POWER, 'source': self.hero_power, 'target': self.other_player})

    return available_actions

  def __str__(self):
    return str((self.player_class, str(self.health), str(self.deck)))

  def __repr__(self):
    return self.name

def main():

  global hero_powers
  global hunter_cards, mage_cards, warrior_cards
  global utility_cards

  global current_player

  random.seed(0)

  hero_powers, hunter_cards, mage_cards, warrior_cards, utility_cards = create_classic_cards()

  player = Player('hunter', 'player')
  enemy = Player('hunter', 'enemy')

  player.other_player = enemy
  enemy.other_player = player

  current_player = random.choice([player, enemy])

  player.generate_random_deck()
  enemy.generate_random_deck()

  game_results = simulate_game(player, enemy)
  print(game_results)


if __name__ == '__main__':
  main()
