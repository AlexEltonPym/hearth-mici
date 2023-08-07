from map_elites import Archive
import matplotlib.pyplot as plt
from coevolution import generate_random_deck
from random import gauss

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

    self.setup_archives_and_agents()
  def setup_archives_and_agents(self):
    self.archives = [(Archive(self.x_title, self.y_title, self.x_range, self.y_range, self.num_buckets, archive_name)) for archive_name in self.archive_names]
  
    self.agents = []
    for agent_number in range(self.num_agents):
      parent_archive_index = int(agent_number/self.num_agents * self.num_archives)
      self.agents.append(Agent(agent_number, self.agent_profile, self.archives[parent_archive_index]))

  def display(self):

    f, axis = plt.subplots(1, 3, sharey=True, sharex=True)
    for (archive, current_ax) in zip(self.archives, axis):
      print(current_ax)
      archive.display(fig=f, ax=current_ax, dont_show=True)
      f.set_figheight(4)
      f.set_figwidth(14)
    plt.tight_layout()

    plt.show()

class Agent():
  def __init__(self, agent_number, agent_profile, parent_archive):
    self.agent_number = agent_number
    self.agent_profile = agent_profile
    self.parent_archive = parent_archive


def meta_evaluation():
  agent_profile = [1,1,1,1,1,1]
  meta_archive = MetaArchive(x_title="Hand size", y_title="Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40, archive_names=["mage", "warrior", "hunter"], num_agents=100, agent_profile=agent_profile)
  meta_archive.archives[0].load("archive/mage_vs_15_withdeck_300x5/map_archive.json")
  meta_archive.archives[0].load("archive/hunter_vs_15_both_300_x_5_glitch/map_archive.json")
  meta_archive.archives[0].load("archive/warrior_vs_15_both_300_x_5/map_archive.json")

  meta_archive.display()

if __name__ == "__main__":
  meta_evaluation()