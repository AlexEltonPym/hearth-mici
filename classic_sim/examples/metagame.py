from map_elites import Archive
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from coevolution import generate_random_deck
from random import gauss, randint, uniform
from copy import deepcopy
class MetaArchive():
  def __init__(self, x_title, y_title, x_range, y_range, num_buckets, archive_names, num_agents, agent_profile):
    self.x_title = x_title
    self.y_title = y_title
    self.x_range = x_range
    self.y_range = y_range
    self.num_buckets = num_buckets
    self.archive_names = archive_names
    self.num_archives = len(archive_names)
    self.num_agents = num_agents    
    self.agent_profile = agent_profile
    self.archives = [(Archive(self.x_title, self.y_title, self.x_range, self.y_range, self.num_buckets, archive_name)) for archive_name in self.archive_names]
  def setup_agents(self):
    self.agents = []
    for agent_number in range(self.num_agents):
      parent_archive_index = int(agent_number/self.num_agents * self.num_archives)
      x_min, x_max, y_min, y_max = self.archives[parent_archive_index].get_range()
      self.agents.append(Agent(agent_number, uniform(x_min, x_max), uniform(y_min, y_max), self.agent_profile, self.archives[parent_archive_index]))

  def load(self, archiveA, archiveB, archiveC):
    self.archives[0].load(archiveA)
    self.archives[1].load(archiveB)
    self.archives[2].load(archiveC)
    self.setup_agents()

  def display(self, fig, axis):
    fig.set_figheight(3.5)
    fig.set_figwidth(12)
    
    for (archive, current_ax) in zip(self.archives, axis):
      x, y, Zm = archive.get_graph()
      im = current_ax.pcolormesh(x, y, Zm.T[:-1, :-1], vmin=-30, vmax=30, shading='flat')
      current_ax.set_xlabel(archive.x_title)
      current_ax.set_ylabel(archive.y_title)

      current_ax.set_title(archive.archive_name.capitalize())
      current_ax.set_xlim(archive.x_min, archive.x_max)
      current_ax.set_ylim(archive.y_min, archive.y_max)
      x0,x1 = current_ax.get_xlim()
      y0,y1 = current_ax.get_ylim()
      current_ax.set_aspect((x1-x0)/(y1-y0))

      agent_x = [agent.x for agent in self.agents if agent.parent_archive == archive]
      agent_y = [agent.y for agent in self.agents if agent.parent_archive == archive]
      current_ax.scatter(agent_x, agent_y, c='red', s=4)
    return im


class Agent():
  def __init__(self, agent_number, x, y, agent_profile, parent_archive):
    self.agent_number = agent_number
    self.agent_profile = agent_profile
    self.parent_archive = parent_archive
    self.x = x
    self.y = y

  def __repr__(self):
    return f"\nAgent {self.agent_number}: {self.parent_archive.archive_name}({self.x:.2f},{self.y:.2f}) = {self.agent_profile}"

def animate(frame_id, *frags):
  meta_archives, fig, axis = frags
  for ax in axis:
    ax.clear()
  im = meta_archives[frame_id].display(fig, axis)

  if frame_id == 0:
    cbar = fig.colorbar(im, ax=axis.ravel().tolist(), shrink=0.9, pad=0.05, fraction=0.05)


def init_animation(*frags):
  pass

def meta_evaluation():
  agent_profile = [1,1,1,1,1,1]
  meta_archive = MetaArchive(x_title="Hand size", y_title="Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40, archive_names=["mage", "hunter", "warrior"], num_agents=300, agent_profile=agent_profile)
  meta_archive.load("archive/mage_vs_15_withdeck_300x5/map_flipped_archive.json", 
                    "archive/hunter_vs_15_both_300_x_5_glitch/map_archive.json", 
                    "archive/warrior_vs_15_both_300_x_5/generation301_flipped_archive.json")
  meta_archives = []
  for i in range(10):
    for agent in meta_archive.agents:
      agent.x+=uniform(-1,1)
      agent.y+=uniform(-1,1)
    meta_archives.append(deepcopy(meta_archive))

  fig, axis = plt.subplots(1, 3, sharey=False, sharex=True)
  plt.tight_layout()

  ani = FuncAnimation(fig, animate, init_func=init_animation, frames=10, interval=200, repeat=False, fargs=[meta_archives, fig, axis])

  plt.show()
if __name__ == "__main__":
  meta_evaluation()