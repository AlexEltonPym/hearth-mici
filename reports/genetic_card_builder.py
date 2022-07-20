import json
import pickle
from deap import base, creator, gp, tools, algorithms

from enum import Enum

import matplotlib.pyplot as plt
import networkx as nx

import re
from collections import defaultdict, deque

import pygraphviz as pgv

from networkx.readwrite import json_graph

import random
import os
import string
import numpy
from tqdm import tqdm

import sim
import subprocess

from scoop import futures


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
  def __init__(self, amount, filter):
    self.val = {"amount": amount, "filter": filter}

  def __repr__(self):

    return self.val

class DealDamage:
  def __init__(self, method, amount, target, filter):
    self.val = {"method": method, "amount": amount, "target": target, "filter": filter}

  def __repr__(self):

    return self.val

class GainArmour:
  def __init__(self, amount, filter):
    self.val = {"amount": amount, "filter": filter}

  def __repr__(self):

    return self.val

class GiveKeyword:
  def __init__(self, method, keyword, target, filter, duration):
    self.val = {"method": method, "keyword": keyword, "target": target, "filter": filter, "duration": duration}

  def __repr__(self):

    return self.val

class RestoreHealth:
  def __init__(self, method, amount, target, filter):

    self.val = {"methode": method, "amount": amount, "target": target, "filter": filter}

  def __repr__(self):

    return self.val

class ReturnHand:
  def __init__(self, method, target, filter):
    self.val = {"method": method, "target": target, "filter": filter}

  def __repr__(self):

    return self.val

class SummonToken:
  def __init__(self, attack, defense):
    self.val = {"attack": attack, "defense": defense}

  def __repr__(self):

    return self.val

class Destroy:
  def __init__(self, method, target, filter):
    self.val = {"method": method, "target": target, "filter": filter}

  def __repr__(self):

    return self.val

class GainMana:
  def __init__(self, amount, filter):
    self.val = {"amount": amount, "filter": filter}

  def __repr__(self):

    return self.val


class EffectName:
  def __init__(self, val):
    self.val = val

  def __repr__(self):

    return str(self.val)



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
  def __init__(self, baseManaCost, baseHp, baseAttack, attributes, creature_type, effect1, effect2, effect3, effect4 ):
    self.baseManaCost = baseManaCost
    self.baseHp = baseHp
    self.baseAttack = baseAttack
    self.attributes = attributes
    self.creature_type = creature_type
    self.effect1 = effect1
    self.effect2 = effect2
    self.effect3 = effect3
    self.effect4 = effect4


  def __repr__(self):
    return {
      'baseManaCost':self.baseManaCost, 
      'baseHp':self.baseHp,
      'baseAttack':self.baseAttack, 
      'attributes': self.attributes,
      'race': self.creature_type,
      'effect1': self.effect1,
      'effect2': self.effect2,
      'effect3': self.effect3,
      'effect4': self.effect4,

    }

class Effect:
  def __init__(self, effect_name, active, set_stats, give_stats, draw_cards, deal_damage,\
                gain_armour, give_keyword, restore_health, return_hand, summon_token,\
                destroy, gain_mana ):
    self.val = {"selected_effect": effect_name, "active": active, "set_stats": set_stats,\
                "give_stats": give_stats, "draw_cards": draw_cards, "deal_damage": deal_damage,\
                "gain_armour": gain_armour, "give_keyword": give_keyword, "restore_health": restore_health,\
                "return_hand": return_hand, "summon_token": summon_token, "destroy": destroy,\
                "gain_mana": gain_mana}

  def __repr__(self):
    if(self.val["active"].__repr__() == "True"):
      sel_eff = self.val["selected_effect"].__repr__()
      return {sel_eff: self.val[sel_eff]}
    else:
      return {}

#NOTE: must return a tuple
def evalCards(indi_uncompileds, num_games):

    compileds = [toolbox.compile(expr=indi_uncompiled) for indi_uncompiled in indi_uncompileds]
    indis = [json.loads(json.dumps(compiled, default=lambda x: x.__repr__(), indent=4)) for compiled in compileds]
    indis_as_spellsource = [convert_genetic_to_spellsource(indi) for indi in indis]

    winrates = []

    if simu:
      with open('generation.json', 'w', encoding='utf-8') as outfile:
        json.dump(indis_as_spellsource, outfile, ensure_ascii=False, indent=2)

      cmd = subprocess.run(["python3", "sim.py", f"{num_games}"], capture_output=True, check=True)
      sim_results = json.loads(cmd.stdout.decode())

      winrates = [abs(0.50 - float(sim_result)) for sim_result in sim_results]
    else:
      winrates = [abs(0.50 - random.random()) for i in range(num_games)]

    attribute_complexities = [abs(1-sum([1 if active == "True" else 0 for (attribute, active) in indi["attributes"].items()])) for indi in indis]
    race_complexities = [abs(1-sum([1 if active == "True" else 0 for (race, active) in indi["race"].items()]))  for indi in indis]
    effect_complexities = [abs(1-sum([0 if indi[f"effect{i}"]=={} else 1 for i in range(1, 5)]))  for indi in indis]
    fitnesses = [winrate * 10 + attribute_complexity * 1 + race_complexity * 1 + effect_complexity * 1 for \
                  winrate, attribute_complexity, race_complexity, effect_complexity in \
                  zip(winrates, attribute_complexities, race_complexities, effect_complexities)]
    # return [(fitnesses[i], winrates[i], attribute_complexities[i], race_complexities[i], effect_complexities[i]) for i in range(len(indis_as_spellsource))]
    return [(fitnesses[i],) for i in range(len(indis_as_spellsource))]

