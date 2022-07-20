
import sys

sys.path.append('../../Spellsource/python')

def tryout(card_to_tryout):
  from spellsource.utils import simulate
  from spellsource.context import Context
  import json
  from tqdm import tqdm
  WARRIOR_DECK = '''### WARRIOR_DECK
  # Class: RED
  # Format: Standard
  #
  # 30x (5) Average Card
  #'''

  MAGE_DECK = '''### MAGE_DECK
  # Class: BLUE
  # Format: Standard
  #
  # 30x (5) Custom Card
  #'''


  CARD_AVERAGE = '''{
    "name": "Average Card",
    "baseManaCost": 5,
    "type": "MINION",
    "heroClass": "ANY",
    "baseAttack": 5,
    "baseHp": 5,
    "rarity": "EPIC",
    "description": "",
    "collectible": false,
    "set": "CUSTOM",
    "fileFormatVersion": 1
  }'''

  CARD_CUSTOM = {
    "baseManaCost": 5,
    "baseHp": 5,
    "baseAttack": 5,
    "attributes": {
        "TAUNT": False,
        "LIFESTEAL": False
    },
    "name": "Custom Card",
    "type": "MINION",
    "rarity": "COMMON",
    "description": "Custom card",
    "collectible": True,
    "set": "CUSTOM",
    "fileFormatVersion": 1
  }

  CARD_CUSTOM['baseAttack'] = 5
  CARD_CUSTOM = json.dumps(CARD_CUSTOM)



  gamesToSim = 3
  decks = [WARRIOR_DECK, MAGE_DECK]
  behaviours = ['GameStateValueBehaviour', 'GameStateValueBehaviour']
  with Context() as context:
      print(context.decks.DeckFormat.formats())
      card_id1 = context.CardCatalogue.addOrReplaceCard(CARD_AVERAGE)
      card_id2 = context.CardCatalogue.addOrReplaceCard(CARD_CUSTOM)

      test_results = list(tqdm(simulate(context=context, decks=decks, number=gamesToSim, behaviours=behaviours, reduce=False)))

      winrates = [sum(game['results'][i]['WIN_RATE'] for game in test_results) for i in [0,1]]
      wr = winrates[0]/sum(winrates)*100
      print(f'Winrates: GSVB wins {wr}% ')
      return(wr)


def get_winrates():

  from spellsource.utils import simulate
  from spellsource.context import Context

  from tqdm import tqdm

  import json

  with open('processedCard.json') as f:
      CARD_GREAT = json.dumps(json.load(f))
  # print(CARD_GREAT)

  OP_DECK = '''### OP
  # Class: RED
  # Format: Standard
  #
  # 15x (1) Great Card
  # 10x (5) Average Card
  # 5x (10) Bad Card
  #'''

  UP_DECK = '''### UP
  # Class: BLUE
  # Format: Standard
  #
  # 2x (1) Great Card
  # 8x (5) Average Card
  # 20x (10) Bad Card
  #'''


  AVG_DECK = '''### AVG
  # Class: BLUE
  # Format: Standard
  #
  # 25x (5) Average Card
  # 5x (10) Bad Card
  ard
  #'''

  # CARD_GREAT = '''{
  #   "name": "Great Card",
  #   "baseManaCost": 1,
  #   "type": "MINION",
  #   "heroClass": "ANY",
  #   "baseAttack": 10,
  #   "baseHp": 10,
  #   "rarity": "EPIC",
  #   "description": "",
  #   "collectible": false,
  #   "set": "CUSTOM",
  #   "fileFormatVersion": 1
  # }'''
  CARD_AVERAGE = '''{
    "name": "Average Card",
    "baseManaCost": 5,
    "type": "MINION",
    "heroClass": "ANY",
    "baseAttack": 5,
    "baseHp": 5,
    "rarity": "EPIC",
    "description": "",
    "collectible": false,
    "set": "CUSTOM",
    "fileFormatVersion": 1
  }'''
  CARD_BAD = '''{
    "name": "Bad Card",
    "baseManaCost": 10,
    "type": "MINION",
    "heroClass": "ANY",
    "baseAttack": 1,
    "baseHp": 1,
    "rarity": "EPIC",
    "description": "",
    "collectible": false,
    "set": "CUSTOM",
    "fileFormatVersion": 1
  }'''

  gamesToSim = 3
  decks = [OP_DECK, AVG_DECK]
  behaviours = ['GameStateValueBehaviour', 'GameStateValueBehaviour']
  with Context() as context:
      print(context.decks.DeckFormat.formats())
      card_id1 = context.CardCatalogue.addOrReplaceCard(CARD_GREAT)
      card_id2 = context.CardCatalogue.addOrReplaceCard(CARD_BAD)
      card_id3 = context.CardCatalogue.addOrReplaceCard(CARD_AVERAGE)

      test_results = list(tqdm(simulate(context=context, decks=decks, number=gamesToSim, behaviours=behaviours, reduce=False)))
      print(game['results'][0] for game in test_results)
      

      winrates = [sum(game['results'][i]['WIN_RATE'] for game in test_results) for i in [0,1]]
      wr = winrates[0]/sum(winrates)*100
      print(f'Winrates: GSVB wins {wr}% ')
      return(wr)
  # with Context() as ctx:
  #     # Add the card
  #     card_id1 = ctx.CardCatalogue.addOrReplaceCard(CARD_GREAT)
  #     card_id2 = ctx.CardCatalogue.addOrReplaceCard(CARD_BAD)
  #     card_id3 = ctx.CardCatalogue.addOrReplaceCard(CARD_AVERAGE)
  #     # Reproducible seed
  #     seed = 10101
  #     # Create new instances of the bot
  #     gsvb_1 = ctx.behaviour.GameStateValueBehaviour()
  #     # Or, to play randomly based on the seed (considerably faster):
  #     #   gsvb_1 = ctx.behaviour.PlayGameLogicRandomBehaviour()
  #     gsvb_2 = ctx.behaviour.GameStateValueBehaviour()
  #     # Likewise, to play randomly based on the seed:
  #     #   gsvb_2 = ctx.behaviour.PlayGameLogicRandomBehaviour()

  #     # Player 1 will get the elemental arch deck
  #     game_context = ctx.GameContext.fromDeckLists([OP_DECK, AVG_DECK])
  #     # set the bots
  #     game_context.setBehaviour(ctx.GameContext.PLAYER_1, gsvb_1)
  #     game_context.setBehaviour(ctx.GameContext.PLAYER_2, gsvb_2)
  #     # set the seed
  #     game_context.setLogic(ctx.GameLogic(seed))
  #     assert game_context.getPlayer(ctx.GameContext.PLAYER_1).getDeck().containsCard(card_id3)
  #     game_context.play()
  #     assert game_context.updateAndGetGameOver()
  
  #     # Inspect and print the game context
  #     hero1 = game_context.getPlayer(ctx.GameContext.PLAYER_1).getHero()
  #     hero2 = game_context.getPlayer(ctx.GameContext.PLAYER_2).getHero()

  #     print(hero1)
  #     print(hero2)

  #     for entity in game_context.getPlayer(ctx.GameContext.PLAYER_1).getGraveyard():
  #         print(entity.getSourceCard().getCardId())
      
