from map_elites import Archive
import numpy as np
from sklearn.manifold import TSNE
from sklearn.cluster import HDBSCAN, KMeans

import matplotlib.pyplot as plt
from matplotlib import cm, colors, colormaps, widgets, pylab

from statistics import mean, stdev
# import sys
# sys.path.append('../')
from enums import CardSets
from card_sets import build_pool


class PlotController:
  index = 0
  #  ("Mage", 156, 180), ("Hunter", 180, 204),
  selections = [("All", 0, 228), ("Clusters", 0, 2), ("Strategy", 2, 26), ("Basics", 26, 69), ("Commons", 69, 109), ("Rares", 109, 145), ("Epics", 145, 156), ("Warrior", 204, 228)]
  
  def __init__(self, points, title, color_values, subtitles, color_maps, cluster_data, important_groups, current_cluster):
    self.points = points
    self.title = title
    self.color_values = color_values
    self.subtitles = subtitles
    self.color_maps = color_maps
    self.cluster_data = cluster_data
    self.important_groups = important_groups
    self.current_cluster = current_cluster

    if self.current_cluster < 0 and self.index == 0: self.index = 1
    selection_title, fro, to = self.selections[self.index]
    plot_2d(self.points, self.title, selection_title, self.color_values[fro:to], self.subtitles[fro:to], self.color_maps[fro:to], self.cluster_data, self.important_groups, self.current_cluster, self)

  def next(self, event):
    self.index = (self.index+1) % len(self.selections)
    if self.current_cluster < 0 and self.index == 0: self.index = 1

    plt.close()

    selection_title, fro, to = self.selections[self.index]
    plot_2d(self.points, self.title, selection_title, self.color_values[fro:to], self.subtitles[fro:to], self.color_maps[fro:to], self.cluster_data,self.important_groups, self.current_cluster, self)

  def prev(self, event):
    self.index = (self.index-1) % len(self.selections)
    if self.current_cluster < 0 and self.index == 0: self.index = len(self.selections)-1

    plt.close()
    selection_title, fro, to = self.selections[self.index]
    plot_2d(self.points, self.title, selection_title, self.color_values[fro:to], self.subtitles[fro:to], self.color_maps[fro:to],  self.cluster_data, self.important_groups,self.current_cluster, self)

def check_group(text, groups):
  for group_text, group_zscore in groups:
    if text == group_text: return True
  return text == "hdbscan" or text == "kmeans"

def get_zscore(text, groups):
  for group_text, group_zscore in groups:
    if text == group_text: return group_zscore
  return 0

def plot_2d(points, title, selection_title, color_values, subtitles, color_maps, cluster_data, important_groups, current_cluster, callback):
  print(f"{current_cluster=}")
  if current_cluster > -1:
    color_values = [color_value for color_value, subtitle in zip(color_values, subtitles) if check_group(subtitle, important_groups[current_cluster])]
    color_maps = [color_maps for color_maps, subtitle in zip(color_maps, subtitles) if check_group(subtitle, important_groups[current_cluster])]
    subtitles = [f"{subtitle}\n({get_zscore(subtitle, important_groups[current_cluster]):+.2f})" for subtitle in subtitles if check_group(subtitle, important_groups[current_cluster])]
  


  w, h = {2: (2, 1), 11: (4, 3), 24: (6, 4), 40: (8, 5), 43: (9, 5), 36: (9, 4)}.get(len(color_values), (6, 4))
  fig, axes = plt.subplots(h, w, facecolor="white", constrained_layout=False, squeeze=False)
  fig.suptitle(selection_title, size=12)
  fig = pylab.gcf()
  fig.canvas.manager.set_window_title(title)
  # axes = np.array(axes)

  axprev = fig.add_axes([0.90, 0.95, 0.05, 0.05])
  axnext = fig.add_axes([0.95, 0.95, 0.05, 0.05])
  bnext = widgets.Button(axnext, '→')
  bnext.on_clicked(callback.next)
  bprev = widgets.Button(axprev, '←')
  bprev.on_clicked(callback.prev)

  unfiltered_x, unfiltered_y = points.T
  for index, (ax, color_value, subtitle, color_map) in enumerate(zip(axes.flatten(), color_values, subtitles, color_maps)):

      cmap = colormaps[color_map]
      norm = colors.Normalize(min(color_value), max(color_value))
      color_value = cmap(color_value/2) if color_map == "twilight" else cmap(norm(color_value)) 
      
      # a = [0 if cluster != current_cluster else 0.9 for cluster in cluster_data]
      x = [_x for _x, cluster in zip(unfiltered_x, cluster_data) if True]
      y = [_y for _y, cluster in zip(unfiltered_y, cluster_data) if True]

      ax.scatter(x, y, c=color_value, s=14, alpha=0.75, edgecolors=None, marker='.')
      ax.set_title(subtitle, size=10)
      ax.set_aspect('equal')
      ax.tick_params(axis='both',which='both', bottom=False, top=False, labelbottom=False, left=False, right=False, labeltop=False, labelleft=False, labelright=False) 
      if color_map == "viridis":
        fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, use_gridspec=True, cax=None, fraction=0.046, pad=0.04)

  [ax.remove() if ax.title.get_text() == "" else None for ax in axes.flatten()]



  plt.tight_layout()
  plt.subplots_adjust(left=0.1,
                    bottom=0.1, 
                    right=0.9, 
                    top=0.9, 
                    wspace=0.6, 
                    hspace=0.3)

  mng = plt.get_current_fig_manager()
  mng.resize(3020, 1640)
  plt.show()


