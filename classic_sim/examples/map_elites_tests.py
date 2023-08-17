import sys
sys.path.append('../')

from map_elites import Archive
import matplotlib.pyplot as plt
from coevolution import generate_random_deck
from random import gauss
import cma
from math import dist


def fitness(val):
  return dist(val, [0, 0])


arch = Archive("Hand size", "Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40)
arch.load("metagame/mage.json")

# opts = cma.CMAOptions()
# opts.set('CMA_stds', [1,2])


es = cma.CMAEvolutionStrategy([4.5, 20.0], 0.1, {'bounds': [[1.0, 9.0], [9.0, 35.0]], 'CMA_stds': [1, 2]})

while not es.stop():
  solutions = es.ask()

  es.tell(solutions, [fitness(s) for s in solutions])
  print(es.result[0], es.result[6])
# es.disp()
# es.result_pretty()


