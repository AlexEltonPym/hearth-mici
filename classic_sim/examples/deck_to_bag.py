import sys
sys.path.append('../')

from enums import *

from game_manager import GameManager



game_manager = GameManager()
game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR])
pool = game_manager.get_player_pool()
num_classics = 130
num_class = 24
[print(f"{index}: {card.name}") for index, card in enumerate(pool)]
