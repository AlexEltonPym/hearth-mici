import sys
  
# appending the parent directory path
sys.path.append('../')

from card import Card
from zones import Deck
from player import Player
from game import Game, TooManyActions
from enums import *
from card_sets import *
from strategy import GreedyAction, RandomAction, RandomNoEarlyPassing
from numpy import empty, array
from action import Action
from tqdm import tqdm
from numpy.random import RandomState
from card_generator import *

from game_manager import GameManager
from itertools import zip_longest
from tqdm import tqdm

from random import randint

def test_random_reshuffle():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR, CardSets.CLASSIC_MAGE])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR, CardSets.CLASSIC_MAGE])
  game_manager.create_player(game_manager.random_state.choice([c for c in Classes]), Deck.generate_random, RandomNoEarlyPassing)
  game_manager.create_enemy(game_manager.random_state.choice([c for c in Classes]), Deck.generate_random, RandomNoEarlyPassing)
  game = game_manager.create_game()
  game_results = empty(100)

  def get_deck_stats():
    player_deck = game.player.deck.get_all()
    enemy_deck = game.enemy.deck.get_all()
    player_deck_string = sorted(game.player.deck.get_string())
    enemy_deck_string = sorted(game.enemy.deck.get_string())
    player_mean_attack = array([card.get_attack() if card.card_type==CardTypes.MINION else 0 for card in player_deck]).mean()
    enemy_mean_attack = array([card.get_attack() if card.card_type==CardTypes.MINION else 0 for card in enemy_deck]).mean()
    player_mean_health = array([card.get_health() if card.card_type==CardTypes.MINION else 0 for card in player_deck]).mean()
    enemy_mean_health = array([card.get_health() if card.card_type==CardTypes.MINION else 0 for card in enemy_deck]).mean()
    player_mean_manacost = array([card.get_manacost() for card in player_deck]).mean()
    enemy_mean_manacost = array([card.get_manacost() for card in enemy_deck]).mean()
    return [player_deck_string, enemy_deck_string, player_mean_attack, enemy_mean_attack, player_mean_health, enemy_mean_health, player_mean_manacost, enemy_mean_manacost]

  def compare_stats(statsA, statsB):
    assert len(statsA[0]) == 30
    assert len(statsB[0]) == 30
    for player_cardA, player_cardB in zip_longest(statsA[0], statsB[0], fillvalue=None):
      assert player_cardA == player_cardB

    for enemy_cardA, enemy_cardB in zip_longest(statsA[1], statsB[1], fillvalue=None):
      assert enemy_cardA == enemy_cardB
    
    for i in range(2, 8):
      assert statsA[i] == statsB[i]
    
  game.reset_game()
  deck_stats = get_deck_stats()

  for i in range(100):
    game.reset_game()
    new_deck_stats = get_deck_stats()
    compare_stats(deck_stats, new_deck_stats)
    deck_stats = new_deck_stats
    game.start_game()
    game_results[i] = game.play_game()

def test_cards_valid():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR, CardSets.CLASSIC_MAGE])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR, CardSets.CLASSIC_MAGE])
  game_manager.create_player(game_manager.random_state.choice([c for c in Classes]), Deck.generate_random, RandomNoEarlyPassing)
  game_manager.create_enemy(game_manager.random_state.choice([c for c in Classes]), Deck.generate_random, RandomNoEarlyPassing)
  i = 0
  for card in game_manager.get_player_pool() + [get_hero_power(c) for c in Classes]:
    print(f"{card=}")
    check_card_valid(card)

   
def test_random_card_game():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, RandomNoEarlyPassing)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, RandomNoEarlyPassing)
  game = game_manager.create_game()

  game_results = empty(10)

  for i in range(10):
    game_results[i] = game.play_game()
    game.reset_game()
    game.start_game()
  
  assert game_results.mean() <= 1 and game_results.mean() >= 0

def test_big_games():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)
  game = game_manager.create_game()
  game_results = empty(10)

  for i in tqdm(range(10)):
    game_results[i] = game.play_game()
    game.reset_game()
    game.start_game()
    assert len(game.current_player.deck) + len(game.current_player.hand) == 30
    assert len(game.current_player.other_player.deck) + len(game.current_player.other_player.hand) == 31
    assert len(game.player.graveyard) == 0
    assert len(game.enemy.graveyard) == 0
    assert game.player.attack == 0
    assert game.player.health == 30
    assert game.enemy.attack == 0
    assert game.enemy.health == 30

  assert game_results.mean() < 1 and game_results.mean() > 0

def test_big_simulate():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(10)
  assert result > 0 and result < 1

def test_big_simulate_parralel():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(10, silent=True, parralel=-1)
  assert result > 0 and result < 1

def test_xl_big_random_cards():
  random_state = RandomState(0)
  for k in tqdm(range(100)):
    rand_seed = random_state.randint(0, 1000)
    print(f"seed was {rand_seed}")

    game_manager = GameManager(RandomState(rand_seed))
    game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
    game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
    for j in range(100):
      game_manager.create_player(Classes.HUNTER, Deck.generate_random, RandomNoEarlyPassing)
      game_manager.create_enemy(Classes.MAGE, Deck.generate_random, RandomNoEarlyPassing)
    
      game = game_manager.create_game()

      game_results = empty(100)

      for i in range(100):
        game_result = game.play_game()
        assert game_result == 1 or game_result == 0
        game_results[i] = game_result
        game.reset_game()
        game.start_game()
      
      assert game_results.mean() < 1 and game_results.mean() > 0

def test_generative_cards():
  random_seed = randint(1, 10000)
  print(f"{random_seed=}")
  game_manager = GameManager(RandomState(4218))
  game_manager.create_player_pool([CardSets.RANDOM_CARDS])
  game_manager.create_enemy_pool([CardSets.RANDOM_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, RandomNoEarlyPassing)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, RandomNoEarlyPassing)
  game = game_manager.create_game()
  # for card in game_manager.player.deck:
  #   print(card)

  # print("---")
  # for card in game_manager.enemy.deck:
  #   print(card)

  game_results = []#empty(100)
  for i in tqdm(range(100)):
    try:
      game_result = game.play_game()
    except (TooManyActions, RecursionError) as e:
      game_result = None
      # print(e)
      # for card in list(game_manager.enemy.deck) + list(game_manager.player.deck):
      #   print(card)
      # print(game_manager.player.deck)
    game_results.append(game_result)
    game.reset_game()
    game.start_game()
  print(game_results)
      

if __name__ == "__main__":
  for i in range(1):
    test_generative_cards()