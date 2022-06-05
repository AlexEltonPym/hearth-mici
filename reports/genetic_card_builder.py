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

class Charge:
  def __init__(self, val):
    self.val = val

  def __repr__(self):
    return self.val

class Lifesteal:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class SpellDamage:
  def __init__(self, val):
    self.val = val

  def __repr__(self):
    return self.val

class DivineShield:
  def __init__(self, val):
    self.val = val

  def __repr__(self):
    return self.val

class Poisonous:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class Windfury:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class Frozen:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class Creature_Type:
  def __init__(self, pirate, beast,elemental, totem):
    self.pirate = pirate
    self.beast = beast
    self.elemental = elemental
    self.totem = totem

  def __repr__(self):

    return {'PIRATE':self.pirate, 'BEAST': self.beast, 'ELEMENTAL':self.elemental, 'TOTEM': self.totem}

class Pirate:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class Beast:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class Elemental:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class Totem:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class Method:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class TargetMinions:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class TargetHeroes:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class Filter:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val


class Duration:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class Keyword:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class SetStats:
  def __init__(self, method, attack, defense, target, filter, duration):
    self.val = {"method": method, "attack": attack, "defense": defense, "target": target, "filter": filter, "duration": duration}

  def __repr__(self):

    return self.val

class GiveStats:
  def __init__(self, method, attack, defense, target, filter, duration):
    self.val = {"method": method, "attack": attack, "defense": defense, "target": target, "filter": filter, "duration": duration}

  def __repr__(self):

    return self.val
class DrawCards:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class DealDamage:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class GainArmour:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class GiveKeyword:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class RestoreHealth:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class ReturnHand:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class SummonToken:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class Destroy:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val

class GainMana:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return self.val


class EffectName:
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
  def __init__(self, taunt, charge, lifesteal, spell_damage, divine_shield, poisonous, windfury, frozen):
    self.taunt = taunt
    self.charge = charge
    self.lifesteal = lifesteal
    self.spell_damage = spell_damage
    self.divine_shield = divine_shield
    self.poisonous = poisonous
    self.windfury = windfury
    self.frozen = frozen

  def __repr__(self):
    return {'TAUNT':self.taunt, 'CHARGE': self.charge, 'LIFESTEAL':self.lifesteal, 'SPELL_DAMAGE': self.spell_damage,\
            'DIVINE_SHIELD': self.divine_shield, 'POISONOUS': self.poisonous, 'WINDFURY': self.windfury, 'FROZEN': self.frozen}

class Card:
  def __init__(self, baseManaCost, baseHp, baseAttack, attributes, creature_type, effect1, effect2, effect3, effect4, effect5, effect6 ):
    self.baseManaCost = baseManaCost
    self.baseHp = baseHp
    self.baseAttack = baseAttack
    self.attributes = attributes
    self.creature_type = creature_type
    self.effect1 = effect1
    self.effect2 = effect2
    self.effect3 = effect3
    self.effect4 = effect4
    self.effect5 = effect5
    self.effect6 = effect6

  def __repr__(self):
    return {
      'baseManaCost':self.baseManaCost, 
      'baseHp':self.baseHp,
      'baseAttack':self.baseAttack, 
      'attributes': self.attributes,
      'creature_type': self.creature_type,
      'effect1': self.effect1,
      'effect2': self.effect2,
      'effect3': self.effect3,
      'effect4': self.effect4,
      'effect5': self.effect5,
      'effect6': self.effect6,
    }

class Effect:
  def __init__(self, effect_name, active, set_stats, give_stats):
    self.val = {"selected_effect": effect_name, "active": active, "set_stats": set_stats, "give_stats": give_stats}

  def __repr__(self):
    if(self.val["active"].__repr__() == "True"):
      return self.val
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
  return gp.PrimitiveTree.from_string("", pset)

# effect_text, effect_short, method, param, targets, filters, duration

pset = gp.PrimitiveSetTyped("main", [], Card)
pset.addPrimitive(Card, [BaseManaCost, BaseHp, BaseAttack, Attributes, Creature_Type, Effect, Effect, Effect, Effect, Effect, Effect], Card)
pset.addPrimitive(BaseManaCost, [Integer,], BaseManaCost)
pset.addPrimitive(BaseHp, [Integer,], BaseHp)
pset.addPrimitive(BaseAttack, [Integer,], BaseAttack)
pset.addPrimitive(Effect, [EffectName, Boolean, SetStats, GiveStats], Effect)

pset.addPrimitive(SetStats, [Method, Integer, Integer, TargetMinions, Filter, Duration], SetStats)
pset.addPrimitive(GiveStats, [Method, Integer, Integer, TargetMinions, Filter, Duration], GiveStats)
pset.addPrimitive(DrawCards, [Integer, Filter], DrawCards)
pset.addPrimitive(DealDamage, [Method, Integer, TargetHeroes, Filter], DealDamage)
pset.addPrimitive(GainArmour, [Integer, Filter], GainArmour)
pset.addPrimitive(GiveKeyword, [Method, Keyword, TargetMinions, Filter, Duration], GiveKeyword)
pset.addPrimitive(RestoreHealth, [Method, Integer, TargetHeroes, Filter], RestoreHealth)
pset.addPrimitive(ReturnHand, [Method, TargetMinions, Filter], ReturnHand)
pset.addPrimitive(SummonToken, [Integer, Integer], SummonToken)
pset.addPrimitive(Destroy, [Method, TargetHeroes, Filter], Destroy)
pset.addPrimitive(GainMana, [Integer, Filter], GainMana)


