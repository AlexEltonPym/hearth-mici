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

def test_return_types():
  print("Inputs")
  for parameter in signature(Add).parameters:
    print(signature(Add).parameters[parameter].annotation)
  print("Returns")
  print(signature(Add.__call__).return_annotation)
  assert True

def test_return_types_constant():
  print("Inputs")
  for parameter in signature(Constant).parameters:
    print(signature(Constant).parameters[parameter].annotation)
  print("Returns")
  print(signature(Constant.__call__).return_annotation.__constraints__)
  assert True

def test_equate_atttribute_to_integer():
  compared = Equals(Constant(1), Constant(Attributes.CHARGE))
  result = compared(Action(Actions.CAST_EFFECT, None, [None]))
  print(type(Attributes.CHARGE))
  assert True

def test_generate_tree():
  result_type = int
  tree = generate_tree(result_type, 0, 2)
  print("PRINTING TREE")
  print_tree(tree, 0)
  evaulation = tree(Action(Actions.CAST_EFFECT, None, [None]))
  print(f"{evaulation=}")
  

def print_tree(tree, depth):
  inputs, output = get_input_output_signature(tree.__class__)

  if len(inputs) == 0 or inputs[0][0] is inspect._empty:
    print("  " * depth + str(tree(Action(Actions.CAST_EFFECT, None, [None]))))
  else:
    print("  " * depth + str(tree))
    for attr in tree.__dict__:
      print_tree(tree.__dict__[attr], depth+1)
  

def generate_tree(root_type, depth, MAX_DEPTH):

  internals, terminals = get_function_set()
  valid_internals = list(filter(lambda internal: root_type in internal[2], internals))
  valid_terminals = list(filter(lambda terminal: root_type in terminal[2], terminals))

  print(root_type)
  print("\n Internals")
  for internal in valid_internals:
    print(internal)
  
  print("\n Terminals")
  for terminal in valid_terminals:
    print(terminal)
  if depth == MAX_DEPTH:
    chosen_terminal = choice(valid_terminals)
    print(f"{chosen_terminal[0]=}")
    return chosen_terminal[0]()
  else:
    pickset = valid_internals if random() < 0.9 else valid_terminals
    chosen_function = choice(pickset)
    if chosen_function[3]:
      return chosen_function[0]()
    else:
      filled_inputs = []
      for input in chosen_function[1]:
        filled_inputs.append(generate_tree(input[0], depth+1, MAX_DEPTH))
      return chosen_function[0](*filled_inputs)


def get_function_set():
  internals = []
  terminals = []
  for dynamic_class in map(dynamics.__dict__.get, dynamics.__all__):
    inputs, output = get_input_output_signature(dynamic_class)
    if(len(inputs)==0):
      # terminals.append((dynamic_class, inputs, output, True))
      pass
    else:
      if dynamic_class == Add or dynamic_class == Multiply:
        internals.append((dynamic_class, inputs, output, False))

  class_names = ["n2", "n1", "zero", "p1", "p2", "true", "false", "friendly", "enemy", "all"]
  class_values = [-2, -1, 0, 1, 2, True, False, OwnerFilters.FRIENDLY, OwnerFilters.ENEMY, OwnerFilters.ALL]

  for class_name, class_value in zip(class_names, class_values):
    exec(f"class {class_name}(object):\n\
            def __init__(self):\n\
              pass\n\
            def __call__(self, action):\n\
              return {class_value}")
    
    terminals.append((eval(f"{class_name}"), [], (type(class_value),), True))

  

  return (internals, terminals)

    

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