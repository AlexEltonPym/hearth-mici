from map_elites import Archive
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Ellipse

from coevolution import generate_random_deck, get_sublist
from random import gauss, randint, uniform, shuffle
from copy import deepcopy

import cma


from statistics import mean
from numpy.random import choice as choice_with_replacement

import json
from atomicwrites import atomic_write
import pickle

try:
  from mpi4py import MPI
  MPI.Errhandler(MPI.ERRORS_ARE_FATAL)
  using_mpi = True
except ModuleNotFoundError:
  using_mpi = False

def stretch(n, start1, stop1, start2, stop2):
  return (n - start1) / (stop1 - start1) * (stop2 - start2) + start2

class MetaArchive():
  def __init__(self, x_title, y_title, x_range, y_range, num_buckets, archive_names, num_agents, num_samples_per_agent):
    self.x_title = x_title
    self.y_title = y_title
    self.x_range = x_range
    self.y_range = y_range
    self.num_buckets = num_buckets
    self.archive_names = archive_names
    self.num_archives = len(archive_names)
    self.num_agents = num_agents    
    self.num_samples_per_agent = num_samples_per_agent
    self.archives = [(Archive(self.x_title, self.y_title, self.x_range, self.y_range, self.num_buckets, archive_name)) for archive_name in self.archive_names]
  
  @classmethod
  def unpickle_from_file(cls, filename="metagame/meta.pickle"):
      with open(filename, 'rb') as f:
        return pickle.load(f)


  def pickle_to_file(self, filename="metagame/meta.pickle"):
    with atomic_write(filename, overwrite=True, mode='wb') as f: 
      pickle.dump(self, f)

  def setup_agents(self):
    self.agents = []
    for agent_number in range(self.num_agents):
      parent_archive_index = int(agent_number/self.num_agents * self.num_archives)
      x_min, x_max, y_min, y_max = self.archives[parent_archive_index].get_range()
      self.agents.append(Agent(agent_number, uniform(x_min, x_max-0.4), uniform(y_min, y_max-1.3), self.archives[parent_archive_index], self.num_samples_per_agent))
  def load_archives(self, archiveA, archiveB, archiveC):
    self.archives[0].load(archiveA)
    self.archives[1].load(archiveB)
    self.archives[2].load(archiveC)
    self.setup_agents()

  def tell_agents(self, contestants, fitnesses):
    agent_contestant_updates = [[] for _ in range(self.num_agents)]
    agent_fitness_updates = [[] for _ in range(self.num_agents)]
    for (agent, sample, cma_sample), fitness in zip(contestants, fitnesses):
      agent_contestant_updates[agent.agent_number].append(cma_sample)
      agent_fitness_updates[agent.agent_number].append(stretch(fitness, -30, 30, 1, 0))

    for agent in self.agents:
      agent.es.tell(agent_contestant_updates[agent.agent_number], agent_fitness_updates[agent.agent_number])
      agent.es.manage_plateaus(2, 0.99)
      agent.x, agent.y = agent.es.result[0]
      agent.x_deviation, agent.y_deviation = agent.es.result[6]

  def display(self, fig, axis):
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

      draw_condifence_ellipses(current_ax, agents_in_this_archive)
    return im

def draw_condifence_ellipses(ax, agents):
  draw_confidence(ax, agents, 1, 'red', 'black', 0.2, '--')
  # draw_confidence(ax, agents, 2, 'red', 'black', 0.1, '--')
  # draw_confidence(ax, agents, 3, 'red', 'black', 0.1, '--')

def draw_confidence(ax, agents, n_stds, facecolor, edgecolor, alpha, linestyle):
  for agent in agents:
    ellipse = Ellipse((agent.x, agent.y), width=agent.x_deviation*n_stds, height=agent.y_deviation*n_stds, facecolor=facecolor, alpha=alpha, edgecolor=edgecolor, linestyle=linestyle)
    ax.add_patch(ellipse)

