from card import Card
from condition import Condition
from enums import *
from effects import *
from card_generator import make_random_card
from copy import deepcopy
from dynamics import *


def get_utility_card(utility_card):
  the_coin = Card(name="The Coin", collectable=False, card_type=CardTypes.SPELL, manacost=0,
          effect=GainMana(value=Constant(1), method=Methods.TARGETED,
                  duration=Durations.TURN, target=Targets.HERO, owner_filter=OwnerFilters.FRIENDLY))
  utility_cards = {"Coin": the_coin}
  return utility_cards[utility_card]


def get_hero_power(hero_class):
  steady_shot = Card(name="Steady Shot", collectable=False, card_type=CardTypes.HERO_POWER, manacost=2,
              effect=DealDamage(value=Constant(2), method=Methods.ALL,
                        target=Targets.HERO, owner_filter=OwnerFilters.ENEMY))
  fireblast = Card(name="Fireblast", collectable=False, card_type=CardTypes.HERO_POWER, manacost=2,
           effect=DealDamage(value=Constant(1), method=Methods.TARGETED, target=Targets.MINION_OR_HERO,
                     owner_filter=OwnerFilters.ALL))
  hero_powers = {Classes.HUNTER: steady_shot, Classes.MAGE: fireblast}
  return hero_powers[hero_class]


def get_hunter_cards():

  snipe = Card(name="Snipe", card_type=CardTypes.SECRET, manacost=2,\
              effect=DealDamage(value=Constant(4), trigger=Triggers.ENEMY_MINION_SUMMONED, method=Methods.TRIGGERER, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY))

  hunter_cards = [snipe]

  return hunter_cards


def get_op_cards():
  op_cards = []
  return op_cards

