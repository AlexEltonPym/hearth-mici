import json
import pickle
from deap import base, creator, gp, tools, algorithms

from enum import Enum

import matplotlib.pyplot as plt
import networkx as nx

from networkx.readwrite import json_graph

import random
import os
import numpy
from tqdm import tqdm

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

#NOTE: must return a tuple
def evalCard(indi_uncompiled):
    compiled = toolbox.compile(expr=indi_uncompiled)
    indi = json.loads(json.dumps(compiled, default=lambda x: x.__repr__()))

    # with open('newRawCard.json', 'w') as outfile:
    #   json.dump(di, indent=4, fp=outfile)
    
    # os.system('python3 rawCardProcessor.py')
    # os.system('./simulatorEvaluator.sh')


    costs = sum((indi["baseManaCost"], 10-indi["baseAttack"], 10-indi["baseHp"]))
    costs = costs + abs(EFFECT_TARGET-sum([0 if indi[f"effect{i}"]=={} else 1 for i in range(1, 7)])) * EFFECT_TARGET_WEIGHT

    return costs,

def eaSimpleCheckpointed(population, toolbox, cxpb, mutpb, ngen, stats=None, halloffame=None, verbose=True):

    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)

    record = stats.compile(population) if stats else {}
    logbook.record(gen=0, nevals=len(invalid_ind), **record)
    if verbose:
        print(logbook.stream)

    # Begin the generational process
    for gen in range(1, ngen + 1):
        # Select the next generation individuals
        offspring = toolbox.select(population, len(population))

        # Vary the pool of individuals
        offspring = algorithms.varAnd(offspring, toolbox, cxpb, mutpb)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offspring)

        # Replace the current population by the offspring
        population[:] = offspring

        # Append the current generation statistics to the logbook
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
        if verbose:
            print(logbook.stream)

    return population, logbook

def initial_individual(pset):
  return gp.PrimitiveTree.from_string("Card(BaseManaCost(Integer(0)), BaseHp(Integer(1)), BaseAttack(Integer(Integer(Integer(Integer(1))))), Effect(Trigger(WhenDrawn), Integer(2), Boolean(Boolean(Boolean(True)))), Effect(Trigger(Trigger(Trigger(Trigger(WhenDrawn)))), Integer(2), Boolean(False)), Effect(Trigger(WhenDrawn), Integer(7), Boolean(False)), Effect(Trigger(WhenDrawn), Integer(3), Boolean(False)), Effect(Trigger(WhenDrawn), Integer(1), Boolean(True)), Effect(Trigger(WhenDrawn), Integer(2), Boolean(False)), Attributes(Taunt(True), Lifesteal(True)))", pset)


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

creator.create("FitnessMax", base.Fitness, weights=(-1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("pre_built", initial_individual, pset)
toolbox.register("expr", gp.genGrow, pset=pset, min_=3, max_=3)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.pre_built)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)
toolbox.register("evaluate", evalCard)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("expr_mut", gp.genGrow, min_=3, max_=3)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)



CXPB = 0.5
MUTPB = 0.2
POP_SIZE = 100
NGEN = 1000
CP_FREQ = 5
EFFECT_TARGET_WEIGHT = 3.0
EFFECT_TARGET = 2

checkpoint = "checkpoint_alpha.pkl"
use_checkpoint = True

draw_plot = False
print_stats = False

if use_checkpoint:
  # A file name has been given, then load the data from the file
  with open(checkpoint, "rb") as cp_file:
    cp = pickle.load(cp_file)
  population = cp["population"]
  start_gen = cp["generation"]
  halloffame = cp["halloffame"]
  logbook = cp["logbook"]
  random.setstate(cp["rndstate"])
else:
  # Start a new evolution
  population = toolbox.population(n=POP_SIZE)
  start_gen = 0
  halloffame = tools.HallOfFame(maxsize=1)
  logbook = tools.Logbook()

  
stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("avg", numpy.mean)
stats.register("min", numpy.min)
stats.register("max", numpy.max)

for gen in tqdm(range(start_gen, NGEN)):
  population = algorithms.varAnd(population, toolbox, cxpb=CXPB, mutpb=MUTPB)

  # Evaluate the individuals with an invalid fitness
  invalid_ind = [ind for ind in population if not ind.fitness.valid]
  fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
  for ind, fit in zip(invalid_ind, fitnesses):
    ind.fitness.values = fit

  halloffame.update(population)
  record = stats.compile(population)
  logbook.record(gen=gen, evals=len(invalid_ind), **record)
  logbook.header = "gen", "evals", "avg", "min", "max"


  population = toolbox.select(population, k=len(population))

  if gen % CP_FREQ == 0:
    # Fill the dictionary using the dict(key=value[, ...]) constructor
    cp = dict(population=population, generation=gen, halloffame=halloffame, logbook=logbook, rndstate=random.getstate())
    with open("checkpoint_alpha.pkl", "wb") as cp_file:
      pickle.dump(cp, cp_file)

# eaSimpleCheckpointed(population, toolbox, 0.5, 0.2, 10, stats, halloffame=halloffame)


print(f"Generation: {gen+1}")

for i, hero in enumerate(halloffame):
  compiled = gp.compile(hero, pset)
  asJson = json.dumps(compiled, default=lambda x: x.__repr__(), indent=4)
  print(f"Hall of famer {i}/{POP_SIZE}: {asJson}")

with open('newRawCard.json', 'w') as outfile:
  json.dump(compiled, default=lambda x: x.__repr__(), indent=4, fp=outfile)

if print_stats:
  print(logbook.stream)

if draw_plot:
  gen = logbook.select("gen")
  fit_min = logbook.select("min")
  fit_avg = logbook.select("avg")
  fit_max = logbook.select("evals")

  fig, ax1 = plt.subplots()
  line1 = ax1.plot(gen, fit_min, "b-", label="Minimum Fitness")
  ax1.set_xlabel("Generation")
  ax1.set_ylabel("Fitness min", color="b")
  for tl in ax1.get_yticklabels():
      tl.set_color("b")

  ax2 = ax1.twinx()
  line2 = ax2.plot(gen, fit_avg, "r-", label="Average Fitness")
  ax2.set_ylabel("Fitness average", color="r")
  for tl in ax2.get_yticklabels():
      tl.set_color("r")


  lns = line1 + line2
  labs = [l.get_label() for l in lns]
  ax1.legend(lns, labs, loc="center right")

  plt.show()