class Agent():
  def __init__(self, agent_number, x, y, parent_archive, num_samples_per_agent):
    self.agent_number = agent_number
    self.parent_archive = parent_archive
    self.x = x
    self.y = y
    self.x_deviation, self.y_deviation = self.parent_archive.transform_from_real_space_to_scale(1, 1)

    x_min, x_max, y_min, y_max = self.parent_archive.get_range()
    self.es = cma.CMAEvolutionStrategy(x0=[self.x, self.y], sigma0=1,
      inopts={
          'bounds': [[x_min, y_min], [x_max-0.4, y_max-1.3]],
          'CMA_stds': [self.x_deviation, self.y_deviation],
          'popsize': num_samples_per_agent,
          # 'CMA_cmean': 1,
          'maxiter': 1000, #we have overridden this with max_iterations
          # 'minstd': self.parent_archive.transform_from_real_space_to_scale(1, 1),
          # 'maxstd': self.parent_archive.transform_from_real_space_to_scale(2, 2),
          # 'verbose': 10, 'verb_disp': 1,
          'verbose': 0, 'verb_disp': 0

      }
    )

  def __repr__(self):
    return f"\nAgent {self.agent_number}: {self.parent_archive.archive_name}({self.x:.2f},{self.y:.2f})"


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
    (player_agent, player, _), (opponent_agent, opponent, _) = match
    player_key = f"{player_agent.parent_archive.archive_name[0]}_{player['x_index']}_{player['y_index']}"
    opponent_key = f"{opponent_agent.parent_archive.archive_name[0]}_{opponent['x_index']}_{opponent['y_index']}"
    return f"{player_key}_v_{opponent_key}" if player_key < opponent_key else f"{opponent_key}_v_{player_key}"

def animate(frame_id, *frags):
  meta_archives, fig, axis, repeating_animation = frags
  for ax in axis:
    ax.clear()
  
  im = meta_archives[frame_id].display(fig, axis)

  if frame_id == 0 and not repeating_animation:
    cbar = fig.colorbar(im, ax=axis.ravel().tolist(), shrink=0.9, pad=0.05, fraction=0.05)


def init_animation(*frags):
  pass


#Returns all samples from each agent that need evaluating, including empty samples
def get_contestants(meta_archive):
  contestants = []
  for agent in meta_archive.agents:
    agent_in_ocean = agent.parent_archive.vals_to_entry(agent.x, agent.y, missing_behaviour="none")['sample'] == None
    agent.still_learning = not agent.es.stop() or agent_in_ocean or agent.es.sigma > 1 #ignore_list=['tolfun', 'tolflatfitness']
    for sample_x, sample_y in agent.es.ask():
      sample_elite = agent.parent_archive.vals_to_entry(sample_x, sample_y, missing_behaviour="none")
      contestants.append((agent, sample_elite, (sample_x, sample_y)))
  return contestants

