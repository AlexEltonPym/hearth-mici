from sys import path, argv

path.append('../../src/')
path.append('../map_elites')

import warnings
from game_manager import GameManager
from strategy import GreedyActionSmart
from zones import Deck
from enums import Classes, CardSets
from exceptions import TooManyActions

import cma

from statistics import mean
from scipy.stats import ttest_ind
from numpy.random import RandomState
from json import loads
from joblib import Parallel, delayed
import dill
import sys

def play_games_till_stoppage(matchup):
  min_games, max_games, pvalue_alpha, min_streak = 3, 10, 0.05, 3
  game_manager = GameManager()
  class_setups = {
    "mage": (Classes.MAGE, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE]),
    "hunter": (Classes.HUNTER, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER]),
    "warrior": (Classes.WARRIOR, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR]),
  }
  (player_agent, player_sample, _), (opponent_agent, opponent_sample, _) = matchup
  if not player_agent.still_learning and not opponent_agent.still_learning:
    return (None, None)
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
  while num_games_played < max_games:
    try:
      game_result = game_manager.game.play_game()
      game_results.append(game_result)
      player_healths = [result[1] for result in game_results]
      enemy_healths = [result[4] for result in game_results]
      pvalue = ttest_ind(player_healths, enemy_healths, equal_var=False).pvalue if num_games_played > 1 else 1
      num_games_played += 1
      streak = streak + 1 if pvalue < pvalue_alpha else 0 
      if streak >= min_streak and num_games_played > min_games: break
    except (TooManyActions, RecursionError) as e:
      game_result = None
      print(e)
    except Exception as e:
      game_result = None
      raise e
    game_manager.game.reset_game()
    game_manager.game.start_game()
  return (mean(player_healths), mean(enemy_healths))
    
if __name__ == "__main__":
  with Parallel(n_jobs=-1) as parallel:
    matchups = dill.load(sys.stdin.buffer)
    results = parallel(delayed(play_games_till_stoppage)(matchup) for matchup in matchups)
    print(">>>"+str(results))