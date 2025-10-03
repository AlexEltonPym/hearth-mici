import sys
sys.path.append('../')

from map_elites.map_elites import Archive
import matplotlib.pyplot as plt
from examples.metaspace_generation.coevolution import generate_random_deck
from random import gauss

arch = Archive("Hand size", "Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40)
arch.load("archive/mage_vs_15_withdeck_300x5/map_archive.json")
arch.save("archive/mage_vs_15_withdeck_300x5/map_flipped_archive.json")