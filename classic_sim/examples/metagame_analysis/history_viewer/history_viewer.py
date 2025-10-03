import csv
import re

from matplotlib import pyplot as plt

import pandas as pd

display_nerfed = True
num_generations = 220

unnerfed = [("invalid_strategy", "Invalid Strategy", "#708090"),
            
            ("warrior0", "Beast Warrior", "#000000"), ("warrior1", "Health Warrior", "#FFDA91"),
            ("warrior2", "Whirlwind Warrior", "#DC143C"), ("warrior3", "Tank Warrior", "#EBA62D"), 
            ("warrior4", "Cleave Warrior", "#FEB1B1"), ("warrior5", "Hand Warrior", "#F1FF53"),
            ("warrior6", "Base Warrior", "#D72638"), ("warrior7", "Armour Warrior", "#6D2B25"),

            ("hunter0", "Slow Hunter", "#213D22"), ("hunter1", "Control Hunter", "#B5EDAE"),
            ("hunter2", "Base Hunter", "#27A127"),

            ("mage0", "Tank Mage", "#3064A4"), ("mage1", "Slow Mage", "#01165A"),
            ("mage2", "Murloc Mage", "#7171DF"), ("mage3", "Shield Mage", "#284A5A"),
            ("mage4", "Base Mage", "#90BEE2"), ("mage5", "Gnome Mage", "#9182BD"),
            ("mage6", "Control Mage", "#3D9A95"), ("mage7", "Weenie Mage", "#37405C"),
            ("mage8", "Secret Mage", "#73DDFD")]

nerfed =    [("invalid_strategy", "Invalid Strategy", "#708090"),
             
            ("warrior0", "Big Warrior", "#000000"), ("warrior1", "Health Warrior", "#FFDA91"),
            ("warrior2", "Slow Warrior", "#DC143C"), ("warrior3", "Trade Warrior", "#EBA62D"), 
            ("warrior4", "Removal Warrior", "#FEB1B1"), ("warrior5", "Mogushan Warrior", "#F1FF53"),
            ("warrior6", "Armour Warrior", "#D4A5CA"), ("warrior7", "Mystic Warrior", "#C21807"),
            ("warrior8", "Beast Warrior", "#D7C226"), ("warrior9", "Taunt Warrior", "#CAA6A3"),
            ("warrior10", "Adventurer Warrior", "#F08080"), ("warrior11", "Ping Warrior", "#92A458"),

            ("hunter0", "Taunt Hunter", "#4CAF50"), ("hunter1", "Tempo Hunter", "#AECD32"),
            ("hunter2", "Trade Hunter", "#228B22"), ("hunter3", "Health Hunter", "#006400"),
            ("hunter4", "Evergreen Hunter", "#76B041"), ("hunter5", "Divine Hunter", "#13431C"),
            ("hunter6", "Explosive Hunter", "#32CD32"),


            ("mage0", "Spellbender Mage", "#3064A4"), ("mage1", "Minion Mage", "#01165A"),
            ("mage2", "Tempo Mage", "#7A8E98"), ("mage3", "Trade Mage", "#284A5A"),
            ("mage4", "Divine Mage", "#90BEE2"), ("mage5", "Weenie Mage", "#9182BD"),
            ("mage6", "Hand Mage", "#3D9A95"), ("mage7", "Health Mage", "#37405C"),
            ]




# unnerfed_labels = [
#     "Tank Mage", "Slow Mage", "Murloc Mage", "Shield Mage", "Buff Mage",
#     "Gnome Mage", "Control Mage", "Weenie Mage",
#     "Tempo Hunter", "Control Hunter",
#     "Hand Warrior", "Value Warrior", "Control Warrior", "Tempo Warrior", "Aggro Warrior",
#     "No Cluster", "Invalid Strategy"
# ]

