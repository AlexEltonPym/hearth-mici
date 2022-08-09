import random

def create_classic_cards():
  hunter_hero_power = Card(-1, 'Hunter hero power', {'mana': 2, 'effects':[{'effect_type': 'deal_damge', 'filter': 'enemy hero'}]})
  elven_archer = Card(0, 'Elven archer', {'type': 'creature', 'mana': 1, 'attack':1, 'health':1, 'effects':[{'effect_type': 'deal_damge', 'filter': 'enemy minions'}]})
  basic_minion = Card(1, 'Basic minion', {'type': 'creature', 'mana': 4, 'attack':5, 'health':5, 'effects':[]})

  hunter_cards = [elven_archer, basic_minion]
  mage_cards = []
  warrior_cards = []
  hero_powers = {'hunter': hunter_hero_power}

  return hero_powers, hunter_cards, mage_cards, warrior_cards


def simulate_game(player, enemy):
  current_player = random.choice([-1, 1])

  player.deck.shuffle()
  enemy.deck.shuffle()

  if current_player == 1:
    player.draw(4)
    player.mulligan()
    enemy.draw(3)
    enemy.mulligan()
    enemy.add_coin()
  else:
    enemy.draw(4)
    enemy.mulligan()
    player.draw(3)
    player.mulligan()
    player.add_coin()


  while True:
    if current_player == 1:
      player.take_turn()
    else:
      enemy.take_turn()
    
    current_player *= -1

    if(player.health <= 0):
      return 0
    elif(enemy.health <= 0):
      return 1

class Deck():
  def __init__(self, starting_deck):
    self.deck = starting_deck

  def generate_random(self):
    while len(self.deck) < 30:
      self.deck.append(random.choice(hunter_cards))

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

  def get_available_targets(self):
    targets = []
    taunt_targets = [target if target['attributes']['taunt'] for target in ]
    for creature in other_player.board.filter(x: x['attributes']['taunt']):
      

  def __str__(self):
    return self.name

  def __repr__(self):
    return self.name

class Player():
  def __init__(self, player_class):
    self.player_class = player_class
    self.hero_power = hero_powers[player_class]
    self.health = 30
    self.weapon = None
    self.deck = Deck([])
    self.hand = []
    self.board = []

  def generate_random_deck(self):
    self.deck.generate_random()
  
  def draw(self, num_to_draw):
    for i in range(num_to_draw):
      self.hand.append(self.deck.deck.pop())
  
  def mulligan(self):
    new_hand = []
    for card in self.hand:
      if card.card_details['mana'] > 3:
        new_hand.append(self.deck.deck.pop())
        self.deck.deck.append(card)
      else:
        new_hand.append(card)
    self.hand = new_hand
    self.deck.shuffle()

  def take_turn(self):
    available_actions = []
    for creature in self.board:
      for target in creature['targets']:
        available_actions.append({'source': creature, 'target': creature.available_targets})


  def __str__(self):
    return str((self.player_class, str(self.health), str(self.deck)))

def main():

  global hero_powers
  global hunter_cards, mage_cards, warrior_cards

  hero_powers, hunter_cards, mage_cards, warrior_cards = create_classic_cards()

  player = Player('hunter')
  player.generate_random_deck()
  enemy = Player('hunter')
  enemy.generate_random_deck()

  game_results = simulate_game(player, enemy)
  print(game_results)


if __name__ == '__main__':
  main()
