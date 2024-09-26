from random import uniform, gauss, shuffle, choice, random, randint
import matplotlib.pyplot as plt
import json
from map_elites import Archive
import numpy as np

empty_archive = Archive("Hand size", "Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40)
empty_archive.load("archive/mage_vs_15gauntlet/map_archive.json")

print(f"population size: {len(empty_archive.get_elites())}")
print(f"Unique population size: {len(empty_archive.get_elites(unique_only=True))}")

empty_archive.display("colorhash")