# nerfed_labels = [
#     "Shield Mage", "Beast Mage", "Tempo Mage", "Trade Mage", "Divine Mage",
#     "Weenie Mage", "Hand Mage",
#     "Tempo Hunter", "Aggro Hunter", "Control Hunter",
#     "Health Hunter", "Silence Hunter", "Defensive Hunter", "Board-Clear Warrior",
#     "Preserve Warrior", "Control Warrior", "Ping Warrior", "Removal Warrior",
#     "Defensive Warrior", "Chaos Warrior", "Counter-Control Warrior", "Enrage Warrior",
#     "Beast Warrior", "Value Warrior",
#     "No Cluster", "Invalid Strategy"
# ]

# mage_tones = ["#3064A4", "#01165A", "#7A8E98", "#284A5A", "#90BEE2", "#9182BD", "#3D9A95", "#37405C"]
# hunter_tones = ["#166525", "#4CAF50", "#32CD32", "#228B22", "#006400", "#76B041"]
# warrior_tones = ["#682519", "#DC143C", "#EBA62D", "#FEB1B1", "#F1FF53", "#D72638", "#C21807", "#FA8072", "#CD5C5C", "#F08080", "#FF0000"]
# invalid_tones = ["#708090"]

# unnerfed_colors = mage_tones[0:8] + hunter_tones[0:2] + warrior_tones[0:5] + invalid_tones
# nerfed_colors = mage_tones[0:7] + hunter_tones[0:6] + warrior_tones[0:11] + invalid_tones


def get_histogram(history_file):
    history = list(csv.reader(history_file))[1 if display_nerfed else 19:num_generations+1]
    histogram = []
    for generation_number, generation in enumerate(history[0:-1]):
      class_names = [name for name in history[generation_number][2:len(generation):4]]
      cluster_numbers = [(int(cluster)) for cluster in history[generation_number][3:len(generation):4]]
      combined_cluster = [class_name + str(cluster_number) if cluster_number >= 0 else "invalid_strategy" for class_name, cluster_number in zip(class_names, cluster_numbers)]
      unique_clusters = set(combined_cluster)
      generation_histogram = {unique_cluster_name: combined_cluster.count(unique_cluster_name) for unique_cluster_name in unique_clusters}
      histogram.append(generation_histogram)
    
    hist_df = pd.DataFrame(histogram)
    print(hist_df.columns)
    tuple_array = nerfed if display_nerfed else unnerfed
    tuple_keys = [t[0] for t in tuple_array]
    ordered_keys = [k for k in tuple_keys if k in hist_df.columns]
    hist_df = hist_df.reindex(columns=ordered_keys)
    hist_df.columns.name = 'cluster_key'
    return hist_df

def plot_stacked_bar_chart(histogram):
    tuple_array = nerfed if display_nerfed else unnerfed
    col_keys = list(histogram.columns)
    col_labels = []
    col_colors = []
    for k in col_keys:
        match = next((t for t in tuple_array if t[0] == k), None)
        if match:
            col_labels.append(match[1])
            col_colors.append(match[2])
        else:
            col_labels.append(k)
            col_colors.append("#cccccc")

    # Reverse columns and colors for plotting (vertical stacking)
    reversed_keys = col_keys[::-1]
    reversed_colors = col_colors[::-1]
    histogram_reversed = histogram[reversed_keys]

    histogram_reversed.plot(kind='bar', stacked=True, width=1.1, ylim=(0,30), color=reversed_colors)
    plt.xticks(ticks=[i for i in range(len(histogram))][::10], rotation=0, ha='center')
    plt.yticks(ticks=[i for i in range(0, 31)], labels=[""] * 31)
    plt.subplots_adjust(right=0.8, bottom=0.2)
    ax = plt.subplot(111)

    # Custom legend with correct labels/colors (original order)
    from matplotlib.patches import Patch
    legend_patches = [Patch(facecolor=col_colors[i], label=col_labels[i]) for i in range(len(col_labels))]
    ax.legend(handles=legend_patches, bbox_to_anchor=(1.0, 1.015), fontsize=11)
    plt.show()



with open("data/mage_nerf_metagame/agent_history.csv" if display_nerfed else "data/no_nerf_metagame/agent_history.csv") as history_file:
# with open("data/agent_history_mage_no_nerf_seed_1.csv") as history_file:
  histogram = get_histogram(history_file)
  plot_stacked_bar_chart(histogram)
