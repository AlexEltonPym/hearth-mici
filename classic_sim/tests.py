import random
from card import Card
from deck import Deck
from player import Player
from game import Game
from enums import *
from card_sets import build_pool, get_utility_card
from strategy import GreedyAction


def test_classic_pool():
    card_pool = build_pool(CardSets.CLASSIC_HUNTER)
    assert len(card_pool) == 3


def test_game():
    
    random.seed(0)

    card_pool = build_pool(CardSets.CLASSIC_HUNTER)
    player = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
    enemy = Player(Classes.HUNTER, Deck().generate_random(card_pool), GreedyAction)
    game = Game(player, enemy)

    game.initalise_game()
    assert game.current_player == game.player


    assert get_utility_card('coin') in game.current_player.other_player.hand


    for i in range(8000):
        game.current_player.take_turn()

        if(game.player.health <= 0):
            return 0
        elif(game.enemy.health <= 0):
            return 1


    assert True

def main():
    test_classic_pool()
    test_game()

if __name__ == '__main__':
    main()
