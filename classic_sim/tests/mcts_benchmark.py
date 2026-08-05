import sys

# appending the parent directory path
sys.path.append('../src/')

import time
from game_manager import GameManager
from strategy import MCTS, GreedyAction, GreedyActionSmart, RandomAction
from enums import *
from zones import Deck
from exceptions import TooManyActions

# mirror decklists so the agents are the only difference between the players
BASIC_MAGE = [
  "Arcane Missiles", "Arcane Missiles", "Murloc Raider", "Murloc Raider",
  "Arcane Explosion", "Arcane Explosion", "Bloodfen Raptor", "Bloodfen Raptor",
  "Novice Engineer", "Novice Engineer", "River Crocolisk", "River Crocolisk",
  "Arcane Intellect", "Arcane Intellect", "Raid Leader", "Raid Leader",
  "Wolfrider", "Wolfrider", "Fireball", "Fireball",
  "Oasis Snapjaw", "Oasis Snapjaw", "Polymorph", "Polymorph",
  "Sen'jin Shieldmasta", "Sen'jin Shieldmasta", "Nightblade", "Nightblade",
  "Boulderfist Ogre", "Boulderfist Ogre"]


def run_match(player_strategy, enemy_strategy, num_games, label):
  game_manager = GameManager()
  game_manager.create_player_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_enemy_pool([CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE])
  game_manager.create_player(Classes.MAGE, Deck.generate_from_decklist(BASIC_MAGE), player_strategy)
  game_manager.create_enemy(Classes.MAGE, Deck.generate_from_decklist(BASIC_MAGE), enemy_strategy)
  game_manager.create_game()

  wins, losses, errors = 0, 0, 0
  start = time.time()
  for i in range(num_games):
    try:
      result = game_manager.game.play_game()
      if result[0] == 1:
        wins += 1
      else:
        losses += 1
    except (TooManyActions, RecursionError):
      errors += 1
    game_manager.game.reset_game()
    game_manager.game.start_game()
    print(f"[{label}] game {i+1}/{num_games}: W{wins} L{losses} E{errors} ({time.time()-start:.0f}s elapsed)", flush=True)

  played = wins + losses
  winrate = wins / played if played else 0
  print(f"[{label}] FINAL: {wins}-{losses} ({winrate:.0%} winrate), {errors} aborted, {time.time()-start:.0f}s", flush=True)
  return winrate


if __name__ == "__main__":
  matchup = sys.argv[1] if len(sys.argv) > 1 else "all"
  games = int(sys.argv[2]) if len(sys.argv) > 2 else 20

  if matchup in ("smoke",):
    run_match(MCTS(iterations=50), RandomAction(), 1, "smoke mcts_vs_random")
  if matchup in ("all", "baseline"):
    run_match(GreedyAction(), RandomAction(), games, "greedy_vs_random")
  if matchup in ("all", "mcts_random"):
    run_match(MCTS(iterations=50), RandomAction(), games, "mcts_vs_random")
  if matchup in ("all", "mcts_greedy"):
    run_match(MCTS(iterations=50), GreedyAction(), games, "mcts_vs_greedy")
  if matchup in ("all", "mcts_smart"):
    run_match(MCTS(iterations=50), GreedyActionSmart(), games, "mcts_vs_smartgreedy")
