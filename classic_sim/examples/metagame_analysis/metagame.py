import warnings
from map_elites import Archive
from game_manager import GameManager
from strategy import GreedyActionSmart
from zones import Deck
from enums import Classes, CardSets
from game import TooManyActions


import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Ellipse
from matplotlib.colors import ListedColormap

from examples.metaspace_generation.coevolution import generate_random_deck, get_sublist
from random import gauss, randint, uniform, shuffle, choice, seed, random
from copy import deepcopy

import cma


from statistics import mean
from scipy.stats import ttest_ind
from numpy.random import choice as choice_with_replacement, RandomState

import json
from atomicwrites import atomic_write
import pickle
import csv

from joblib import Parallel, delayed
from multiprocessing import cpu_count
from contextlib import nullcontext

warnings.simplefilter("ignore", cma.evolution_strategy.InjectionWarning)

try:
  from mpi4py import MPI
  MPI.Errhandler(MPI.ERRORS_ARE_FATAL)
  using_mpi = True
except ModuleNotFoundError:
  using_mpi = False

def stretch(n, start1, stop1, start2, stop2):
  return (n - start1) / (stop1 - start1) * (stop2 - start2) + start2

class MetaArchive():
  def __init__(self, x_title, y_title, x_range, y_range, num_buckets, archive_names, num_agents, num_samples_per_agent, archive_colors):
    self.x_title = x_title
    self.y_title = y_title
    self.x_range = x_range
    self.y_range = y_range
    self.num_buckets = num_buckets
    self.archive_names = archive_names
    self.archive_colors = archive_colors
    self.num_archives = len(archive_names)
    self.num_agents = num_agents    
    self.num_samples_per_agent = num_samples_per_agent
    self.archives = [(Archive(self.x_title, self.y_title, self.x_range, self.y_range, self.num_buckets, archive_name, archive_color)) for archive_name, archive_color in zip(self.archive_names, self.archive_colors)]
  
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
      self.agents.append(Agent(agent_number, uniform(x_min, x_max-0.4), uniform(y_min, y_max-1.3), self, parent_archive_index, self.num_samples_per_agent))
  
  def load_archives(self, archiveA, archiveB, archiveC):
    self.archives[0].load(archiveA)
    self.archives[1].load(archiveB)
    self.archives[2].load(archiveC)
    self.setup_agents()

  def tell_agents(self, contestants, fitnesses):
    agent_contestant_updates = [[] for _ in range(self.num_agents)]
    agent_fitness_updates = [[] for _ in range(self.num_agents)]
    for (agent, sample, cma_sample), fitness in zip(contestants, fitnesses):
      if not agent.still_learning: continue
      agent_contestant_updates[agent.agent_number].append(cma_sample)
      agent_fitness_updates[agent.agent_number].append(stretch(fitness, -30, 30, 1, 0))

    for agent in self.agents:
      if not agent.still_learning: continue
      agent.latest_fitness = 0.6*agent.latest_fitness + 0.2*mean(agent_fitness_updates[agent.agent_number]) + 0.2*0.5
      agent.es.tell(agent_contestant_updates[agent.agent_number], agent_fitness_updates[agent.agent_number])
      agent.es.manage_plateaus(2, 0.99)
      agent.x, agent.y = agent.es.result[0]
      agent.x_deviation, agent.y_deviation = agent.es.result[6]

  def change_classes_if_struggling(self):
    for agent in self.agents:
      agent.class_switch_if_underperforming()

  def display(self, fig, axis):
    fig.set_figheight(3.5)
    fig.set_figwidth(12)
    
    for (archive, current_ax) in zip(self.archives, axis):
      x, y, Zm = archive.get_graph()
      
      im = current_ax.pcolormesh(x, y, Zm.T[:-1, :-1], vmin=-30, vmax=30, shading='flat')
      current_ax.set_xlabel(archive.x_title)
      current_ax.set_ylabel(archive.y_title)

      current_ax.set_title(archive.archive_name.capitalize(), color=archive.title_color)
      trim_x, trim_y = archive.transform_from_real_space_to_scale(1, 1)
      current_ax.set_xlim(archive.x_min, archive.x_max-trim_x)
      current_ax.set_ylim(archive.y_min, archive.y_max-trim_y)
      x0,x1 = current_ax.get_xlim()
      y0,y1 = current_ax.get_ylim()
      current_ax.set_aspect((x1-x0)/(y1-y0))

      agents_in_this_archive = [agent for agent in self.agents if agent.parent_archive == archive]

      agent_x = [agent.x for agent in agents_in_this_archive]
      agent_y = [agent.y for agent in agents_in_this_archive]
      custom_cmap =["#eb4034", "#ebab34", "#f700ff"]
      agent_original_parent_id = [custom_cmap[agent.original_parent_archive_id] for agent in agents_in_this_archive]
      draw_condifence_ellipses(current_ax, agents_in_this_archive)
      current_ax.scatter(agent_x, agent_y, c=agent_original_parent_id, s=8)

    return im

