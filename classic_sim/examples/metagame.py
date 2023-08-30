from map_elites import Archive
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Ellipse

from coevolution import generate_random_deck
from random import gauss, randint, uniform, shuffle
from copy import deepcopy

import cma


from statistics import mean
from numpy.random import choice as choice_with_replacement

import json
from atomicwrites import atomic_write


try:
  from mpi4py import MPI
except ModuleNotFoundError:
  pass

def stretch(n, start1, stop1, start2, stop2):
  return (n - start1) / (stop1 - start1) * (stop2 - start2) + start2

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
      self.agents.append(Agent(agent_number, uniform(x_min, x_max-0.4), uniform(y_min, y_max-1.3), self.agent_profile, self.archives[parent_archive_index]))
  def load(self, archiveA, archiveB, archiveC):
    self.archives[0].load(archiveA)
    self.archives[1].load(archiveB)
    self.archives[2].load(archiveC)
    self.setup_agents()

  def display(self, fig, axis, fittest_agent):
    fig.set_figheight(3.5)
    fig.set_figwidth(12)
    
    for (archive, current_ax) in zip(self.archives, axis):
      x, y, Zm = archive.get_graph()
      
      im = current_ax.pcolormesh(x, y, Zm.T[:-1, :-1], vmin=-30, vmax=30, shading='flat')
      current_ax.set_xlabel(archive.x_title)
      current_ax.set_ylabel(archive.y_title)

      current_ax.set_title(archive.archive_name.capitalize())
      trim_x, trim_y = archive.transform_from_real_space_to_scale(1, 1)
      current_ax.set_xlim(archive.x_min, archive.x_max-trim_x)
      current_ax.set_ylim(archive.y_min, archive.y_max-trim_y)
      x0,x1 = current_ax.get_xlim()
      y0,y1 = current_ax.get_ylim()
      current_ax.set_aspect((x1-x0)/(y1-y0))

      agents_in_this_archive = [agent for agent in self.agents if agent.parent_archive == archive]

      agent_x = [agent.x for agent in agents_in_this_archive]
      agent_y = [agent.y for agent in agents_in_this_archive]
      current_ax.scatter(agent_x, agent_y, c='red', s=4)

      draw_condifence_ellipses(current_ax, agents_in_this_archive, fittest_agent, False)
    return im

def draw_condifence_ellipses(ax, agents, fittest_agent, highlight_fittest):
  draw_confidence(ax, agents, fittest_agent, 1, 'red', 'black', 0.2, '--', highlight_fittest)
  # draw_confidence(ax, agents, fittest_agent, 2, 'red', 'black', 0.1, '--', highlight_fittest)
  # draw_confidence(ax, agents, fittest_agent, 3, 'red', 'black', 0.1, '--', highlight_fittest)

def draw_confidence(ax, agents, fittest_agent, n_stds, facecolor, edgecolor, alpha, linestyle, highlight_fittest):
  for agent in agents:
    if highlight_fittest and agent.agent_number == fittest_agent.agent_number:
      ellipse = Ellipse((agent.x, agent.y), width=agent.x_deviation*n_stds, height=agent.y_deviation*n_stds, facecolor='blue', alpha=0.5, edgecolor=edgecolor, linestyle=linestyle)
    else:
      ellipse = Ellipse((agent.x, agent.y), width=agent.x_deviation*n_stds, height=agent.y_deviation*n_stds, facecolor=facecolor, alpha=alpha, edgecolor=edgecolor, linestyle=linestyle)
    ax.add_patch(ellipse)

class Agent():
  def __init__(self, agent_number, x, y, agent_profile, parent_archive):
    self.agent_number = agent_number
    self.agent_profile = agent_profile
    self.parent_archive = parent_archive
    self.x = x
    self.y = y
    self.x_deviation, self.y_deviation = self.parent_archive.transform_from_real_space_to_scale(1, 1)

    x_min, x_max, y_min, y_max = self.parent_archive.get_range()
    self.es = cma.CMAEvolutionStrategy(
    x0=[self.x, self.y],
    sigma0=1,
    inopts={
        'bounds': [[x_min, y_min], [x_max-0.4, y_max-1.3]],
        'CMA_stds': [self.x_deviation, self.y_deviation],
        # 'popsize': 10,
        'CMA_cmean': 1,
        'maxiter': 1000, #we have overridden this with max_iterations
        # 'minstd': self.parent_archive.transform_from_real_space_to_scale(1, 1),
        # 'maxstd': self.parent_archive.transform_from_real_space_to_scale(2, 2),
        'verbose': 10, 'verb_disp': 1,

    }
)


  def __repr__(self):
    return f"\nAgent {self.agent_number}: {self.parent_archive.archive_name}({self.x:.2f},{self.y:.2f}) = {self.agent_profile}"

  def get_sample(self):
    sample_x, sample_y = gauss(self.x, self.x_deviation), gauss(self.y, self.y_deviation)
    sample_elite = self.parent_archive.vals_to_entry(sample_x, sample_y, missing_behaviour="closest")
    return sample_elite['fitness'], sample_elite['sample']

  def get_sample_average_fitness(self, num_samples):
    fitnesses = []
    for i in range(num_samples):
      sample_fitness, sample_value = self.get_sample()
      if sample_fitness != None:
        fitnesses.append(sample_fitness)
    if len(fitnesses) > 0:
      return stretch(mean(fitnesses), -30, 30, 1, 0)
    else:
      return -100


