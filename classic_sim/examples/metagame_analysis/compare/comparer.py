from sys import path
path.append('../../../src/')
path.append('../../map_elites')
from numpy import mean
from map_elites import Archive



# for filename in glob.glob('*.json'):
for filename in ["mage", "mage_nerf", "hunter", "hunter_nerf", "warrior", "warrior_nerf"]:
  arch = Archive("Hand size", "Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40)
  arch.load(f"{filename}.json")
  # print(f"{filename} avg fit: {arch.get_average_fitness()}")
  elites = arch.get_elites()
  sorted_elites = arch.get_n_fittest(10)
  top_ten_fitness = mean([elite['fitness'] for elite in sorted_elites])

  thresholded_elites = arch.get_by_threshold_fitness(0)
  threshold_fitness = mean([elite['fitness'] for elite in thresholded_elites])

  sample = arch.get_most_fit()
  print(sample['sample'])

  print(f"{filename} {top_ten_fitness} {threshold_fitness}")
