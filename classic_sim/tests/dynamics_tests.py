import sys
from webbrowser import get
sys.path.append('../')

from dynamics import *
import dynamics
from action import Action
from inspect import signature
from player import Player
from card import Card
import inspect
from typing import ForwardRef
from enums import *
from random import choice, random
import pprint
import yaml # pip install pyyaml
import jsonpickle
import json
from copy import deepcopy
from game_manager import GameManager
from collections.abc import Callable
from typing import Union, get_origin, get_args


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

def test_generate_tree():
  game = GameManager().create_test_game()
  
  tundra_rhino1 = game.game_manager.get_card('Tundra Rhino', game.current_player.board)
  tundra_rhino2 = game.game_manager.get_card('Tundra Rhino', game.current_player.other_player.board)

  result_type = Callable[..., bool]
  tree = generate_tree(result_type, 0, 3)
  print_tree(tree, 0, Action(Actions.CAST_EFFECT, tundra_rhino1, [tundra_rhino2]))
  evaulation = tree(Action(Actions.CAST_EFFECT, tundra_rhino1, [tundra_rhino2]))
  print(f"{evaulation=}")
  

def print_tree(tree, depth, action):
  if type(tree).__name__ in dir(__builtins__):
    inputs = []
    output = tuple([])
  else:
    inputs, output = get_input_output_signature(tree.__class__)

  if len(inputs) == 0 or inputs[0][0] is inspect._empty:
    if callable(tree):
      print("  " * depth + str(tree) + " == " + str(tree(action)))
    else:
      print("  " * depth + "Literal " + str(tree))
  else:
    print("  " * depth + str(tree))
    for attr in tree.__dict__:
      print_tree(tree.__dict__[attr], depth+1, action)
  

def generate_tree(root_type, depth, MAX_DEPTH):

  internals, terminals, near_terminals = get_function_set()
  valid_internals = list(filter(lambda internal: root_type in internal[2], internals))
  valid_terminals = list(filter(lambda terminal: root_type in terminal[2], terminals))
  valid_near_terminals = list(filter(lambda internal: root_type in internal[2], near_terminals))

  # print(f"{root_type=}")
  # print("\n Internals")
  # for internal in valid_internals:
  #   print(internal)
  # print("\n Terminals")
  # for terminal in valid_terminals:
  #   print(terminal)
  # print("\n Near Terminals")
  # for terminal in valid_near_terminals:
  #   print(terminal)

  if depth == MAX_DEPTH - 1 and len(valid_near_terminals) > 0:
    chosen_function = choice(valid_near_terminals)
    child = generate_tree(chosen_function[1][0][0], depth+1, MAX_DEPTH)
    return chosen_function[0](child)
  elif depth == MAX_DEPTH and len(valid_terminals) > 0:
    chosen_terminal = choice(valid_terminals)
    if(callable(chosen_terminal[0])):
      return chosen_terminal[0]()
    else:
      return chosen_terminal[0]
  else:
    if len(valid_terminals) == 0:
      pickset = valid_internals
      chosen_function = choice(pickset)
    elif len(valid_internals) == 0:
      pickset = valid_terminals
      chosen_function = choice(pickset)
    else:
      pickset = valid_internals if random() < 0.99 else valid_terminals
      chosen_function = choice(pickset)
    if chosen_function[3]:
      if(callable(chosen_function[0])):
        return chosen_function[0]()
      else:
        return chosen_function[0]
    else:
      filled_inputs = []
      for input in chosen_function[1]:
        filled_inputs.append(generate_tree(input[0], depth+1, MAX_DEPTH))
      return chosen_function[0](*filled_inputs)


def get_function_set():
  internals = []
  terminals = []
  near_terminals = []
  near_terminal_classes = [ConstantInt, ConstantBool, ConstantCard, ConstantAttribute, NumOtherMinions, CardsInHand, DamageTaken, PlayerArmor, WeaponAttack, HasWeapon, MinionsPlayed, NumCardsInHand, NumWithCreatureType, NumDamaged, HasSecret]
  for dynamic_class in map(dynamics.__dict__.get, dynamics.__all__):
    inputs, output = get_input_output_signature(dynamic_class)
    if(len(inputs)==0):
      terminals.append((dynamic_class, inputs, output, True))
    else:
      internals.append((dynamic_class, inputs, output, False))
      if dynamic_class in near_terminal_classes:
        near_terminals.append((dynamic_class, inputs, output, False))

  oneone = Card(name="OneOne", collectable=False, card_type=CardTypes.MINION, manacost=1, attack=1, health=1)
  class_values = list(range(-20, 21)) + [True, False] + [o for o in OwnerFilters] + [c for c in CreatureTypes] + [a for a in Attributes] + [oneone]
  for class_value in class_values:
    terminals.append((class_value, [], (type(class_value),), True))

  return (internals, terminals, near_terminals)

    

def get_input_output_signature(dynamic_class):
  classes = {"CARD": Card, "PLAYER": Player}
  inputs = []
  output = None

  parameters = signature(dynamic_class).parameters
  for parameter in parameters:
    try:
      input_options = list(parameters[parameter].annotation.__constraints__)
      for index, input_option in enumerate(input_options):
        try:
          input_options[index] = classes[input_option.__forward_arg__]
        except AttributeError:
          pass
      input_options = tuple(input_options)
    except AttributeError:
      input_options = parameters[parameter].annotation
      try:
        input_options = classes[input_options.__forward_arg__]
      except AttributeError:
        pass
      input_options = tuple([input_options])
    inputs.append(input_options)

  try:
    output = list(signature(dynamic_class.__call__).return_annotation.__constraints__)
    for index, output_option in enumerate(output):
      try:
        output[index] = classes[output_option.__forward_arg__]
      except AttributeError:
        pass
    output = tuple(output)
  except AttributeError:
    output = signature(dynamic_class.__call__).return_annotation
    if isinstance(output, ForwardRef):
      output = classes[output.__forward_arg__]
    output = tuple([output])

  return (inputs, output)


if __name__ == "__main__":
  test_generate_tree()