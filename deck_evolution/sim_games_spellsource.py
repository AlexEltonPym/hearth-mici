import random
from spellsource.context import Context
import sys


HUNTER_DECK = '''### HUNTER_DECK
# Class: GREEN
# Format: Standard
# 2x Arcane Shot
# 2x Stonetusk Boar
# 2x Timber Wolf
# 2x Tracking
# 2x Bloodfen Raptor
# 2x River Crocolisk
# 2x Ironforge Rifleman
# 2x Raid Leader
# 2x Razorfen Hunter
# 2x Silverback Patriarch
# 2x Houndmaster
# 2x Multi-Shot
# 2x Oasis Snapjaw
# 2x Stormpike Commando
# 2x Core Hound
#'''

MAGE_DECK = '''### MAGE_DECK
# Class: BLUE
# Format: Standard
# 2x Arcane Missiles
# 2x Murloc Raider
# 2x Arcane Explosion
# 2x Bloodfen Raptor
# 2x Novice Engineer
# 2x River Crocolisk
# 2x Arcane Intellect
# 2x Raid Leader
# 2x Wolfrider
# 2x Fireball
# 2x Oasis Snapjaw
# 2x Polymorph
# 2x Sen'jin Shieldmasta
# 2x Nightblade
# 2x Boulderfist Ogre
#'''

WARRIOR_DECK = '''### WARRIOR_DECK
# Class: RED
# Format: Standard
# 2x Boulderfist Ogre
# 2x Charge
# 2x Dragonling Mechanic
# 2x Execute
# 2x Fiery War Axe
# 2x Frostwolf Grunt
# 2x Gurubashi Berserker
# 2x Heroic Strike
# 2x Lord of the Arena
# 2x Murloc Raider
# 2x Murloc Tidehunter
# 2x Razorfen Hunter
# 2x Sen'jin Shieldmasta
# 2x Warsong Commander
# 2x Wolfrider
#'''

def playtest(player_deck, enemy_deck, num_games):
  player_stats = dict({'HEALTH_DELTA': 0,
                      'WIN_RATE': 0,
                      'DAMAGE_DEALT': 0,
                      'HEALING_DONE': 0,
                      'MANA_SPENT': 0,
                      'CARDS_PLAYED': 0,
                      'TURNS_TAKEN': 0,
                      'ARMOR_GAINED': 0,
                      'CARDS_DRAWN': 0,
                      'FATIGUE_DAMAGE': 0,
                      'MINIONS_PLAYED': 0,
                      'SPELLS_CAST': 0,
                      'HERO_POWER_USED': 0,
                      'WEAPONS_EQUIPPED': 0,
                      'WEAPONS_PLAYED': 0,
                      'CARDS_DISCARDED': 0,
                      'HERO_POWER_DAMAGE_DEALT': 0,
                      'ARMOR_LOST': 0})

  with Context() as ctx:
    player1_ai = ctx.behaviour.GameStateValueBehaviour()
    player2_ai = ctx.behaviour.GameStateValueBehaviour()

    delta_health = 0
    num_successful_games = 0
    num_failed_games = 0
    while num_successful_games < num_games:
      try:
        game_context = ctx.GameContext.fromDeckLists([player_deck, enemy_deck])
        game_context.setBehaviour(ctx.GameContext.PLAYER_1, player1_ai)
        game_context.setBehaviour(ctx.GameContext.PLAYER_2, player2_ai)
        game_context.play()
        player1health = int(str(game_context.getPlayer(ctx.GameContext.PLAYER_1).getHero()).split(",")[3].split("/")[1])
        player2health = int(str(game_context.getPlayer(ctx.GameContext.PLAYER_2).getHero()).split(",")[3].split("/")[1])
        # stats = str(game_context.getPlayer(ctx.GameContext.PLAYER_1).getStatistics())
        # for stat in stats.split("\n")[1:-1]:
        #   stat_name, stat_value = tuple(stat.split(": "))
        #   if(stat_name in player_stats):
        #     player_stats[stat_name] += float(stat_value)/num_games

        # player_stats['HEALTH_DELTA'] += (player1health-player2health)/num_games
        delta_health += player1health-player2health
        num_successful_games += 1
      except Exception as e:
        num_failed_games += 1
    return delta_health / num_games, num_successful_games, num_failed_games


if __name__ == "__main__":
  lines = []
  while True:
    try:
        lines.append(input())
    except EOFError:
        break
  deck = '\n'.join(lines)

  num_games = int(sys.argv[1])

  if num_games == -1:
    print(f"{random.gauss(0, 10)},{num_games},0")
    exit(0)
  else:
    try:
      health_delta_vs_hunter, sucesses, failures = playtest(deck, HUNTER_DECK, num_games)
      print(f"{health_delta_vs_hunter},{sucesses},{failures}")
      exit(0)
    except Exception as e:
      print("exception with fitness evaulation")
      exit(1)