def convert_genetic_to_spellsource(genetic_card):
  card = {"name": "Custom Card", "type": "MINION", "rarity": "COMMON", "description": "A custom card", "collectible": True, "set": "CUSTOM", "fileFormatVersion": 1}
  for race, active in genetic_card['race'].items():
    if active:
      card["race"] = race
      break
  
  card['attributes'] = {}

  for attribute in genetic_card['attributes']:
    if genetic_card['attributes'][attribute] == True:
      if attribute == 'SPELL_DAMAGE':
        card['attributes'][attribute] = 1
      else:
        card['attributes'][attribute] = True
  

  card['baseManaCost'] = genetic_card['baseManaCost']
  card['baseHp'] = genetic_card['baseHp']
  card['baseAttack'] = genetic_card['baseAttack']

  
  pcard = json.dumps(card, indent=4)
  # print(pcard)

  return card

def initial_individual(pset):
  # test_string = "Card(BaseManaCost(Integer(a7)), BaseHp(Integer(p8)), BaseAttack(Integer(l7)), Attributes(Taunt(True), Charge(False), Lifesteal(False), SpellDamage(True), DivineShield(True), Poisonous(True), Windfury(True), Frozen(True)), Creature_Type(Pirate(False), Beast(True), Elemental(False), Totem(True)), Effect(EffectName(GainArmourT), Boolean(True), SetStats(Targeted, u7, b2, Pirates, AllF, Permanently), GiveStats(Randomly, a3, a1, Beasts, Friendly, Permanently)), Effect(EffectName(RetoreHealthT), Boolean(False), SetStats(All, l0, z9, Beasts, AllF, Turn), GiveStats(Targeted, c3, x0, Beasts, AllF, Turn)), Effect(EffectName(GiveKeywordsT), Boolean(True), SetStats(Randomly, e8, e2, Pirates, AllF, Permanently), GiveStats(Targeted, k9, y1, Minions, Friendly, Turn)), Effect(EffectName(GiveStatsT), Boolean(False), SetStats(Randomly, a9, i3, Totems, AllF, Turn), GiveStats(Randomly, r6, g7, Elementals, Enemy, Turn)), Effect(EffectName(SetStatsT), Boolean(False), SetStats(Randomly, z6, u1, Elementals, AllF, Turn), GiveStats(Targeted, n2, w1, Elementals, Friendly, Permanently)), Effect(EffectName(ReturnHandT), Boolean(False), SetStats(Targeted, p7, l1, Minions, AllF, Permanently), GiveStats(Targeted, Integer(Integer(Integer(j3))), r5, Totems, Enemy, Turn)))"

  # tokens = re.split("[ \t\n\r\f\v(),]", test_string)

  # pt = gp.PrimitiveTree.from_string(test_string, pset)
  # # pt[3].value = 100


  # comp = gp.compile(pt, pset)
  # asJson = json.dumps(comp, default=lambda x: x.__repr__(), indent=4)
  # print(f"mici -> genetic: {asJson}")
  return None

# effect_text, effect_short, method, param, targets, filters, duration
pset = gp.PrimitiveSetTyped("main", [], Card)
pset.addPrimitive(Card, [BaseManaCost, BaseHp, BaseAttack, Attributes, Creature_Type, Effect, Effect, Effect, Effect], Card)
pset.addPrimitive(BaseManaCost, [Integer,], BaseManaCost)
pset.addPrimitive(BaseHp, [Integer,], BaseHp)
pset.addPrimitive(BaseAttack, [Integer,], BaseAttack)
pset.addPrimitive(Effect, [EffectName, Boolean, SetStats, GiveStats,\
                          DrawCards, DealDamage, GainArmour, GiveKeyword,\
                          RestoreHealth, ReturnHand, SummonToken, Destroy, GainMana], Effect)

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



