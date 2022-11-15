import sys
sys.path.append('../')

from dynamics import *
from action import Action
from inspect import signature
from enums import *
from random import choice

from game_manager import GameManager
from dynamics_generator import *
from numpy.random import RandomState

def test_return_types():
  print("Inputs")
  for parameter in signature(Add).parameters:
    print(signature(Add).parameters[parameter].annotation)
  print("Returns")
  print(signature(Add.__call__).return_annotation)
  assert True


def test_equate_atttribute_to_integer():
  compared = Equals(ConstantInt(1), ConstantAttribute(Attributes.CHARGE))
  result = compared(Action(Actions.CAST_EFFECT, None, [None]))
  print(type(Attributes.CHARGE))
  assert True

def test_dyanamics_tree():
  tree = create_dynamics_tree(return_type=choice([int, bool, "CARD", Attributes]), max_depth=3, internals_ratio=0.4, random_state=RandomState())

  game = GameManager().create_test_game()
  tundra_rhino1 = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  tundra_rhino2 = game.game_manager.get_card('Tundra Rhino', game.current_player.other_player.board)
  print_tree(tree, 0, Action(Actions.CAST_EFFECT, tundra_rhino1, [tundra_rhino2]))
  evaulation = tree(Action(Actions.CAST_EFFECT, tundra_rhino1, [tundra_rhino2]))
  print(f"{evaulation=}")


if __name__ == "__main__":
  for i in range(100):
    test_dyanamics_tree()