def draw_condifence_ellipses(ax, agents):
  draw_confidence(ax, agents, 1, 'grey', 'black', 0.2, '--')
  # draw_confidence(ax, agents, 2, 'red', 'black', 0.1, '--')
  # draw_confidence(ax, agents, 3, 'red', 'black', 0.1, '--')

def draw_confidence(ax, agents, n_stds, facecolor, edgecolor, alpha, linestyle):
  for agent in agents:
    ellipse = Ellipse((agent.x, agent.y), width=agent.x_deviation*n_stds, height=agent.y_deviation*n_stds, facecolor=facecolor, alpha=alpha, edgecolor=edgecolor, linestyle=linestyle)
    ax.add_patch(ellipse)

class Agent():
  def __init__(self, agent_number, x, y, grandparent_meta_archive, parent_archive_id, num_samples_per_agent):
    self.agent_number = agent_number
    self.grandparent_meta_archive = grandparent_meta_archive
    self.parent_archive_id = parent_archive_id
    self.original_parent_archive_id = parent_archive_id
    self.parent_archive = grandparent_meta_archive.archives[parent_archive_id]
    self.x = x
    self.y = y
    self.x_deviation, self.y_deviation = self.parent_archive.transform_from_real_space_to_scale(1, 1)
    x_min, x_max, y_min, y_max = self.parent_archive.get_range()
    self.latest_fitness = 0.5
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
          'verbose': 0, 'verb_disp': 0,
          'seed': 1,

      }
    )

  def scale_covariance(self, scale):
    self.es.sigma *= scale

  def class_switch_if_underperforming(self):
    chance = (0.5-self.latest_fitness)*2 if self.latest_fitness < 0.5 else 0
    print(self.latest_fitness)
    if random() < chance:
      alternative_classes = [0, 1, 2]
      alternative_classes.remove(self.parent_archive_id)
      new_parent_id = choice(alternative_classes)
      self.parent_archive = self.grandparent_meta_archive.archives[new_parent_id]
      self.scale_covariance(4)

  def __repr__(self):
    return f"\nAgent {self.agent_number} ({self.parent_archive.archive_name}@{self.x:.2f},{self.y:.2f})"


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
    if not contestant_agent.still_learning:
      fitnesses.append(None)
      continue
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
    meta_archive = MetaArchive(x_title="Hand size", y_title="Turns", x_range=(1, 9), y_range=(9, 35), num_buckets=40, archive_names=["mage", "hunter", "warrior"], num_agents=num_agents, num_samples_per_agent=num_samples_per_agent, archive_colors=["#eb4034", "#ebab34", "#f700ff"])
    meta_archive.load_archives("metagame/mage.json", "metagame/hunter.json", "metagame/warrior.json")
    meta_archives = []
  
  memoizer = Memoizer("metagame/memoizer.json")
  
  [meta_archive.archives[i].assign_clusters() for i in range(meta_archive.num_archives)]

  return meta_archive,meta_archives,memoizer


def render_animation(meta_archives):
  fig, axis = plt.subplots(1, 3, sharey=False, sharex=True)
  plt.tight_layout()
  repeating_animation = True
  ani = FuncAnimation(fig, animate, init_func=init_animation, frames=len(meta_archives), interval=20, repeat=repeating_animation, repeat_delay=10000,fargs=[meta_archives, fig, axis, repeating_animation])
  ani.save("metagame/tourny.gif", writer="pillow", fps=10, progress_callback = lambda i, n: print(f'Saving frame {i+1}/{n}'))

