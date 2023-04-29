from random import uniform, gauss, shuffle, choice, random, randint
import matplotlib.pyplot as plt
import json
from map_elites import Archive
import numpy as np


empty_archive = Archive("Hand size", "Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40)
empty_archive.load("archive/mage_with_deck_vs_handmade/map_archive.json")
population = [elite['sample'] for elite in empty_archive.get_elites()]
population = [tuple(policy + deck) for (policy, deck) in population]
print(f"population size: {len(population)}")
uniques = list(set(population))
print(f"Unique population size: {len(uniques)}")


empty_archive.display("colorhash")