def make_card(args):

  CARD_CUSTOM = {
    "baseManaCost": 5,
    "baseHp": 5,
    "baseAttack": 5,
    "attributes": {
        "TAUNT": False,
        "LIFESTEAL": False
    },
    "name": "Custom Card",
    "type": "MINION",
    "rarity": "COMMON",
    "description": "Custom card",
    "collectible": True,
    "set": "CUSTOM",
    "fileFormatVersion": 1
  }
  return CARD_CUSTOM
  
def get_histogram():
  from spellsource.utils import simulate
  from spellsource.context import Context
  import json
  from tqdm import tqdm
  WARRIOR_DECK = '''### WARRIOR_DECK
  # Class: RED
  # Format: Standard
  #
  # 2x (1) Charge
  # 2x (1) Murloc Raider
  # 2x (2) Execute
  # 2x (2) Frostwolf Grunt
  # 2x (2) Heroic Strike
  # 2x (2) Murloc Tidehunter
  # 2x (3) Fiery War Axe
  # 2x (3) Razorfen Hunter
  # 2x (3) Warsong Commander
  # 2x (3) Wolfrider
  # 2x (4) Dragonling Mechanic
  # 2x (4) Sen'jin Shieldmasta
  # 2x (5) Gurubashi Berserker
  # 2x (6) Boulderfist Ogre
  # 2x (6) Lord of the Arena
  #'''

  MAGE_DECK = '''### MAGE_DECK
  # Class: BLUE
  # Format: Standard
  #
  # 2x (1) Arcane Missiles
  # 2x (1) Murloc Raider
  # 2x (2) Arcane Explosion
  # 2x (2) Bloodfen Raptor
  # 2x (2) Novice Engineer
  # 2x (2) River Crocolisk
  # 2x (3) Arcane Intellect
  # 2x (3) Raid Leader
  # 2x (3) Wolfrider
  # 2x (4) Fireball
  # 2x (4) Oasis Snapjaw
  # 2x (4) Polymorph
  # 2x (4) Sen'jin Shieldmasta
  # 2x (5) Nightblade
  # 2x (6) Boulderfist Ogre
  #'''


  gamesToSim = 100
  decks = [WARRIOR_DECK, MAGE_DECK]
  behaviours = ['GameStateValueBehaviour', 'GameStateValueBehaviour']
  with Context() as context:
      test_results = list(tqdm(simulate(context=context, decks=decks, number=gamesToSim, behaviours=behaviours, reduce=False)))

      winrates = [sum(game['results'][i]['WIN_RATE'] for game in test_results) for i in [0,1]]
      wr = winrates[0]/sum(winrates)*100
      print(f'Winrates: GSVB wins {wr}% ')

# tryout()
# get_winrates()
get_histogram()