def pprint_matchup(matchup):
  player, opponent = matchup
  print(f"{player[0]}, sample_index: {player[1]['x_index'], player[1]['y_index']}, sample_fitness: {player[1]['fitness']} vs {opponent[0]}, sample_index: {opponent[1]['x_index'], opponent[1]['y_index']}, sample_fitness: {opponent[1]['fitness']}")


def play_games_till_stoppage(matchups, min_games, max_games, pvalue_alpha, min_streak):
  results = []
  game_manager = GameManager()
  class_setups = {
    "mage": (Classes.MAGE, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE]),
    "hunter": (Classes.HUNTER, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER]),
    "warrior": (Classes.WARRIOR, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR]),
  }
  for matchup in matchups:
    (player_agent, player_sample, _), (opponent_agent, opponent_sample, _) = matchup
    if not player_agent.still_learning and not opponent_agent.still_learning:
      results.append((None, None))
      continue
    player_strategy = GreedyActionSmart(player_sample['sample'][0])
    player_decklist = Deck.generate_from_decklist(player_sample['sample'][1])
    opponent_strategy = GreedyActionSmart(opponent_sample['sample'][0])
    opponent_decklist = Deck.generate_from_decklist(opponent_sample['sample'][1])
    player_class_enum, player_cardset = class_setups[player_agent.parent_archive.archive_name]
    opponent_class_enum, opponent_cardset = class_setups[opponent_agent.parent_archive.archive_name]
    game_manager.build_full_game_manager(player_cardset, opponent_cardset, player_class_enum, player_decklist, player_strategy, opponent_class_enum, opponent_decklist, opponent_strategy, RandomState(0))
    game_results = []
    game_manager.create_game()

    num_games_played = 0
    streak = 0
    # print(f"Playing {min_games} < n < {max_games} games\nEarly stoppage at {min_streak}x streak of p<{pvalue_alpha}")
    while num_games_played < max_games:
      try:
        game_result = game_manager.game.play_game()
        game_results.append(game_result)
        player_healths = [result[1] for result in game_results]
        enemy_healths = [result[4] for result in game_results]
        pvalue = ttest_ind(player_healths, enemy_healths, equal_var=False).pvalue if num_games_played > 1 else 1
        num_games_played += 1
        streak = streak + 1 if pvalue < pvalue_alpha else 0 
        # print(f"Played {num_games_played} games, p={pvalue:.4f} {streak=}")


        if streak >= min_streak and num_games_played > min_games: break
      except (TooManyActions, RecursionError) as e:
        game_result = None
        print(e)
      except Exception as e:
        game_result = None
        raise e
      game_manager.game.reset_game()
      game_manager.game.start_game()
    results.append((mean(player_healths), mean(enemy_healths)))
  return results
    


