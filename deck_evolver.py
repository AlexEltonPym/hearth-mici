from spellsource.context import Context

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

with Context() as ctx:
  game_context = ctx.GameContext.fromDeckLists([HUNTER_DECK, MAGE_DECK])

  player1_ai = ctx.behaviour.GameStateValueBehaviour()
  player2_ai = ctx.behaviour.GameStateValueBehaviour()

  game_context.setBehaviour(ctx.GameContext.PLAYER_1, player1_ai)
  game_context.setBehaviour(ctx.GameContext.PLAYER_2, player2_ai)

  game_context.play()

  stats = game_context.getPlayer(ctx.GameContext.PLAYER_1).getStatistics()
  print(stats)