class Memoizer():
  def __init__(self, filename):
    self.filename = filename
    self.cache = {}
    self.load()
  def load(self):
    try:
      with open(self.filename, 'r') as f:
        self.cache = json.load(f)
      print(f"Loaded memo cache with {len(self.cache)} entries")
    except FileNotFoundError:
      return
  def memoize_all(self, results):
    for match, value in results:
      key = self.match_to_key(match)
      self.cache[key] = value
    with atomic_write(self.filename, overwrite=True) as f:
      json.dump(self.cache, f)

  def fetch(self, match):
    key = self.match_to_key(match)
    return self.cache[key]
  def remembers(self, match):
    key = self.match_to_key(match)
    return key in self.cache
  def match_to_key(self, match):
    player, opponent = match
    player_key = f"{player[0][0]}_{player[1]['x_index']}_{player[1]['y_index']}"
    opponent_key = f"{opponent[0][0]}_{opponent[1]['x_index']}_{opponent[1]['y_index']}"
    return f"{player_key}_v_{opponent_key}" if player_key < opponent_key else f"{opponent_key}_v_{player_key}"


def animate(frame_id, *frags):
  meta_archives, fig, axis, repeating_animation = frags
  for ax in axis:
    ax.clear()
  
  agent_fitnesses = []
  for agent in meta_archives[frame_id].agents:
    agent_result = agent.get_sample_average_fitness(10)
    agent_fitnesses.append((agent, agent_result))
  
  fittest = max(agent_fitnesses, key=lambda x: x[1])
  fittest_agent, fittest_agent_fitness = fittest

  im = meta_archives[frame_id].display(fig, axis, fittest_agent)

  if frame_id == 0 and not repeating_animation:
    cbar = fig.colorbar(im, ax=axis.ravel().tolist(), shrink=0.9, pad=0.05, fraction=0.05)


def init_animation(*frags):
  pass

def evaluate_fitness(agent, sample):
  sample_x, sample_y = sample
  sample_elite = agent.parent_archive.vals_to_entry(sample_x, sample_y, missing_behaviour="none")
  fitness = -1000 if sample_elite['fitness'] == None else sample_elite['fitness']
  return stretch(fitness, -30, 30, 1, 0)

#Returns all samples from each agent that need evaluating, including empty samples
def get_contestants(meta_archive):
  contestants = []
  for agent in meta_archive.agents:
    agent_in_ocean = agent.parent_archive.vals_to_entry(agent.x, agent.y, missing_behaviour="none")['fitness'] == None
    if(not agent.es.stop() or agent_in_ocean or agent.es.sigma > 1): #ignore_list=['tolfun', 'tolflatfitness']
      solutions = agent.es.ask()
      for sample_x, sample_y in solutions:
        sample_elite = agent.parent_archive.vals_to_entry(sample_x, sample_y, missing_behaviour="none")
        contestants.append((agent.parent_archive.archive_name, sample_elite))
  
  return contestants