def run_tournament(using_mpi, max_iterations, num_matchups_per_evaluation, fake_games, min_games, max_games, pvalue_alpha, min_streak, core_spread_multiplier, comm, num_cores, rank, meta_archive, meta_archives, memoizer):
  with Parallel(n_jobs=num_cores, verbose=50) if not using_mpi else nullcontext() as parallel:
    iter_num = 0
    while iter_num < max_iterations:
      if rank == 0:
        print(f"Starting iteration {iter_num}")
        contestants = get_contestants(meta_archive)
        if not any([agent.still_learning for agent,_,_ in contestants]): break
        matchups = get_matchups(contestants, num_matchups_per_evaluation)

        new_matchups_to_simulate = [match for match in matchups if not memoizer.remembers(match)]
        for matchup in new_matchups_to_simulate:
          print(memoizer.match_to_key(matchup))
        print(f"Remembered: {len(matchups) - len(new_matchups_to_simulate)}/{len(matchups)}, simulating {len(new_matchups_to_simulate)} total")
      else:
        new_matchups_to_simulate = None
      if(len(new_matchups_to_simulate) == 0):
        spread = []
      else:
        spread = [get_sublist(new_matchups_to_simulate, num_cores, core) for core in range(num_cores*(core_spread_multiplier if not using_mpi else 1))] if rank == 0 else None
        spread = [core_matches for core_matches in spread if core_matches != []]
      cores_matchups_to_simulate = comm.scatter(spread, root=0) if using_mpi else spread
      if fake_games:
        results = []
        for core in cores_matchups_to_simulate:
          for matchup in core:
            (player_agent, player_sample, _), (opponent_agent, opponent_sample, _) = matchup
            # if not player_agent.still_learning and not opponent_agent.still_learning:
            #   results.append((None, None))
            # else:
            results.append((player_sample['fitness'], opponent_sample['fitness']))
      else:
        if using_mpi:
          print(f"Core #{rank} has {len(cores_matchups_to_simulate)} matchups to simulate")
          results = play_games_till_stoppage(cores_matchups_to_simulate, min_games, max_games, pvalue_alpha, min_streak)
        else:
          results = parallel(delayed(play_games_till_stoppage)(cores_matchups_to_simulate[i], min_games, max_games, pvalue_alpha, min_streak) for i in range(len(cores_matchups_to_simulate)))

      non_flat_results = comm.gather(results, root=0) if using_mpi else results
      if rank == 0:
        results = [result for individual_core_reponses in non_flat_results for result in individual_core_reponses] if not fake_games else results
        memoizer.memoize_all(zip(new_matchups_to_simulate, results))
        match_results = [memoizer.fetch(match) for match in matchups]
        fitnesses = compile_fitnesses(num_matchups_per_evaluation, contestants, matchups, match_results)
        meta_archive.tell_agents(contestants, fitnesses)
        meta_archive.change_classes_if_struggling()
        meta_archives.append(deepcopy(meta_archive))

        meta_archive.pickle_to_file()
        with atomic_write("metagame/meta_history.pickle", overwrite=True, mode='wb') as f:
          pickle.dump(meta_archives, f)

        with open("metagame/agent_history.csv", mode='a+') as f:
          writer = csv.writer(f)
          generation = []
          for agent in meta_archive.agents:
            try:
              cluster = agent.parent_archive.vals_to_entry(agent.x, agent.y, missing_behaviour="none")['hdbscan']
            except KeyError:
              cluster = -1
            generation.extend((agent.x, agent.y, agent.parent_archive.archive_name, cluster))
          writer.writerow(generation)

      iter_num += 1
    return meta_archives

def meta_evaluation():
  try_unpickle = False #should we continue from a saved pickle checkpoint
  max_iterations = 10 #override max iterations that simulation will run regardless of CMA covnergence
  num_agents = 48 #how many total agents divided between the three classes
  num_samples_per_agent = 9 #seems like must be >= 3, how many samples should each agent draw from their search space to test
  num_matchups_per_evaluation = 10 #must be even, how many other players each agent plays against
  min_games = 10 #min games to play even if streak triggers
  max_games = 100 #max games to play if pvalue doesnt converge
  pvalue_alpha = 0.05 #the p-value threshold for significance
  min_streak = 3 #how many p<alpha in a row before early stoppage
  num_cores_to_use_if_not_mpi = cpu_count() #how many cores should we use if not using mpi
  fake_games = False #Generate game results from general fitness
  core_spread_multiplier = 4 #spread the total matchups between extra cores

  seed(0) 

  if not try_unpickle:
    with open('metagame/agent_history.csv', 'w') as f:
      writer = csv.writer(f)
      headers = []
      [(headers.append(f"agent_{agent_id}_x"), headers.append(f"agent_{agent_id}_y"), headers.append(f"agent_{agent_id}_archive"), headers.append(f"agent_{agent_id}_cluster")) for agent_id in range(num_agents)]
      writer.writerow(headers)

  comm, num_cores, rank = (MPI.COMM_WORLD, MPI.COMM_WORLD.Get_size(), MPI.COMM_WORLD.Get_rank()) if using_mpi else (None, num_cores_to_use_if_not_mpi, 0)
  meta_archive, meta_archives, memoizer = init_archives(try_unpickle, num_agents, num_samples_per_agent) if rank == 0 else (None, None, None)
  meta_archives = run_tournament(using_mpi, max_iterations, num_matchups_per_evaluation, fake_games, min_games, max_games, pvalue_alpha, min_streak, core_spread_multiplier, comm, num_cores, rank, meta_archive, meta_archives, memoizer)
  if rank == 0: render_animation(meta_archives)
if __name__ == "__main__":
  meta_evaluation()