pset.addPrimitive(Taunt, [Boolean], Taunt)
pset.addPrimitive(Charge, [Boolean], Charge)
pset.addPrimitive(Lifesteal, [Boolean], Lifesteal)
pset.addPrimitive(SpellDamage, [Boolean], SpellDamage)
pset.addPrimitive(DivineShield, [Boolean], DivineShield)
pset.addPrimitive(Poisonous, [Boolean], Poisonous)
pset.addPrimitive(Windfury, [Boolean], Windfury)
pset.addPrimitive(Frozen, [Boolean], Frozen)
pset.addPrimitive(Attributes, [Taunt, Charge, Lifesteal, SpellDamage, DivineShield, Poisonous, Windfury, Frozen], Attributes)


pset.addPrimitive(Creature_Type, [Pirate, Beast, Elemental, Totem], Creature_Type)
pset.addPrimitive(Pirate, [Boolean], Pirate)
pset.addPrimitive(Beast, [Boolean], Beast)
pset.addPrimitive(Elemental, [Boolean], Elemental)
pset.addPrimitive(Totem, [Boolean], Totem)


pset.addPrimitive(Integer, [Integer], Integer)
pset.addPrimitive(Boolean, [Boolean], Boolean)
pset.addPrimitive(Trigger, [Trigger], Trigger)
pset.addPrimitive(Method, [Method], Method)
pset.addPrimitive(TargetMinions, [TargetMinions], TargetMinions)
pset.addPrimitive(TargetHeroes, [TargetHeroes], TargetHeroes)
pset.addPrimitive(Filter, [Filter], Filter)
pset.addPrimitive(Duration, [Duration], Duration)
pset.addPrimitive(Keyword, [Keyword], Keyword)
pset.addPrimitive(EffectName, [EffectName], EffectName)



pset.addTerminal(EffectName("SetStats"), EffectName, name="SetStatsT")
pset.addTerminal(EffectName("GiveStats"), EffectName, name="GiveStatsT")
pset.addTerminal(EffectName("DrawCard"), EffectName, name="DrawCardsT")
pset.addTerminal(EffectName("DealDamage"), EffectName, name="DealDamageT")
pset.addTerminal(EffectName("GainArmour"), EffectName, name="GainArmourT")
pset.addTerminal(EffectName("GiveKeywords"), EffectName, name="GiveKeywordsT")
pset.addTerminal(EffectName("RestoreHealth"), EffectName, name="RetoreHealthT")
pset.addTerminal(EffectName("ReturnHand"), EffectName, name="ReturnHandT")
pset.addTerminal(EffectName("SummonToken"), EffectName, name="SummonTokenT")
pset.addTerminal(EffectName("Destory"), EffectName, name="DestroyT")
pset.addTerminal(EffectName("GainMana"), EffectName, name="GainManaT")


pset.addTerminal(Method("randomly"), Method, name="Randomly")
pset.addTerminal(Method("targeted"), Method, name="Targeted")
pset.addTerminal(Method("all"), Method, name="All")

pset.addTerminal(TargetMinions("minions"), TargetMinions, name="Minions")
pset.addTerminal(TargetMinions("pirates"), TargetMinions, name="Pirates")
pset.addTerminal(TargetMinions("beasts"), TargetMinions, name="Beasts")
pset.addTerminal(TargetMinions("elementals"), TargetMinions, name="Elementals")
pset.addTerminal(TargetMinions("totems"), TargetMinions, name="Totems")

pset.addTerminal(TargetHeroes("minions"), TargetHeroes, name="MinionsH")
pset.addTerminal(TargetHeroes("heroes"), TargetHeroes, name="Heroes")
pset.addTerminal(TargetHeroes("minions_or_heroes"), TargetHeroes, name="Minions_Or_Heroes")
pset.addTerminal(TargetHeroes("pirates"), TargetHeroes, name="PiratesH")
pset.addTerminal(TargetHeroes("beasts"), TargetHeroes, name="BeastsH")
pset.addTerminal(TargetHeroes("elementals"), TargetHeroes, name="ElementalsH")
pset.addTerminal(TargetHeroes("totems"), TargetHeroes, name="TotemsH")

pset.addTerminal(Filter("enemy"), Filter, name="Enemy")
pset.addTerminal(Filter("firendly"), Filter, name="Friendly")
pset.addTerminal(Filter("all"), Filter, name="AllF")

pset.addTerminal(Duration("turn"), Duration, name="Turn")
pset.addTerminal(Duration("permanently"), Duration, name="Permanently")

pset.addTerminal(Keyword("taunt"), Keyword, name="TauntK")
pset.addTerminal(Keyword("charge"), Keyword, name="ChargeK")
pset.addTerminal(Keyword("lifesteal"), Keyword, name="LifestealK")
pset.addTerminal(Keyword("spell_damage"), Keyword, name="Spell DamageK")
pset.addTerminal(Keyword("divine_shield"), Keyword, name="Divine ShieldK")
pset.addTerminal(Keyword("poisonous"), Keyword, name="PoisonousK")
pset.addTerminal(Keyword("windfury"), Keyword, name="WindfuryK")
pset.addTerminal(Keyword("frozen"), Keyword, name="FrozenK")


pset.addTerminal(Boolean(True), Boolean, name="True")
pset.addTerminal(Boolean(False), Boolean, name="False")

for i in range(10):
  pset.addTerminal(Integer(i), Integer, name=str(i))

creator.create("FitnessMax", base.Fitness, weights=(-1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
# toolbox.register("pre_built", initial_individual, pset)
toolbox.register("expr", gp.genGrow, pset=pset, min_=3, max_=3)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
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
NGEN = 10
CP_FREQ = 5
EFFECT_TARGET_WEIGHT = 3.0
EFFECT_TARGET = 2

checkpoint = "checkpoint_alpha.pkl"
use_checkpoint = False

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



