import json

from deap import base, creator, gp, tools, algorithms

from enum import Enum

import matplotlib.pyplot as plt
import networkx as nx

from networkx.readwrite import json_graph
import random
import os

class Boolean:
  def __init__(self, val):
    self.val = val

  def __repr__(self):
    return str(self.val)

  def get_val(self):
    return self.val

class Integer:
  def __init__(self, val):
    self.val = val

  def __repr__(self):
    return self.val

class Trigger:
  def __init__(self, val):
    self.val = val

  def __repr__(self):
    return self.val

class Taunt:
  def __init__(self, val):
    self.val = val

  def __repr__(self):
    return self.val

class Lifesteal:
  def __init__(self, val):
    self.val = val

  def __repr__(self):
    return self.val

class BaseManaCost:
  def __init__(self, baseManaCost):
    self.baseManaCost = baseManaCost

  def __repr__(self):
    return self.baseManaCost

class BaseHp:
  def __init__(self, baseHp):
    self.baseHp = baseHp

  def __repr__(self):
    return self.baseHp

class BaseAttack:
  def __init__(self, baseAttack):
    self.baseAttack = baseAttack

  def __repr__(self):
    return self.baseAttack

class Attributes:
  def __init__(self, taunt, lifesteal):
    self.taunt = taunt
    self.lifesteal = lifesteal

  def __repr__(self):
    return {'TAUNT':self.taunt, 'LIFESTEAL':self.lifesteal}

class Card:
  def __init__(self, baseManaCost, baseHp, baseAttack, effect1, effect2, effect3, effect4, effect5, effect6, attributes):
    self.baseManaCost = baseManaCost
    self.baseHp = baseHp
    self.baseAttack = baseAttack
    self.effect1 = effect1
    self.effect2 = effect2
    self.effect3 = effect3
    self.effect4 = effect4
    self.effect5 = effect5
    self.effect6 = effect6
    self.attributes = attributes

  def __repr__(self):
    return {
      'baseManaCost':self.baseManaCost, 
      'baseHp':self.baseHp,
      'baseAttack':self.baseAttack, 
      'effect1': self.effect1,
      'effect2': self.effect2,
      'effect3': self.effect3,
      'effect4': self.effect4,
      'effect5': self.effect5,
      'effect6': self.effect6,
      'attributes': self.attributes,
    }

class Effect:
  def __init__(self, trigger, value, active):
    self.trigger = trigger
    self.value = value
    self.active = active

  def __repr__(self):
    if(self.active.__repr__() == "True"):
      return {'trigger':self.trigger, 'value':self.value, 'active':self.active}
    else:
      return {}

    


# simple_type_names = ['Taunt', 'Lifesteal', 'Trigger', 'Integer', 'Boolean']
# simple_types = []

# def simple_type_init(self, val):
#   self.val = val

# def simple_type_repr(self):
#   return self.val

# for type_name in simple_type_names:
#   exec("%s=type(type_name, (), { '__init__': simple_type_init, '__repr__': simple_type_repr })" % (type_name))


pset = gp.PrimitiveSetTyped("main", [], Card)
pset.addPrimitive(Card, [BaseManaCost, BaseHp, BaseAttack, Effect, Effect, Effect, Effect, Effect, Effect, Attributes], Card)
pset.addPrimitive(BaseManaCost, [Integer,], BaseManaCost)
pset.addPrimitive(BaseHp, [Integer,], BaseHp)
pset.addPrimitive(BaseAttack, [Integer,], BaseAttack)
pset.addPrimitive(Effect, [Trigger,Integer,Boolean], Effect)
pset.addPrimitive(Attributes, [Taunt, Lifesteal], Attributes)
pset.addPrimitive(Taunt, [Boolean], Taunt)
pset.addPrimitive(Lifesteal, [Boolean], Lifesteal)

pset.addPrimitive(Integer, [Integer], Integer)
pset.addPrimitive(Boolean, [Boolean], Boolean)
pset.addPrimitive(Trigger, [Trigger], Trigger)


pset.addTerminal(Trigger("WhenPlayed"), Trigger, name="WhenPlayed")
pset.addTerminal(Trigger("WhenDrawn"), Trigger, name="WhenDrawn")

pset.addTerminal(Boolean(True), Boolean, name="True")
pset.addTerminal(Boolean(False), Boolean, name="False")

for i in range(10):
  pset.addTerminal(Integer(i), Integer, name=str(i))


#NOTE: must return a tuple
def evalCard(individual):
    compiled = toolbox.compile(expr=individual)
    s = json.dumps(compiled, default=lambda x: x.__repr__())
    #print(s)

    di = json.loads(s)


    # with open('newRawCard.json', 'w') as outfile:
    #   json.dump(di, indent=4, fp=outfile)
    
    # os.system('python3 rawCardProcessor.py')
    # os.system('./simulatorEvaluator.sh')
    EFFECT_TARGET_WEIGHT = 3.0
    EFFECT_TARGET = 2

    costs = sum((di["baseManaCost"], 10-di["baseAttack"], 10-di["baseHp"]))
    costs = costs + abs(EFFECT_TARGET-sum([0 if di[f"effect{i}"]=={} else 1 for i in range(1, 7)])) * EFFECT_TARGET_WEIGHT

    return costs,



creator.create("FitnessMax", base.Fitness, weights=(-1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("expr", gp.genGrow, pset=pset, min_=3, max_=3)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)
toolbox.register("evaluate", evalCard)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("expr_mut", gp.genGrow, min_=10, max_=13)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

stats = tools.Statistics(lambda ind: ind.fitness.values)
pop = toolbox.population(n=10)
hof = tools.HallOfFame(1)
algorithms.eaSimple(pop, toolbox, 0.5, 0.2, 10, stats, halloffame=hof)

for i, hero in enumerate(hof):
  compiled = gp.compile(hero, pset)
  asJson = json.dumps(compiled, default=lambda x: x.__repr__(), indent=4)
  print("Hall of famer %i: %s" % (i, asJson))



with open('newRawCard.json', 'w') as outfile:
  json.dump(compiled, default=lambda x: x.__repr__(), indent=4, fp=outfile)