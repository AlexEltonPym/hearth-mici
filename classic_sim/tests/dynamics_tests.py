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
  generate_tree(result_type)
  assert False

def generate_tree(root_type):
 
  for dynamic_class in map(dynamics.__dict__.get, dynamics.__all__):
    inputs, output = get_input_output_signature(dynamic_class)
    print(f"\n{dynamic_class=}")
    print(f"{inputs=}")
    print(f"{output=}")

    

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
    
  return (inputs, output)