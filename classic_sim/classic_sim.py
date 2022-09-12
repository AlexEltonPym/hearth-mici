from zones import Deck
from enums import *
from strategy import GreedyAction, RandomAction, RandomNoEarlyPassing
from game_manager import GameManager
NUM_GAMES = 16

def main():
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER, CardSets.TEST_CARDS])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.TEST_CARDS])
  game_manager.create_player(Classes.HUNTER, Deck.generate_random, GreedyAction)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_random, GreedyAction)

  result = game_manager.simulate(NUM_GAMES, parralel=-1)
  assert result > 0 and result < 1
  print(result)

if __name__ == '__main__':
  main()
