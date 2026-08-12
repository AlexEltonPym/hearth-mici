"""Pilot selection for probe_card_values.py, without touching
evolve_metagame_shift.py.

The probe's work items carry their piloting agent in the eval_weights slot,
and evolve_metagame_shift.make_fixed_agent turns that slot into a strategy
object on the worker: a list -> GreedyActionSmart, a dict -> NeuralGreedy.
There is no third case, so a beam-search pilot cannot be expressed. This
module widens the slot to also accept a value_net_selfplay agent SPEC tuple
(("beam", (net_weights, beam_width, depth)), ("net", w), ("linear", w)) by
REBINDING make_fixed_agent at runtime - evolve_metagame_shift is owned
elsewhere and stays unmodified.

Why a module and not an inline monkeypatch in the worker script: joblib's
loky children pickle _run_one by reference and re-import
evolve_metagame_shift fresh, so a patch applied only in the parent process
would be silently undone in every child. Importing this module applies the
rebind, and _run_probe re-applies it per task, so both the parent and every
child process agree on the pilot.
"""
import sys

sys.path.append('../../src')

import evolve_metagame_shift as ems
from strategy import GreedyActionSmart, NeuralGreedy
from value_net_selfplay import make_agent


def make_probe_agent(eval_weights):
  """Superset of evolve_metagame_shift.make_fixed_agent: adds the spec tuple."""
  if isinstance(eval_weights, tuple):
    return make_agent(eval_weights)
  if isinstance(eval_weights, dict):
    return NeuralGreedy(eval_weights)
  return GreedyActionSmart(eval_weights) if eval_weights else GreedyActionSmart()


ems.make_fixed_agent = make_probe_agent


def _run_probe(work_item):
  ems.make_fixed_agent = make_probe_agent  #re-apply per task: see module docstring
  return ems.play_matchup_till_stoppage(*work_item)


def agent_spec(kind, eval_weights, beam_width=3, depth=3):
  """CLI --agent choice + loaded weights -> the eval_weights slot's payload.

  'auto' keeps the historical behaviour exactly (raw weights through
  make_fixed_agent's own list/dict dispatch), so re-running an old condition
  is byte-for-byte the same experiment.
  """
  if kind == "auto":
    return eval_weights
  if kind == "linear":
    return ("linear", eval_weights)
  if kind == "net":
    return ("net", eval_weights)
  if kind == "beam":
    return ("beam", (eval_weights, beam_width, depth))
  raise ValueError(f"unknown agent kind {kind}")
