import sys, inspect
import _pickle as cPickle

def _stripped_dump(payload, game):
  #the game_manager's prototype players (and its game backref) roughly double
  #the pickle payload and are never read by the forward model, so detach them
  #around the dump. setup_players is the only consumer and it never runs on clones.
  #the RandomState is also detached: reconstructing numpy generators dominates
  #loads, so clones are handed the live master stream instead (_revive).
  gm = game.game_manager
  proto_player, proto_enemy, gm_game, gm_random = gm.player, gm.enemy, gm.game, gm.random_state
  gm.player = None
  gm.enemy = None
  gm.game = None
  gm.random_state = None
  try:
    data = cPickle.dumps(payload, -1)
  finally:
    gm.player = proto_player
    gm.enemy = proto_enemy
    gm.game = gm_game
    gm.random_state = gm_random
  return data

def _revive(clone, random_state):
  clone.game_manager.game = clone
  clone.game_manager.random_state = random_state

def fast_clone(game):
  random_state = game.game_manager.random_state
  clone = cPickle.loads(_stripped_dump(game, game))
  _revive(clone, random_state)
  return clone

def clone_with_action(game, action):
  #pickling the state and action together preserves their shared references,
  #so the returned action is bound to the clone's objects and can be performed
  #on it directly - no need to re-derive the action list on the clone
  random_state = game.game_manager.random_state
  clone, bound_action = cPickle.loads(_stripped_dump((game, action), game))
  _revive(clone, random_state)
  return clone, bound_action

class BoundCloner():
  #dumps the state (plus its action list) once, then stamps out clones with
  #loads only - the cheap half of the pickle round-trip. use when several
  #clones of the same state are needed, e.g. one per candidate action.
  def __init__(self, game, actions=None):
    self._random_state = game.game_manager.random_state
    self._data = _stripped_dump((game, actions), game)

  def clone(self):
    clone, bound_actions = cPickle.loads(self._data)
    _revive(clone, self._random_state)
    return clone, bound_actions

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