def get_basic_cards():
  # Basic one drops
  elven_archer = Card(name="Elven Archer", card_type=CardTypes.MINION, manacost=1, attack=1, health=1,\
                      effect=DealDamage(value=Constant(1), trigger=Triggers.BATTLECRY, method=Methods.TARGETED, owner_filter=OwnerFilters.ALL, target=Targets.MINION_OR_HERO))
  goldshire_footman = Card(name="Goldshire Footman", card_type=CardTypes.MINION, manacost=1, attack=1, health=2, attributes=[Attributes.TAUNT])
  grimscale_oracle = Card(name="Grimscale Oracle", card_type=CardTypes.MINION, creature_type=CreatureTypes.MURLOC, manacost=1, attack=1, health=1,\
                          effect=ChangeStats(value=(Constant(1),Constant(0)), method=Methods.ALL, trigger=Triggers.AURA, owner_filter=OwnerFilters.ALL, target=Targets.MINION, type_filter=CreatureTypes.MURLOC))
  murloc_raider = Card(name="Murloc Raider", card_type=CardTypes.MINION, manacost=1, attack=2, health=1, creature_type=CreatureTypes.MURLOC)
  stonetusk_boar = Card(name="Stonetusk Boar", card_type=CardTypes.MINION, manacost=1, attack=1, health=1, creature_type=CreatureTypes.BEAST, attributes=[Attributes.CHARGE])
  voodoo_doctor = Card(name="Voodoo Doctor", card_type=CardTypes.MINION, manacost=1, attack=2, health=1,\
                       effect=RestoreHealth(value=Constant(2),trigger=Triggers.BATTLECRY, method=Methods.TARGETED, owner_filter=OwnerFilters.ALL, target=Targets.MINION_OR_HERO))
  # Basic two drops
  acidic_swamp_ooze = Card(name="Acidic Swamp Ooze", card_type=CardTypes.MINION, manacost=2, attack=3, health=2,\
                           effect=Destroy(trigger=Triggers.BATTLECRY, method=Methods.ALL, target=Targets.WEAPON, owner_filter=OwnerFilters.ENEMY))
  bloodfen_raptor = Card(name="Bloodfen Raptor", card_type=CardTypes.MINION, manacost=2, attack=3, health=2, creature_type=CreatureTypes.BEAST)
  bluegill_warrior = Card(name="Bluegill Warrior", card_type=CardTypes.MINION, manacost=2, attack=2, health=1, creature_type=CreatureTypes.MURLOC, attributes=[Attributes.CHARGE])
  frostwolf_grunt = Card(name="Frostwolf Grunt", card_type=CardTypes.MINION, manacost=2, attack=2, health=2, attributes=[Attributes.TAUNT])
  kobold_geomancer = Card(name="Kobold Geomancer", card_type=CardTypes.MINION, manacost=2, attack=2, health=2, attributes=[Attributes.SPELL_DAMAGE])
  murloc_tidehunter = Card(name="Murloc Tidehunter", card_type=CardTypes.MINION, manacost=2, attack=2, health=1, creature_type=CreatureTypes.MURLOC,\
                           effect=SummonToken(trigger=Triggers.BATTLECRY, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY,\
                           value=Card(name="Murloc Scout", collectable=False, card_type=CardTypes.MINION, manacost=0, attack=1, health=1, creature_type=CreatureTypes.MURLOC)))
  novice_engineer = Card(name="Novice Engineer", card_type=CardTypes.MINION, manacost=2, attack=1, health=1,\
                         effect=DrawCards(value=Constant(1), trigger=Triggers.BATTLECRY, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY))
  river_crocolisk = Card(name="River Crocolisk", card_type=CardTypes.MINION, manacost=2, attack=2, health=3, creature_type=CreatureTypes.BEAST)

  # Basic three drops
  dalaran_mage = Card(name="Dalaran Mage", card_type=CardTypes.MINION, manacost=3, attack=1, health=4, attributes=[Attributes.SPELL_DAMAGE])
  ironforge_rifleman = Card(name="Ironforge Rifleman", card_type=CardTypes.MINION, manacost=3, attack=2, health=2,\
                      effect=DealDamage(value=Constant(1), trigger=Triggers.BATTLECRY, method=Methods.TARGETED, owner_filter=OwnerFilters.ALL, target=Targets.MINION_OR_HERO))
  ironfur_grizzly = Card(name="Ironfur Grizzly", card_type=CardTypes.MINION, manacost=3, attack=3, health=3, creature_type=CreatureTypes.BEAST, attributes=[Attributes.TAUNT])
  magma_rager = Card(name="Magma Rager", card_type=CardTypes.MINION, manacost=3, attack=5, health=1)
  raid_leader = Card(name="Raid Leader", card_type=CardTypes.MINION, manacost=3, attack=2, health=2,\
                     effect=ChangeStats(value=(Constant(1),Constant(0)), trigger=Triggers.AURA, method=Methods.ALL, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY))
  razorfen_hunter = Card(name="Razorfen Hunter", card_type=CardTypes.MINION, manacost=3, attack=2, health=3,\
                           effect=SummonToken(trigger=Triggers.BATTLECRY, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY,\
                           value=Card(name="Boar", collectable=False, card_type=CardTypes.MINION, manacost=1, attack=1, health=1, creature_type=CreatureTypes.BEAST)))
  shattered_sun_cleric = Card(name="Shattered Sun Cleric", card_type=CardTypes.MINION, manacost=3, attack=3, health=2,\
                              effect=ChangeStats(value=(Constant(1),Constant(1)), trigger=Triggers.BATTLECRY, method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  silverback_patriarch = Card(name="Silverback Patriarch", card_type=CardTypes.MINION, manacost=3, attack=1, health=4, creature_type=CreatureTypes.BEAST, attributes=[Attributes.TAUNT])
  wolfrider = Card(name="Wolfrider", card_type=CardTypes.MINION, manacost=3, attack=3, health=1, attributes=[Attributes.CHARGE])

  # Basic four drops
  chillwind_yeti = Card(name="Chillwind Yeti", card_type=CardTypes.MINION, manacost=4, attack=4, health=5)
  dragonling_mechanic = Card(name="Dragonling Mechanic", card_type=CardTypes.MINION, manacost=4, attack=2, health=4,\
                             effect=SummonToken(trigger=Triggers.BATTLECRY, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY,\
                             value=Card(name="Mechanical Dragonling", collectable=False, card_type=CardTypes.MINION, manacost=1, attack=2, health=1, creature_type=CreatureTypes.MECH)))
  gnomish_inventor = Card(name="Gnomish Inventor", card_type=CardTypes.MINION, manacost=4, attack=2, health=4,\
                         effect=DrawCards(value=Constant(1), trigger=Triggers.BATTLECRY, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY))
  oasis_snapjaw = Card(name="Oasis Snapjaw", card_type=CardTypes.MINION, manacost=4, attack=2, health=7, creature_type=CreatureTypes.BEAST)
  ogre_magi = Card(name="Ogre Magi", card_type=CardTypes.MINION, manacost=4, attack=4, health=4, attributes=[Attributes.SPELL_DAMAGE])
  senjin_shieldmasta = Card(name="Sen'jin Shieldmasta", card_type=CardTypes.MINION, manacost=4, attack=3, health=5, attributes=[Attributes.TAUNT])
  stormwind_knight = Card(name="Stormwind Knight", card_type=CardTypes.MINION, manacost=4, attack=2, health=5, attributes=[Attributes.CHARGE])

  # Basic five drops
  booty_bay_bodyguard = Card(name="Booty Bay Bodyguard", card_type=CardTypes.MINION, manacost=5, attack=5, health=4, attributes=[Attributes.TAUNT])
  darkscale_healer = Card(name="Darkscale Healer", card_type=CardTypes.MINION, manacost=5, attack=4, health=5,\
                          effect=RestoreHealth(value=Constant(2), trigger=Triggers.BATTLECRY, method=Methods.ALL, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.FRIENDLY))
  frostwolf_warlord = Card(name="Frostwolf Warlord", card_type=CardTypes.MINION, manacost=5, attack=4, health=4,\
                           effect=ChangeStats(value=(NumOtherFriendlyMinions(), NumOtherFriendlyMinions()), trigger=Triggers.BATTLECRY, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  gurubashi_berserker = Card(name="Gurubashi Berserker", card_type=CardTypes.MINION, manacost=5, attack=2, health=7,\
                             effect=ChangeStats(value=(Constant(3), Constant(0)), trigger=Triggers.SELF_DAMAGE_TAKEN, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  nightblade = Card(name="Nightblade", card_type=CardTypes.MINION, manacost=5, attack=4, health=4,\
                    effect=DealDamage(value=Constant(3), trigger=Triggers.BATTLECRY, method=Methods.ALL, target=Targets.HERO, owner_filter=OwnerFilters.ENEMY))
  stormpike_commando = Card(name="Stormpike Commando", card_type=CardTypes.MINION, manacost=5, attack=4, health=2,\
                            effect=DealDamage(value=Constant(2), trigger=Triggers.BATTLECRY, method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL))

  # Basic six drops
  archmage = Card(name="Archmage", card_type=CardTypes.MINION, manacost=6, attack=4, health=7, attributes=[Attributes.SPELL_DAMAGE])
  boulderfist_ogre = Card(name="Boulderfist Ogre", card_type=CardTypes.MINION, manacost=6, attack=6, health=7)
  lord_of_the_arena = Card(name="Lord of the Arena", card_type=CardTypes.MINION, manacost=6, attack=6, health=5, attributes=[Attributes.TAUNT])
  reckless_rocketeer = Card(name="Reckless Rocketeer", card_type=CardTypes.MINION, manacost=6, attack=5, health=2, attributes=[Attributes.CHARGE])

  #Basic seven drops
  core_hound = Card(name="Core Hound", card_type=CardTypes.MINION, creature_type=CreatureTypes.BEAST, manacost=7, attack=9, health=5)
  stormwind_champion = Card(name="Stormwind Champion", card_type=CardTypes.MINION, manacost=7, attack=6, health=6,\
                            effect=ChangeStats(value=(Constant(1), Constant(1)), trigger=Triggers.AURA, method=Methods.ALL, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY))
  war_golem = Card(name="War Golem", card_type=CardTypes.MINION, manacost=7, attack=7, health=7)


  basic_one_drops = [elven_archer, goldshire_footman, grimscale_oracle, murloc_raider, stonetusk_boar, voodoo_doctor]
  basic_two_drops = [acidic_swamp_ooze, bloodfen_raptor, bluegill_warrior, frostwolf_grunt, kobold_geomancer, murloc_tidehunter, novice_engineer, river_crocolisk]
  basic_three_drops = [dalaran_mage, ironforge_rifleman, ironfur_grizzly, magma_rager, raid_leader, razorfen_hunter, shattered_sun_cleric, silverback_patriarch, wolfrider]
  basic_four_drops = [chillwind_yeti, dragonling_mechanic, gnomish_inventor, oasis_snapjaw, ogre_magi, senjin_shieldmasta, stormwind_knight]
  basic_five_drops = [booty_bay_bodyguard, darkscale_healer, frostwolf_warlord, gurubashi_berserker, nightblade, stormpike_commando]
  basic_six_drops = [archmage, boulderfist_ogre, lord_of_the_arena, reckless_rocketeer]
  basic_seven_drops = [core_hound, stormwind_champion, war_golem]
  return basic_one_drops + basic_two_drops + basic_three_drops + basic_four_drops + basic_five_drops + basic_six_drops + basic_seven_drops

def get_common_cards():
  # Common one drops
  wisp = Card(name="Wisp", card_type=CardTypes.MINION,
        manacost=0, attack=1, health=1)
  abusive_sergeant = Card(name="Abusive Sergeant", card_type=CardTypes.MINION, manacost=1, attack=1, health=1,
              effect=ChangeStats(value=(Constant(2), Constant(0)), method=Methods.TARGETED,
                         target=Targets.MINION, owner_filter=OwnerFilters.ALL, duration=Durations.TURN,
                         trigger=Triggers.BATTLECRY, type_filter=CreatureTypes.ALL))
  argent_squire = Card(name="Argent Squire", card_type=CardTypes.MINION, manacost=1, attack=1, health=1,
             attributes=[Attributes.DIVINE_SHIELD])
  leper_gnome = Card(name="Leper Gnome", card_type=CardTypes.MINION, manacost=1, attack=2, health=1,
             effect=DealDamage(value=Constant(2), method=Methods.ALL, target=Targets.HERO,
                     owner_filter=OwnerFilters.ENEMY, trigger=Triggers.DEATHRATTLE))
  shieldbearer = Card(name="Shieldbearer", card_type=CardTypes.MINION,
            manacost=1, attack=0, health=4, attributes=[Attributes.TAUNT])
  southsea_deckhand = Card(name="Southsea Deckhand", card_type=CardTypes.MINION, creature_type=CreatureTypes.PIRATE, manacost=1, attack=2, health=1,
               condition=Condition(requirement=Condition.has_weapon, result={'attributes': [Attributes.CHARGE]}))
  worgen_infiltrator = Card(name="Worgen Infiltrator", card_type=CardTypes.MINION,
                manacost=1, attack=2, health=1, attributes=[Attributes.STEALTH])
  young_dragonhawk = Card(name="Young Dragonhawk", card_type=CardTypes.MINION,
              manacost=1, attack=1, health=1, attributes=[Attributes.WINDFURY])

  # Common two drops
  amani_berserker = Card(name="Amani Berserker", card_type=CardTypes.MINION, manacost=2, attack=2,
               health=3, condition=Condition(requirement=Condition.damaged, result={'temp_attack': 3}))
  bloodsail_raider = Card(name="Bloodsail Raider", card_type=CardTypes.MINION, manacost=2, attack=2, health=3, creature_type=CreatureTypes.PIRATE,\
              effect=ChangeStats(trigger=Triggers.BATTLECRY, value=(FriendlyWeaponAttack(), Constant(0)), method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
      
  dire_wolf_alpha = Card(name="Dire Wolf Alpha", card_type=CardTypes.MINION, manacost=2, attack=2, health=2, effect=ChangeStats(value=(Constant(1), Constant(0)), trigger=Triggers.AURA, method=Methods.ADJACENT,
               target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, type_filter=CreatureTypes.ALL))  # gives all minions +1 including self, nerf attack by 1, mana by 1?
  faerie_dragon = Card(name="Faerie Dragon", card_type=CardTypes.MINION, creature_type=CreatureTypes.DRAGON,\
             manacost=2, attack=3, health=2, attributes=[Attributes.HEXPROOF])
  ironbeak_owl = Card(name="Ironbeak Owl", card_type=CardTypes.MINION, creature_type=CreatureTypes.BEAST, manacost=2, attack=2, health=1,
            effect=Silence(method=Methods.TARGETED, owner_filter=OwnerFilters.ALL, target=Targets.MINION, trigger=Triggers.BATTLECRY))
  loot_hoarder = Card(name="Loot Hoarder", card_type=CardTypes.MINION, manacost=2, attack=2, health=1,
            effect=DrawCards(value=Constant(1), method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.DEATHRATTLE))
  mad_bomber = Card(name="Mad Bomber", card_type=CardTypes.MINION, manacost=2, attack=3, health=2,
            effect=DealDamage(value=Constant(1), random_count=3, method=Methods.RANDOMLY, target=Targets.MINION_OR_HERO,
                    owner_filter=OwnerFilters.ALL, trigger=Triggers.BATTLECRY))
  youthful_brewmaster = Card(name="Youthful Brewmaster", card_type=CardTypes.MINION, manacost=2, attack=3, health=2,
                 effect=ReturnToHand(method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.BATTLECRY))

  # Common three drops
  acolyte_of_pain = Card(name="Acolyte of Pain", card_type=CardTypes.MINION, manacost=3, attack=1, health=3,\
                             effect=DrawCards(value=Constant(1), trigger=Triggers.SELF_DAMAGE_TAKEN, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY))
  earthen_ring_farseer = Card(name="Earthen Ring Farseer", card_type=CardTypes.MINION, manacost=3, attack=3, health=3,
                effect=RestoreHealth(value=Constant(3), method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL, trigger=Triggers.BATTLECRY))
  flesheating_ghoul = Card(name="Flesheating Ghoul", card_type=CardTypes.MINION, manacost=3, attack=2, health=3,
               effect=ChangeStats(value=(Constant(1), Constant(0)), method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.ANY_MINION_DIES))
  harvest_golem = Card(name="Harvest Golem", card_type=CardTypes.MINION, creature_type=CreatureTypes.MECH, manacost=3, attack=2, health=3,
             effect=SummonToken(value=Card(name="Damaged Golem", collectable=False, card_type=CardTypes.MINION, creature_type=CreatureTypes.MECH, manacost=1, attack=2, health=1),
                      method=Methods.TARGETED, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.DEATHRATTLE))
  jungle_panther = Card(name="Jungle Panther", card_type=CardTypes.MINION,
              creature_type=CreatureTypes.BEAST, manacost=3, attack=4, health=2, attributes=[Attributes.STEALTH])
  raging_worgen = Card(name="Raging Worgen", card_type=CardTypes.MINION, manacost=3, attack=3, health=3, condition=Condition(
    requirement=Condition.damaged, result={'temp_attack': 1, 'attributes': [Attributes.WINDFURY]}))
  scarlet_crusader = Card(name="Scarlet Crusader", card_type=CardTypes.MINION,
              manacost=3, attack=3, health=1, attributes=[Attributes.DIVINE_SHIELD])
  tauren_warrior = Card(name="Tauren Warrior", card_type=CardTypes.MINION, manacost=3, attack=2, health=3, attributes=[
              Attributes.TAUNT], condition=Condition(requirement=Condition.damaged, result={'temp_attack': 3}))
  thrallmar_farseer = Card(name="Thrallmar Farseer", card_type=CardTypes.MINION,
               manacost=3, attack=2, health=3, attributes=[Attributes.WINDFURY])

  # Common four drops
  ancient_brewmaster = Card(name="Ancient Brewmaster", card_type=CardTypes.MINION, manacost=4, attack=5, health=4,
                effect=ReturnToHand(method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.BATTLECRY))
  cult_master = Card(name="Cult Master", card_type=CardTypes.MINION, manacost=4, attack=4, health=2,
             effect=DrawCards(value=Constant(1), method=Methods.TARGETED, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.FRIENDLY_MINION_DIES))
  dark_iron_dwarf = Card(name="Dark Iron Dwarf", card_type=CardTypes.MINION, manacost=4, attack=4, health=4,
               effect=ChangeStats(value=(Constant(2), Constant(0)), method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.ALL, duration=Durations.TURN, trigger=Triggers.BATTLECRY))
  dread_corsair = Card(name="Dread Corsair", card_type=CardTypes.MINION, manacost=4, attack=3, health=3, creature_type=CreatureTypes.PIRATE,
             effect=ChangeCost(value=Multiply(FriendlyWeaponAttack(), Constant(-1)), method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.AURA))
  mogushan_warden = Card(name="Mogushan Warden", card_type=CardTypes.MINION,
               manacost=4, attack=1, health=7, attributes=[Attributes.TAUNT])
  silvermoon_guardian = Card(name="Silvermoon Guardian", card_type=CardTypes.MINION,
                 manacost=4, attack=3, health=3, attributes=[Attributes.DIVINE_SHIELD])
  spellbreaker = Card(name="Spellbreaker", card_type=CardTypes.MINION, manacost=4, attack=4, health=3,
            effect=Silence(method=Methods.TARGETED, owner_filter=OwnerFilters.ALL, target=Targets.MINION, trigger=Triggers.BATTLECRY))
  
  # Common five drops
  fen_creeper = Card(name="Fen Creeper", card_type=CardTypes.MINION,
             manacost=5, attack=3, health=6, attributes=[Attributes.TAUNT])
  silver_hand_knight = Card(name="Silver Hand Knight", card_type=CardTypes.MINION, manacost=5, attack=4, health=4,
                effect=SummonToken(value=Card(name="Squire", collectable=False, card_type=CardTypes.MINION, manacost=1, attack=2, health=2),
                         method=Methods.TARGETED, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.BATTLECRY))
  spiteful_smith = Card(name="Spiteful Smith", card_type=CardTypes.MINION, manacost=5, attack=4, health=6,
              effect=ChangeStats(value=(Constant(2), Constant(0)), trigger=Triggers.AURA, owner_filter=OwnerFilters.FRIENDLY, target=Targets.WEAPON, method=Methods.ALL))
  stranglethorn_tiger = Card(name="Stranglethorn Tiger", card_type=CardTypes.MINION, creature_type=CreatureTypes.BEAST, manacost=5,attack=5, health=5, attributes=[Attributes.STEALTH])
  
  venture_co_mercenary = Card(name="Venture Co. Mercenary", card_type=CardTypes.MINION, manacost=5, attack=7, health=6,
                effect=ChangeCost(value=Constant(3), target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, method=Methods.ALL, trigger=Triggers.AURA))

  # Common six drops
  frost_elemental = Card(name="Frost Elemental", card_type=CardTypes.MINION, creature_type=CreatureTypes.ELEMENTAL, manacost=6, attack=5, health=5,\
            effect=GiveKeyword(value=Attributes.FROZEN, trigger=Triggers.BATTLECRY, method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL, duration=Durations.PERMANENTLY))
  priestess_of_elune = Card(name="Priestess of Elune", card_type=CardTypes.MINION, manacost=6, attack=5, health=4,\
                  effect=RestoreHealth(value=Constant(4), trigger=Triggers.BATTLECRY, method=Methods.ALL, target=Targets.HERO, owner_filter=OwnerFilters.FRIENDLY))
  windfury_harpy = Card(name="Windfury Harpy", card_type=CardTypes.MINION, manacost=6, attack=4, health=5, attributes=[Attributes.WINDFURY])

  # Combine
  common_one_drops = [wisp, abusive_sergeant, argent_squire, leper_gnome,
            shieldbearer, southsea_deckhand, worgen_infiltrator, young_dragonhawk]
  common_two_drops = [amani_berserker, bloodsail_raider, dire_wolf_alpha,
            faerie_dragon, ironbeak_owl, loot_hoarder, mad_bomber, youthful_brewmaster]
  common_three_drops = [acolyte_of_pain, earthen_ring_farseer, flesheating_ghoul, harvest_golem,
              jungle_panther, raging_worgen, scarlet_crusader, tauren_warrior, thrallmar_farseer]
  common_four_drops = [ancient_brewmaster, cult_master, dark_iron_dwarf,
             dread_corsair, mogushan_warden, silvermoon_guardian, spellbreaker]
  common_five_drops = [fen_creeper, silver_hand_knight, spiteful_smith, stranglethorn_tiger, venture_co_mercenary]
  common_six_drops = [frost_elemental, priestess_of_elune, windfury_harpy]
  return common_one_drops + common_two_drops + common_three_drops + common_four_drops + common_five_drops + common_six_drops

def get_rare_cards():
  # Rare one drops
  angry_chicken = Card(name="Angry Chicken", card_type=CardTypes.MINION, manacost=1, attack=1, health=1, creature_type=CreatureTypes.BEAST,\
                       condition=Condition(Condition.damaged, {'temp_attack': 5}))
  
  bloodsail_corsair = Card(name="Bloodsail Corsair", card_type=CardTypes.MINION, creature_type=CreatureTypes.PIRATE, manacost=1, attack=1, health=2,\
                           effect=DealDamage(value=Constant(1), trigger=Triggers.BATTLECRY, method=Methods.TARGETED, target=Targets.WEAPON, owner_filter=OwnerFilters.ENEMY))
  
  lightwarden = Card(name="Lightwarden", card_type=CardTypes.MINION, manacost=1, attack=1, health=2,\
                     effect=ChangeStats(value=(Constant(2),Constant(0)), trigger=Triggers.ANY_HEALED, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))

  murloc_tidecaller = Card(name="Murloc Tidecaller", card_type=CardTypes.MINION, creature_type=CreatureTypes.MURLOC, manacost=1, attack=1, health=2,\
                           effect=ChangeStats(value=(Constant(1),Constant(0)), method=Methods.SELF, trigger=Triggers.FRIENDLY_SAME_TYPE_SUMMONED, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
 
  secretkeeper = Card(name="Secretkeeper", card_type=CardTypes.MINION, manacost=1, attack=1, health=2,\
                      effect=ChangeStats(value=(Constant(1),Constant(1)), trigger=Triggers.ANY_SECRET_CAST, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  young_priestess = Card(name="Young Priestess", card_type=CardTypes.MINION, manacost=1, attack=2, health=1,\
                         effect=ChangeStats(value=(Constant(0),Constant(1)), trigger=Triggers.FRIENDLY_END_TURN, method=Methods.RANDOMLY, owner_filter=OwnerFilters.FRIENDLY, target=Targets.MINION, duration=Durations.PERMANENTLY))

  # Rare two drops
  ancient_watcher = Card(name="Ancient Watcher", card_type=CardTypes.MINION, manacost=2, attack=4, health=5, attributes=[Attributes.DEFENDER])
  crazed_alchemist = Card(name="Crazed Alchemist", card_type=CardTypes.MINION, manacost=2, attack=2, health=2,\
                          effect=SwapStats(trigger=Triggers.BATTLECRY, method=Methods.TARGETED, owner_filter=OwnerFilters.ALL, target=Targets.MINION))
  knife_juggler = Card(name="Knife Juggler", card_type=CardTypes.MINION, manacost=2, attack=3, health=2,\
                       effect=DealDamage(value=Constant(1), trigger=Triggers.FRIENDLY_MINION_SUMMONED, method=Methods.RANDOMLY, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ENEMY))
  mana_addict = Card(name="Mana Addict", card_type=CardTypes.MINION, manacost=2, attack=1, health=3,\
                     effect=ChangeStats(value=(Constant(2), Constant(0)), trigger=Triggers.FRIENDLY_SPELL_CAST, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.TURN))
  mana_wraith = Card(name="Mana Wraith", card_type=CardTypes.MINION, manacost=2, attack=2, health=2,
                effect=ChangeCost(value=Constant(1), target=Targets.MINION, owner_filter=OwnerFilters.ALL, method=Methods.ALL, trigger=Triggers.AURA))
  master_swordsmith = Card(name="Master Swordsmith", card_type=CardTypes.MINION, manacost=2, attack=1, health=3,\
                           effect=ChangeStats(value=(Constant(1), Constant(0)), trigger=Triggers.FRIENDLY_END_TURN, method=Methods.RANDOMLY, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  pint_sized_summoner = Card(name="Pint-Sized Summoner", card_type=CardTypes.MINION, manacost=2, attack=2, health=2,\
                             effect=ChangeCost(value=If(Equals(MinionsPlayed(), Constant(0)), Constant(-1), Constant(0)), trigger=Triggers.AURA, method=Methods.ALL, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY))
  sunfury_protector = Card(name="Sunfury Protector", card_type=CardTypes.MINION, manacost=2, attack=2, health=2,\
                          effect=GiveKeyword(value=Attributes.TAUNT, method=Methods.ADJACENT, target=Targets.MINION,
                          owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.BATTLECRY))
  wild_pyromancer = Card(name="Wild Pyromancer", card_type=CardTypes.MINION, manacost=2, attack=3, health=2,\
                        effect=DuelActionSelf(DealDamage(trigger=Triggers.FRIENDLY_SPELL_CAST, method=Methods.ALL, value=Constant(1), target=Targets.MINION, owner_filter=OwnerFilters.ALL),\
                                              DealDamage(trigger=Triggers.FRIENDLY_SPELL_CAST, method=Methods.SELF, value=Constant(1), target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY)))

  # Rare three drops
  alarm_o_bot = Card(name="Alarm-o-Bot", card_type=CardTypes.MINION, manacost=3, attack=0, health=3, creature_type=CreatureTypes.MECH,\
                     effect=SwapWithMinion(trigger=Triggers.FRIENDLY_UNTAP, method=Methods.RANDOMLY, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY))
  
  
  # Rare four drops
  defender_of_argus = Card(name="Defender of Argus", card_type=CardTypes.MINION, manacost=4, attack=2, health=3,
                          effect=DuelAction(ChangeStats(value=(Constant(1),Constant(1)), method=Methods.ADJACENT, target=Targets.MINION,
                          owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.BATTLECRY),
                          GiveKeyword(value=Attributes.TAUNT, method=Methods.ADJACENT, target=Targets.MINION,
                          owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.BATTLECRY)))

                    
  rare_one_drops = [angry_chicken, bloodsail_corsair, lightwarden, murloc_tidecaller, secretkeeper, young_priestess]
  rare_two_drops = [ancient_watcher, crazed_alchemist, knife_juggler, mana_addict, mana_wraith, master_swordsmith, pint_sized_summoner, sunfury_protector, wild_pyromancer]
  rare_three_drops = [alarm_o_bot]
  rare_four_drops = [defender_of_argus]
  rare_five_drops = []

  return rare_one_drops + rare_two_drops + rare_three_drops + rare_four_drops + rare_five_drops

def get_mage_cards():
  fireball = Card(name="Fireball", card_type=CardTypes.SPELL, manacost=4, effect=DealDamage(
    value=Constant(6), method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL))
  return [fireball]


def get_test_cards():
  all_dam = Card("All Damage", card_type=CardTypes.SPELL, manacost=0,
           effect=DealDamage(value=Constant(3), method=Methods.ALL, target=Targets.MINION_OR_HERO,
                   owner_filter=OwnerFilters.ALL)
           )
  generic_weapon = Card("Generic Weapon", card_type=CardTypes.WEAPON, manacost=1,
              attack=3, health=2)
  battlecry_weapon = Card("Battlecry Weapon", card_type=CardTypes.WEAPON, manacost=1, attack=3, health=2,
              effect=DealDamage(value=Constant(1), method=Methods.ALL, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL, trigger=Triggers.BATTLECRY))
  windfury_weapon = Card("Windfury Weapon", card_type=CardTypes.WEAPON,
               manacost=0, attack=2, health=2, attributes=[Attributes.WINDFURY])
  battlecry_reduce_cost = Card("Battlecry Reduce Cost", card_type=CardTypes.MINION, manacost=0, attack=0, health=1,
                 effect=ChangeCost(value=Constant(1), target=Targets.MINION_OR_SPELL, method=Methods.ALL, owner_filter=OwnerFilters.ENEMY, trigger=Triggers.BATTLECRY))
  test_cards = [all_dam, generic_weapon, battlecry_weapon,
          windfury_weapon, battlecry_reduce_cost]
  return test_cards

def get_random_cards(random_state):
  rand_cards = [make_random_card(i, random_state) for i in range(100)]
  return rand_cards

def build_pool(set_names, random_state):
  pool = []
  if CardSets.CLASSIC_NEUTRAL in set_names:
    pool.extend(get_basic_cards())
    pool.extend(get_common_cards())
    pool.extend(get_rare_cards())
  if CardSets.CLASSIC_HUNTER in set_names:
    pool.extend(get_hunter_cards())
  if CardSets.CLASSIC_MAGE in set_names:
    pool.extend(get_mage_cards())
  if CardSets.OP_CARDS in set_names:
    pool.extend(get_op_cards())
  if CardSets.TEST_CARDS in set_names:
    pool.extend(get_test_cards())
  if CardSets.RANDOM_CARDS in set_names:
    pool.extend(get_random_cards(random_state))
  return pool
