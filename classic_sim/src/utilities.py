import sys, inspect
import _pickle as cPickle

def _stripped_dump(payload, game):
  #the game_manager's prototype players (and its game backref) roughly double
  #the pickle payload and are never read by the forward model, so detach them
  #around the dump. setup_players is the only consumer and it never runs on clones.
  gm = game.game_manager
  proto_player, proto_enemy, gm_game = gm.player, gm.enemy, gm.game
  gm.player = None
  gm.enemy = None
  gm.game = None
  try:
    data = cPickle.dumps(payload, -1)
  finally:
    gm.player = proto_player
    gm.enemy = proto_enemy
    gm.game = gm_game
  return data

def fast_clone(game):
  clone = cPickle.loads(_stripped_dump(game, game))
  clone.game_manager.game = clone
  return clone

def clone_with_action(game, action):
  #pickling the state and action together preserves their shared references,
  #so the returned action is bound to the clone's objects and can be performed
  #on it directly - no need to re-derive the action list on the clone
  clone, bound_action = cPickle.loads(_stripped_dump((game, action), game))
  clone.game_manager.game = clone
  return clone, bound_action

def choice_with_none(iterable, random_state):
  if len(iterable) == 0:
    return None
  else:
    return random_state.choice(iterable)

def get_classes(module):
  classes = []
  for _, obj in inspect.getmembers(sys.modules[module.__name__]):
      if inspect.isclass(obj) and obj.__module__ == module.__name__:
          classes.append(obj)
  return classes