pset.addTerminal(EffectName("set_stats"), EffectName, name="SetStatsT")
pset.addTerminal(EffectName("give_stats"), EffectName, name="GiveStatsT")
pset.addTerminal(EffectName("draw_cards"), EffectName, name="DrawCardsT")
pset.addTerminal(EffectName("deal_damage"), EffectName, name="DealDamageT")
pset.addTerminal(EffectName("gain_armour"), EffectName, name="GainArmourT")
pset.addTerminal(EffectName("give_keyword"), EffectName, name="GiveKeywordsT")
pset.addTerminal(EffectName("restore_health"), EffectName, name="RetoreHealthT")
pset.addTerminal(EffectName("return_hand"), EffectName, name="ReturnHandT")
pset.addTerminal(EffectName("summon_token"), EffectName, name="SummonTokenT")
pset.addTerminal(EffectName("destroy"), EffectName, name="DestroyT")
pset.addTerminal(EffectName("gain_armour"), EffectName, name="GainManaT")


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
pset.addTerminal(TargetHeroes("minions_or_heroes"), TargetHeroes, name="MinionsOrHeroes")
pset.addTerminal(TargetHeroes("pirates"), TargetHeroes, name="PiratesH")
pset.addTerminal(TargetHeroes("beasts"), TargetHeroes, name="BeastsH")
pset.addTerminal(TargetHeroes("elementals"), TargetHeroes, name="ElementalsH")
pset.addTerminal(TargetHeroes("totems"), TargetHeroes, name="TotemsH")

pset.addTerminal(Filter("enemy"), Filter, name="Enemy")
pset.addTerminal(Filter("friendly"), Filter, name="Friendly")
pset.addTerminal(Filter("all"), Filter, name="AllF")

pset.addTerminal(Duration("turn"), Duration, name="Turn")
pset.addTerminal(Duration("permanently"), Duration, name="Permanently")

pset.addTerminal(Keyword("taunt"), Keyword, name="TauntK")
pset.addTerminal(Keyword("charge"), Keyword, name="ChargeK")
pset.addTerminal(Keyword("lifesteal"), Keyword, name="LifestealK")
pset.addTerminal(Keyword("spell_damage"), Keyword, name="SpellDamageK")
pset.addTerminal(Keyword("divine_shield"), Keyword, name="DivineShieldK")
pset.addTerminal(Keyword("poisonous"), Keyword, name="PoisonousK")
pset.addTerminal(Keyword("windfury"), Keyword, name="WindfuryK")
pset.addTerminal(Keyword("frozen"), Keyword, name="FrozenK")




for j in string.ascii_lowercase:
  for i in range(10):
    pset.addTerminal(Integer(i), Integer, name=(j+str(i)))

  pset.addTerminal(Boolean(True), Boolean, name=(j+"True"))
  pset.addTerminal(Boolean(False), Boolean, name=(j+"False"))

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin)


toolbox = base.Toolbox()
toolbox.register("map", futures.map)
toolbox.register("pre_built", initial_individual, pset)
toolbox.register("expr", gp.genGrow, pset=pset, min_=3, max_=3)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)
toolbox.register("select", tools.selTournament, tournsize=10)
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("expr_mut", gp.genGrow, min_=3, max_=3)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)





if __name__ == "__main__":

  CXPB = 0.5 #crossbread probability
  MUTPB = 0.2 #mutation probability
  CP_FREQ = 1 #frequency of generation saved to checpoint

  POP_SIZE = 2 #total population size
  NGEN = 2 #number of generations to run
  NUM_GAMES = 2 #games to play when evaluating fitness
  simu = True #should games be simulated or random

  checkpoint = "checkpoint_alpha.pkl"
  use_checkpoint = False

  draw_plot = False
  print_stats = False
  print_hero = False

  # initial_individual(pset)


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
    invalid_individuals = [ind for ind in population if not ind.fitness.valid]
    fitnesses = evalCards(invalid_individuals, NUM_GAMES)
    for ind, fit in zip(invalid_individuals, fitnesses):
      ind.fitness.values = fit

    halloffame.update(population)
    record = stats.compile(population)
    logbook.record(gen=gen, evals=len(invalid_individuals), **record)
    logbook.header = "gen", "evals", "avg", "min", "max"


    population = toolbox.select(population, k=len(population))

    if gen % CP_FREQ == 0:
      # Fill the dictionary using the dict(key=value[, ...]) constructor
      cp = dict(population=population, generation=gen, halloffame=halloffame, logbook=logbook, rndstate=random.getstate())
      with open("checkpoint_alpha.pkl", "wb") as cp_file:
        pickle.dump(cp, cp_file)

  if print_hero:
    print(f"Generation: {gen+1}")
    

    for i, hero in enumerate(halloffame):
      compiled = gp.compile(hero, pset)
      asJson = json.dumps(compiled, default=lambda x: x.__repr__(), indent=4)
      print(f"Hall of famer {i+1}/{len(halloffame)} in {POP_SIZE} total population")
      print(f"Fitness == {hero.fitness}\n")
      print(asJson)

      nodes, edges, labels = gp.graph(hero)

      g = pgv.AGraph()
      g.add_nodes_from(nodes)
      g.add_edges_from(edges)
      g.layout(prog="dot")

      for i in nodes:
          n = g.get_node(i)
          n.attr["label"] = labels[i]

      g.draw("tree.pdf")

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

    line2 = ax1.plot(gen, fit_avg, "r-", label="Average Fitness")


    lns = line1 + line2
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc="center right")

    plt.show()