def get_matchups(contestants, num_matchups_per_evaluation):
  matchups = []
  participants = []
  for contestant in contestants:
    if contestant not in participants and contestant[1]['fitness'] != None:
      participants.append(contestant)

  shuffle(participants)

  for index, participant in enumerate(participants):
    for offset in range(1, num_matchups_per_evaluation//2+1):
      matchups.append((participant, participants[(index+offset)%len(participants)]))

  return matchups

def compile_fitnesses(num_matchups_per_evaluation, contestants, matchups, match_results):
  fitnesses = []
  for contestant_parent, contestant_elite in contestants:
    if contestant_elite['sample'] == None:
      fitnesses.append(-1000)
    else:
      running_average = 0
      for ((player_parent, player), (opponent_parent, opponent)), (player_result, opponent_result) in zip(matchups, match_results):
        if player == contestant_elite:
          running_average += player_result/num_matchups_per_evaluation
        elif opponent == contestant_elite:
          running_average += opponent_result/num_matchups_per_evaluation
      fitnesses.append(running_average)
  return fitnesses


def train_agents_one_step(meta_archive):
  number_of_agents_finished = 0
  for agent in meta_archive.agents:
    agent_in_ocean = agent.parent_archive.vals_to_entry(agent.x, agent.y, missing_behaviour="none")['fitness'] == None
    if(not agent.es.stop() or agent_in_ocean or agent.es.sigma > 1): #ignore_list=['tolfun', 'tolflatfitness']
      solutions = agent.es.ask()



      agent.es.tell(solutions, [evaluate_fitness(agent, s) for s in solutions])
      agent.es.manage_plateaus(2, 0.99)

      if(agent.agent_number == 0):
        agent.es.disp()
      agent.x, agent.y = agent.es.result[0]
      agent.x_deviation, agent.y_deviation = agent.es.result[6]
    else:
      print(agent.es.stop())
      number_of_agents_finished+=1
  print(f"Done {number_of_agents_finished}/{len(meta_archive.agents)}")
  return number_of_agents_finished == len(meta_archive.agents)

def run_agent_training(meta_archive, max_iterations):
  meta_archives = []
  done_training = False
  iter_num = 0
  while not done_training and iter_num < max_iterations:
    print(f"Starting iteration {iter_num}")
    done_training = train_agents_one_step(meta_archive)
    meta_archives.append(deepcopy(meta_archive))
    iter_num += 1
  return meta_archives

def render_animation(meta_archives):
  fig, axis = plt.subplots(1, 3, sharey=False, sharex=True)
  plt.tight_layout()
  repeating_animation = True
  ani = FuncAnimation(fig, animate, init_func=init_animation, frames=len(meta_archives), interval=20, repeat=repeating_animation, repeat_delay=10000,fargs=[meta_archives, fig, axis, repeating_animation])
  ani.save("metagame/tourny.gif")
  # plt.show()


def pprint_matchup(matchup):
  player, opponent = matchup
  print(f"{player[0], player[1]['x_index'], player[1]['y_index'], player[1]['fitness']} vs {opponent[0], opponent[1]['x_index'], opponent[1]['y_index'], opponent[1]['fitness']}")


def meta_evaluation():
  using_mpi = False
  max_iterations = 2
  num_agents = 30
  num_matchups_per_evaluation = 6 #must be even
  if num_matchups_per_evaluation % 2 != 0:
    raise Exception("num_matchups_per_evaluation must be even")

  if using_mpi:
    comm = MPI.COMM_WORLD
    num_cores = comm.Get_size()
    rank = comm.Get_rank()
  else:
    rank = 0
    num_cores = 1

  if rank == 0:
    agent_profile = [1,1,1,1,1,1]
    meta_archive = MetaArchive(x_title="Hand size", y_title="Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40, archive_names=["mage", "hunter", "warrior"], num_agents=num_agents, agent_profile=agent_profile)
    meta_archive.load("metagame/mage.json", "metagame/hunter.json", "metagame/warrior.json")
    memoizer = Memoizer("metagame/memoizer.json")
    contestants = get_contestants(meta_archive)
    matchups = get_matchups(contestants, num_matchups_per_evaluation)
    matchups_to_simulate = [match for match in matchups if not memoizer.remembers(match)]
    print(f"Num not remembered: {len(matchups_to_simulate)}/{len(matchups)}")
  else:
    matchups_to_simulate = None

  if using_mpi:
    matchups_to_simulate = comm.scatter(matchups_to_simulate, root=0)

  my_results = [(uniform(-30, 30), uniform(-30, 30)) for i in range(len(matchups_to_simulate))]
  results = comm.gather(my_results, root=0) if using_mpi else my_results

  if rank == 0:
    memoizer.memoize_all(zip(matchups_to_simulate, results))
    match_results = [memoizer.fetch(match) for match in matchups]
    fitnesses = compile_fitnesses(num_matchups_per_evaluation, contestants, matchups, match_results)
    
    
    print(f"{len(fitnesses)=}")
    print(f"{len(contestants)=}")




  meta_archives = run_agent_training(meta_archive, max_iterations)
  meta_archives.extend([meta_archives[-1]] * 20)
  render_animation(meta_archives)

if __name__ == "__main__":
  meta_evaluation()