def get_matchups(contestants, num_matchups_per_evaluation):
  matchups = []
  participants = []
  for contestant in contestants:
    if contestant not in participants and contestant[1]['sample'] != None:
      participants.append(contestant)

  shuffle(participants)

  for index, participant in enumerate(participants):
    for offset in range(1, num_matchups_per_evaluation//2+1):
      matchups.append((participant, participants[(index+offset)%len(participants)]))

  return matchups

def compile_fitnesses(num_matchups_per_evaluation, contestants, matchups, match_results):
  fitnesses = []
  for contestant_agent, contestant_elite, contestant_original_sample in contestants:
    if contestant_elite['sample'] == None:
      fitnesses.append(-30)
    else:
      running_average = 0
      for ((player_agent, player, _), (opponent_agent, opponent, _)), (player_result, opponent_result) in zip(matchups, match_results):
        if player == contestant_elite:
          running_average += player_result/num_matchups_per_evaluation
        elif opponent == contestant_elite:
          running_average += opponent_result/num_matchups_per_evaluation
      fitnesses.append(running_average)
  return fitnesses


def init_archives(unpickle_if_available, num_agents, num_samples_per_agent):
  if unpickle_if_available:
    try:
      meta_archive = MetaArchive.unpickle_from_file()
      print("Loaded meta_archive")
    except FileNotFoundError:
      unpickle_if_available = False
    try:
      with open("metagame/meta_history.pickle", 'rb') as f:
        meta_archives = pickle.load(f)
      print(f"Loaded meta history with {len(meta_archives)} entries")
    except FileNotFoundError:
      unpickle_if_available = False

  if not unpickle_if_available:
    meta_archive = MetaArchive(x_title="Hand size", y_title="Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40, archive_names=["mage", "hunter", "warrior"], num_agents=num_agents, num_samples_per_agent=num_samples_per_agent)
    meta_archive.load_archives("metagame/mage.json", "metagame/hunter.json", "metagame/warrior.json")
    meta_archives = []
  
  memoizer = Memoizer("metagame/memoizer.json")
  
  return meta_archive,meta_archives,memoizer


def render_animation(meta_archives):
  fig, axis = plt.subplots(1, 3, sharey=False, sharex=True)
  plt.tight_layout()
  repeating_animation = True
  ani = FuncAnimation(fig, animate, init_func=init_animation, frames=len(meta_archives), interval=20, repeat=repeating_animation, repeat_delay=10000,fargs=[meta_archives, fig, axis, repeating_animation])
  ani.save("metagame/tourny.gif", writer="pillow", fps=10, progress_callback = lambda i, n: print(f'Saving frame {i+1}/{n}'))

def pprint_matchup(matchup):
  player, opponent = matchup
  print(f"{player[0], player[1]['x_index'], player[1]['y_index'], player[1]['fitness']} vs {opponent[0], opponent[1]['x_index'], opponent[1]['y_index'], opponent[1]['fitness']}")


def run_tournament(using_mpi, max_iterations, num_matchups_per_evaluation, comm, num_cores, rank, meta_archive, meta_archives, memoizer):
  iter_num = 0
  while iter_num < max_iterations:
    if rank == 0:
      print(f"Starting iteration {iter_num}")
      contestants = get_contestants(meta_archive)
      if not any([agent.still_learning for agent,_,_ in contestants]): break
      matchups = get_matchups(contestants, num_matchups_per_evaluation)
      new_matchups_to_simulate = [match for match in matchups if not memoizer.remembers(match)]
      print(f"Remembered: {len(matchups) - len(new_matchups_to_simulate)}/{len(matchups)}, simulating {len(new_matchups_to_simulate)} total")
    else:
      new_matchups_to_simulate = None

    spread = [get_sublist(new_matchups_to_simulate, num_cores, core) for core in range(num_cores)] if rank == 0 else None
    cores_matchups_to_simulate = comm.scatter(spread, root=0) if using_mpi else new_matchups_to_simulate

    print(f"Core #{rank} has {len(cores_matchups_to_simulate)} matchups to simulate")
    results = [(matchup[0][1]['fitness'], matchup[1][1]['fitness']) for matchup in cores_matchups_to_simulate]
    non_flat_results = comm.gather(results, root=0) if using_mpi else [results]

    if rank == 0:
      results = [result for individual_core_reponses in non_flat_results for result in individual_core_reponses]
      memoizer.memoize_all(zip(new_matchups_to_simulate, results))
      match_results = [memoizer.fetch(match) for match in matchups]
      fitnesses = compile_fitnesses(num_matchups_per_evaluation, contestants, matchups, match_results)
      meta_archive.tell_agents(contestants, fitnesses)
      meta_archives.append(deepcopy(meta_archive))

      meta_archive.pickle_to_file()
      with atomic_write("metagame/meta_history.pickle", overwrite=True, mode='wb') as f:
        pickle.dump(meta_archives, f)

    iter_num += 1
  return meta_archives

def meta_evaluation():
  try_unpickle = True
  max_iterations = 3
  num_agents = 30
  num_samples_per_agent = 6
  num_matchups_per_evaluation = 6 #must be even

  comm, num_cores, rank = (MPI.COMM_WORLD, MPI.COMM_WORLD.Get_size(), MPI.COMM_WORLD.Get_rank()) if using_mpi else (None, 1, 0)
  meta_archive, meta_archives, memoizer = init_archives(try_unpickle, num_agents, num_samples_per_agent) if rank == 0 else (None, None, None)
  meta_archives = run_tournament(using_mpi, max_iterations, num_matchups_per_evaluation, comm, num_cores, rank, meta_archive, meta_archives, memoizer)
  if rank == 0: render_animation(meta_archives)

if __name__ == "__main__":
  meta_evaluation()