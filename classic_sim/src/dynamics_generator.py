
from dynamics import *
import dynamics
from inspect import signature
from card import Card
import inspect
from typing import ForwardRef
from enums import *
from typing import Callable



def create_dynamics_tree(return_type, max_depth, internals_ratio, random_state, is_condition=False):
  CARD="CARD"
  result_type = Callable[..., return_type]
  internals, terminals, near_terminals = get_function_set()
  if is_condition:
    for index, terminal in enumerate(terminals):
      if terminal[0] == dynamics.AttackValue:
        terminals.pop(index)

  tree = generate_tree(result_type, 0, max_depth, internals_ratio, internals, terminals, near_terminals, random_state)

  return tree
  

def print_tree(tree, depth, action):

  if type(tree) in [int, bool]:
    inputs = []
  else:
    inputs, _ = get_input_output_signature(tree.__class__)

  if len(inputs) == 0 or inputs[0][0] is inspect._empty:
    if callable(tree):
      print("  " * depth + str(tree) + " == " + str(tree(action)))
    else:
      print("  " * depth + "Literal " + str(tree))
  else:
    print("  " * depth + str(tree))
    for attr in tree.__dict__:
      print_tree(tree.__dict__[attr], depth+1, action)
  

def generate_tree(root_type, depth, MAX_DEPTH, internals_ratio, internals, terminals, near_terminals, random_state):

  valid_internals = list(filter(lambda internal: root_type in internal[2], internals))
  valid_terminals = list(filter(lambda terminal: root_type in terminal[2], terminals))
  valid_near_terminals = list(filter(lambda internal: root_type in internal[2], near_terminals))

  # print(f"{root_type=}")
  # print(f"{depth=}")
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
    chosen_function = valid_near_terminals[random_state.randint(len(valid_near_terminals))]
    filled_inputs = []
    for input in chosen_function[1]:
      filled_inputs.append(generate_tree(input[0], depth+1, MAX_DEPTH, internals_ratio, internals, terminals, near_terminals, random_state))
    return chosen_function[0](*filled_inputs)
  elif depth == MAX_DEPTH and len(valid_terminals) > 0:
    chosen_terminal = valid_terminals[random_state.randint(len(valid_terminals))]
    if(callable(chosen_terminal[0])):
      return chosen_terminal[0]()
    else:
      return chosen_terminal[0]
  else:
    if len(valid_terminals) == 0 and len(valid_internals) > 0:
      pickset = valid_internals
      chosen_function = pickset[random_state.randint(len(pickset))]
    elif len(valid_internals) == 0 and len(valid_terminals) > 0:
      pickset = valid_terminals
      chosen_function = pickset[random_state.randint(len(pickset))]
    else:
      pickset = valid_internals if random_state.random() < internals_ratio else valid_terminals

      chosen_function = pickset[random_state.randint(len(pickset))]
    if chosen_function[3]:
      if(callable(chosen_function[0])):
        return chosen_function[0]()
      else:
        return chosen_function[0]
    else:
      filled_inputs = []
      for input in chosen_function[1]:
        filled_inputs.append(generate_tree(input[0], depth+1, MAX_DEPTH, internals_ratio, internals, terminals, near_terminals, random_state))
      return chosen_function[0](*filled_inputs)


def get_function_set():
  internals = []
  terminals = []
  near_terminals = []
  near_terminal_classes = [RandomInt, ConstantInt, ConstantBool, ConstantCard, ConstantAttribute, NumOtherMinions, CardsInHand, DamageTaken, PlayerArmor, WeaponAttack, HasWeapon, MinionsPlayed, NumCardsInHand, NumWithCreatureType, NumDamaged, HasSecret]
  for dynamic_class in map(dynamics.__dict__.get, dynamics.__all__):
    inputs, output = get_input_output_signature(dynamic_class)
    if(len(inputs)==0):
      terminals.append((dynamic_class, inputs, output, True))
    else:
      internals.append((dynamic_class, inputs, output, False))
      if dynamic_class in near_terminal_classes:
        near_terminals.append((dynamic_class, inputs, output, False))

  oneone = Card(name="OneOne", collectable=False, card_type=CardTypes.MINION, manacost=1, attack=1, health=1)
  class_values = list(range(-20, 21)) + [True, False] + [o for o in OwnerFilters] + [a for a in Attributes] + [c for c in CreatureTypes]
  for class_value in class_values:
    terminals.append((class_value, [], (type(class_value),), True))
  terminals.append((oneone, [], ('CARD',), True))


  return (internals, terminals, near_terminals)

    

def get_input_output_signature(dynamic_class):
  classes = {"CARD": Card}
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


  class_name = str(dynamic_class.__name__)
  input_strings = []
  output_strings = []
  for _input in inputs:
    if(type(_input) == Callable):
      i = str(_input)
      bits = i.split("..., ")[1].split("]")[0]
      input_strings.append(bits)
    else:
      input_strings.append((str(_input)))
  for _output in output:
    o = str(_output)
    bits = o.split("..., ")[1].split("]")[0]
    output_strings.append(bits)
  
  print(class_name, input_strings, output_strings)


  return (inputs, output)