def get_pool():
  pool = build_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE, CardSets.CLASSIC_HUNTER, CardSets.CLASSIC_WARRIOR], None)
  pool = [card.name for card in pool]
  return pool

def bags_from_decks(decks):
  pool = get_pool()

  bags = []
  for deck in decks:
    bag = np.zeros(len(pool))
    for card in deck:
      index = pool.index(card)
      bag[index] = 1
    bags.append(bag)
  return bags

def view_archive(class_name, plot_cluster_only, plot_strat, plot_deck,plot_cluster, seed):
  supertitle = f"{class_name} tSNE"
  map_archive = Archive("Hand size", "Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40)

  map_archive.load(f'metagame/{class_name}.json')
  elites = map_archive.get_elites(unique_only=True)
  elites = sorted(elites, key=lambda elite: elite['fitness'])
  x = np.array([elite['sample'][0] for elite in elites])
  decks = np.array([elite['sample'][1] for elite in elites])

  bags = bags_from_decks(decks)

  x = np.array([np.append(strat, deck) for (strat, deck) in zip(x, bags)])
  
  hdbscan_clusters = HDBSCAN(min_cluster_size=10).fit(x).labels_
  kmeans_clusters = KMeans(n_clusters=12, random_state=seed, n_init="auto").fit(x).labels_


  fitness = [elite['fitness'] for elite in elites]
  x_value = [elite['x_value'] for elite in elites]
  y_value = [elite['y_value'] for elite in elites]


  colors = [hdbscan_clusters, kmeans_clusters, fitness, x_value, y_value]
  samples = x.T
  colors.extend(samples)

  titles = ["hdbscan", "kmeans", "fitness (behavior)", "hand size (behavior)", "turns (behavior)"]#+[f"Component {n}" for n in range(21)]
  heuristics = ["pass early", "hp", "enemy hp", "health diff", "armor diff", "minions diff", "minion attack diff", "minion health diff", "taunt minions", "enemy taunt minions", "divine shield minions ", "enemy divine shield minions", "lifesteal minions", "enemy lifesteal minions", "spell damage minions", "enemy spell damage minions", "other attributes", "enemy other attributes", "hand diff", "library diff", "secrets diff"]
  cards = get_pool()
  titles.extend(heuristics)
  titles.extend(cards)

  color_maps = ["tab20"] * 2 + ["viridis"] * 24 + ["twilight"] * 202


  X_embedded = TSNE(n_components=2, learning_rate='auto', init='pca', perplexity=30, random_state=seed).fit_transform(x)

  important_groups = []
  for checking_cluster in range(max(hdbscan_clusters)):
    cluster_important_groups = []
    print(f"\nCluster {checking_cluster} defined by:")
    for signal, group in zip(samples, titles[5:]):
      m = mean(signal)
      d = stdev(signal)
      running_average = 0
      running_count = 0
      for elite_signal, cluster in zip(signal, hdbscan_clusters):
        if cluster == checking_cluster:
          running_average += elite_signal
          running_count += 1
      running_average /= running_count
      zscore = (running_average-m)/d
      if zscore >= 1 and zscore < 2:
        print(f"+{group}")
        cluster_important_groups.append((group, zscore))
      elif zscore >=2:
        print(f"++{group}")
        cluster_important_groups.append((group, zscore))
      elif zscore <=-1 and zscore > -2:
        print(f"-{group}")
        cluster_important_groups.append((group, zscore))
      elif zscore <= -2:
        print(f"--{group}")
        cluster_important_groups.append((group, zscore))
    important_groups.append(cluster_important_groups)



  PlotController(X_embedded, supertitle, colors, titles, color_maps, hdbscan_clusters, important_groups, plot_cluster)


if __name__ == '__main__':

  plot_cluster_only = False
  plot_strat = True
  plot_deck = True
  plot_cluster = 12
  class_name = "warrior"
  seed = 0
  
  view_archive(class_name, plot_cluster_only, plot_strat, plot_deck, plot_cluster, seed)
