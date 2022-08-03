from spellsource.utils import simulate
from spellsource.context import Context
import json
from tqdm import tqdm

def sim_full_game(attack, hp, mana, taunt, lifesteal, charge):

  DRUID_DECK = '''### DRUID_DECK
  # Class: BROWN
  # Format: Standard
  # 2x Innervate
  # 2x Claw
  # 2x Elven Archer
  # 2x Mark of the Wild
  # 2x River Crocolisk
  # 2x Wild Growth
  # 2x Healing Touch
  # 2x Silverback Patriarch
  # 2x Chillwind Yeti
  # 2x Oasis Snapjaw
  # 2x Darkscale Healer
  # 2x Nightblade
  # 2x Boulderfist Ogre
  # 2x Lord of the Arena
  # 2x Core Hound
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

  MAGE_DECK = '''### MAGE_DECK
  # Class: BLUE
  # Format: Standard
  # 2x Arcane Explosion
  # 2x Arcane Intellect
  # 2x Arcane Missiles
  # 2x Bloodfen Raptor
  # 2x Boulderfist Ogre
  # 2x Fireball
  # 2x Murloc Raider
  # 2x Nightblade
  # 2x Novice Engineer
  # 2x Oasis Snapjaw
  # 2x Polymorph
  # 2x Raid Leader
  # 6x Custom Card
  #'''



  FULL_THIRTY = '''### MAGE_DECK
  # Class: BLUE
  # Format: Standard
  # 30x Custom Card
  #'''

  CARD_CUSTOM = {
    "baseManaCost": mana,
    "baseHp": hp,
    "baseAttack": attack,
    "attributes": {
        "TAUNT": taunt,
        "LIFESTEAL": lifesteal,
        "CHARGE": charge
    },
    "name": "Custom Card",
    "type": "MINION",
    "rarity": "COMMON",
    "description": "Custom card",
    "collectible": True,
    "set": "CUSTOM",
    "fileFormatVersion": 1
  }

  CARD_CUSTOM = json.dumps(CARD_CUSTOM)
  custom_cards = [CARD_CUSTOM]

  with Context() as ctx:
      # Add the card
      cardId = None
      for c in custom_cards:
        cardId = ctx.CardCatalogue.addOrReplaceCard(c)
  
      # Create new instances of the bot, random is faster
      player1_ai = ctx.behaviour.GameStateValueBehaviour()
      player2_ai = ctx.behaviour.GameStateValueBehaviour()
      # ctx.behaviour.PlayGameLogicRandomBehaviour()

      game_context = ctx.GameContext.fromDeckLists([MAGE_DECK, WARRIOR_DECK])
      # set the bots
      game_context.setBehaviour(ctx.GameContext.PLAYER_1, player1_ai)
      game_context.setBehaviour(ctx.GameContext.PLAYER_2, player2_ai)
      
      
      # assert game_context.getPlayer(ctx.GameContext.PLAYER_1).getDeck().containsCard(cardId)
      # for entity in game_context.getPlayer(ctx.GameContext.PLAYER_1).getDeck():
      #   print(entity.getSourceCard().getCardId())



      # set the seed
      # game_context.setLogic(ctx.GameLogic(10101))
      game_context.play()
      assert game_context.updateAndGetGameOver()
      # Inspect and print the game context
      # hero1 = game_context.getPlayer(ctx.GameContext.PLAYER_1).getHero()
      # hero2 = game_context.getPlayer(ctx.GameContext.PLAYER_2).getHero()
      # print(hero1)
      # print(hero2)

      grave = [entity.getSourceCard().getCardId() for entity in game_context.getPlayer(ctx.GameContext.PLAYER_1).getGraveyard()]
      victory = True
      card_played = False
      for card in grave:
        if card == 'hero_jaina':
          victory = False
        elif card == 'minion_custom_card':
          card_played = True
      
      print("Win: " + str(victory))
      print("Card played: " + str(card_played))


for i in tqdm(range(100)):
  sim_full_game(4,4,6, False, False, False)
