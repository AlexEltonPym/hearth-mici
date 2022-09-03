from random import choice
import sys, inspect

def choice_with_none(iterable):
  if len(iterable) == 0:
    return None
  else:
    return choice(iterable)

def get_classes(module):
  classes = []
  for _, obj in inspect.getmembers(sys.modules[module.__name__]):
      if inspect.isclass(obj) and obj.__module__ == module.__name__:
          classes.append(obj)
  return classes

