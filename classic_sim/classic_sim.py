import random
from card import Card
from deck import Deck
from player import Player
from game import Game
from enums import *
from card_sets import build_pool
from strategy import GreedyAction

def main():
    
    random.seed(0)

    card_pool = build_pool(CardSets.CLASSIC_HUNTER)
    player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
    enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
    game = Game(player, enemy)


    game_results = game.simulate_game()
    print(game_results)


if __name__ == '__main__':
    main()
