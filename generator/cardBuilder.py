import json

from deap import base, creator, gp, tools, algorithms

from enum import Enum

import matplotlib.pyplot as plt
import networkx as nx

from networkx.readwrite import json_graph
import random
import os

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
  def __init__(self, baseManaCost, baseHp, baseAttack, isSpell, spell, attributes):
    self.baseManaCost = baseManaCost
    self.baseHp = baseHp
    self.baseAttack = baseAttack
    self.isSpell = isSpell
    self.spell = spell
    self.attributes = attributes

  def __repr__(self):
    return {
      'baseManaCost':self.baseManaCost, 
      'baseHp':self.baseHp,
      'baseAttack':self.baseAttack, 
      'isSpell':self.isSpell, 
      'spell': self.spell,
      'attributes': self.attributes,
    }

class Spell:
  def __init__(self, trigger, value):
    self.trigger = trigger
    self.value = value

  def __repr__(self):
    return {'trigger':self.trigger, 'value':self.value}


simple_type_names = ['Taunt', 'Lifesteal', 'Trigger', 'IsSpell', 'Integer', 'Boolean']
simple_types = []

def simple_type_init(self, val):
  self.val = val

def simple_type_repr(self):
  return self.val

for type_name in simple_type_names:
  exec("%s=type(type_name, (), { '__init__': simple_type_init, '__repr__': simple_type_repr })" % (type_name))


pset = gp.PrimitiveSetTyped("main", [], Card)
pset.addPrimitive(Card, [BaseManaCost, BaseHp, BaseAttack, IsSpell, Spell, Attributes], Card)
pset.addPrimitive(BaseManaCost, [Integer,], BaseManaCost)
pset.addPrimitive(BaseHp, [Integer,], BaseHp)
pset.addPrimitive(BaseAttack, [Integer,], BaseAttack)
pset.addPrimitive(Spell, [Trigger,Integer], Spell)
pset.addPrimitive(IsSpell, [Boolean], IsSpell)
pset.addPrimitive(Attributes, [Taunt, Lifesteal], Attributes)
pset.addPrimitive(Taunt, [Boolean], Taunt)
pset.addPrimitive(Lifesteal, [Boolean], Lifesteal)

pset.addPrimitive(Integer, [Integer], Integer)
pset.addPrimitive(Boolean, [Boolean], Boolean)
pset.addPrimitive(Trigger, [Trigger], Trigger)


pset.addTerminal(Trigger("WhenPlayed"), Trigger, name="WhenPlayed")
pset.addTerminal(Trigger("WhenDrawn"), Trigger, name="WhenDrawn")

pset.addTerminal(Boolean(True), Boolean, name="True")
pset.addTerminal(Boolean(True), Boolean, name="False")

for i in range(10):
  pset.addTerminal(Integer(i), Integer, name=str(i))



def evalCard(individual):
    compiled = toolbox.compile(expr=individual)
    s = json.dumps(compiled, default=lambda x: x.__repr__())
    #print(s)

    di = json.loads(s)


    # with open('newRawCard.json', 'w') as outfile:
    #   json.dump(di, indent=4, fp=outfile)
    
    # os.system('python3 rawCardProcessor.py')
    # os.system('./simulatorEvaluator.sh')

    

    return sum((10-di["baseManaCost"], di["baseAttack"], di["baseHp"], di["spell"]["value"])),



creator.create("FitnessMax", base.Fitness, weights=(1.0,))
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
pop = toolbox.population(n=10000)
hof = tools.HallOfFame(1)
algorithms.eaSimple(pop, toolbox, 0.5, 0.2, 2, stats, halloffame=hof)

for i, hero in enumerate(hof):
  compiled = gp.compile(hero, pset)
  asJson = json.dumps(compiled, default=lambda x: x.__repr__(), indent=4)
  print("Hall of famer %i: %s" % (i, asJson))



with open('newRawCard.json', 'w') as outfile:
  json.dump(compiled, default=lambda x: x.__repr__(), indent=4, fp=outfile)