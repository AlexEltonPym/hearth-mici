import plotly.graph_objects as go
import csv
base_labels = ["invalid strategy", "no cluster", "cluster1", "cluster2",	"cluster3",	"cluster4",	"cluster5",	"cluster6",	"cluster7",	"cluster8",	"cluster9",	"cluster10", "cluster11"]
base_colors = ['#37ab65', '#3df735', '#ad6d70', '#ec2504', '#8c0b90', '#c0e4ff', '#27b502', '#7c60a8', '#cf95d7', '#cdaaee', '#67cdff', '#cd67ff', '#ffcd67']
num_generations = 100


def stretch(n, start1, stop1, start2, stop2):
  return (n - start1) / (stop1 - start1) * (stop2 - start2) + start2


class AdjacencyMatix():
  def __init__(self):
    self.entries = []
  
  def add_entry(self, from_cluster, to_cluster):
    # for entry in self.entries:
      # if entry['from_cluster'] == from_cluster and entry['to_cluster'] == to_cluster:
      #   entry['value'] += 1
      #   return
    new_entry = {"from_cluster": from_cluster, "to_cluster": to_cluster, "value": 1}
    self.entries.append(new_entry)

  def get_entries(self):
    source = [entry['from_cluster'] for entry in self.entries]
    target = [entry['to_cluster'] for entry in self.entries]
    value = [entry['value'] for entry in self.entries]
    return source, target, value

def get_nodes(history_file):
    history = list(csv.reader(history_file))[1:num_generations+1]

    adjacency_matrix = AdjacencyMatix()

    for generation_number, generation in enumerate(history[0:-1]):
      current_generation_clusters = [(int(cluster)+1)+(generation_number*100) for cluster in history[generation_number][3:len(generation):4]]
      next_generation_clusters = [(int(cluster)+1)+((generation_number+1)*100) for cluster in history[generation_number+1][3:len(generation):4]]
      for current, next in zip(current_generation_clusters, next_generation_clusters):
        adjacency_matrix.add_entry(current, next)

    source, target, value = adjacency_matrix.get_entries()

    return source, target, value

def plot_sankey(source, target, value):

    labels = [""] * num_generations*101
    for generation_number in range(num_generations):
      for index, label in enumerate(base_labels):
        labels[index+generation_number*100] = label + f" - {generation_number}"

    colors = ["#ffffff"] * num_generations*101
    for generation_number in range(num_generations):
      for index, base_color in enumerate(base_colors):
        colors[index+generation_number*100] = base_color
    
    # x_positions = [0] * num_generations*101
    # y_positions = [0] * num_generations*101
    # for generation_number in range(num_generations):
    #   for y in range(len(base_labels)):
    #     x_positions[y+generation_number*100] = stretch(generation_number/(num_generations-1), 0, 1, 0.1, 0.9)
    #     y_positions[y+generation_number*100] = stretch(y/len(base_labels), 0, 1, 0.1, 0.9)
    # print(x_positions[100])
    # print(y_positions[100])
    # print(labels[100])
    nodes = dict(
        pad = 10,
        thickness = 5,
        line = dict(color = "black", width = 0.5),
        label = labels,
        color = colors,
        # y = y_positions,
        # x = x_positions
      )


    fig = go.Figure(data=[go.Sankey(
      arrangement = "freeform",
      node = nodes,
      link = dict(
        source = source,
        target = target,
        value = value
    ))])

    fig.update_layout(title_text="Basic Sankey Diagram", font_size=10)
    fig.show()

with open("example_history.csv") as history_file:
  source, target, value = get_nodes(history_file)
  plot_sankey(source, target, value)


