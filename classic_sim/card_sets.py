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
  excess_mana = Card(name="Excess Mana", collectable=False, card_type=CardTypes.SPELL, manacost=0,
          effect=DrawCards(value=Constant(1), method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY))
  utility_cards = {"Coin": the_coin, "Excess Mana": excess_mana}
  return utility_cards[utility_card]


def get_hero_power(hero_class):
  steady_shot = Card(name="Steady Shot", collectable=False, card_type=CardTypes.HERO_POWER, manacost=2,
              effect=DealDamage(value=Constant(2), method=Methods.ALL,
                        target=Targets.HERO, owner_filter=OwnerFilters.ENEMY))
  fireblast = Card(name="Fireblast", collectable=False, card_type=CardTypes.HERO_POWER, manacost=2,
           effect=DealDamage(value=Constant(1), method=Methods.TARGETED, target=Targets.MINION_OR_HERO,
                     owner_filter=OwnerFilters.ALL))
  armor_up = Card(name="Armor Up!", card_type=CardTypes.HERO_POWER, collectable=False, manacost=2,\
                  effect=GainArmor(value=Constant(2), method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY))
  hero_powers = {Classes.HUNTER: steady_shot, Classes.MAGE: fireblast, Classes.WARRIOR: armor_up}
  return hero_powers[hero_class]




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
                           value=(Constant(1), Constant(Card(name="Murloc Scout", collectable=False, card_type=CardTypes.MINION, manacost=0, attack=1, health=1, creature_type=CreatureTypes.MURLOC)))))
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
                           value=(Constant(1), Constant(Card(name="Boar", collectable=False, card_type=CardTypes.MINION, manacost=1, attack=1, health=1, creature_type=CreatureTypes.BEAST)))))
  shattered_sun_cleric = Card(name="Shattered Sun Cleric", card_type=CardTypes.MINION, manacost=3, attack=3, health=2,\
                              effect=ChangeStats(value=(Constant(1),Constant(1)), trigger=Triggers.BATTLECRY, method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  silverback_patriarch = Card(name="Silverback Patriarch", card_type=CardTypes.MINION, manacost=3, attack=1, health=4, creature_type=CreatureTypes.BEAST, attributes=[Attributes.TAUNT])
  wolfrider = Card(name="Wolfrider", card_type=CardTypes.MINION, manacost=3, attack=3, health=1, attributes=[Attributes.CHARGE])

  # Basic four drops
  chillwind_yeti = Card(name="Chillwind Yeti", card_type=CardTypes.MINION, manacost=4, attack=4, health=5)
  dragonling_mechanic = Card(name="Dragonling Mechanic", card_type=CardTypes.MINION, manacost=4, attack=2, health=4,\
                             effect=SummonToken(trigger=Triggers.BATTLECRY, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY,\
                             value=(Constant(1), Constant(Card(name="Mechanical Dragonling", collectable=False, card_type=CardTypes.MINION, manacost=1, attack=2, health=1, creature_type=CreatureTypes.MECH)))))
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
                           effect=ChangeStats(value=(NumOtherMinions(OwnerFilters.FRIENDLY), NumOtherMinions(OwnerFilters.FRIENDLY)), trigger=Triggers.BATTLECRY, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
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
             effect=SummonToken(value=(Constant(1), Constant(Card(name="Damaged Golem", collectable=False, card_type=CardTypes.MINION, creature_type=CreatureTypes.MECH, manacost=1, attack=2, health=1))),
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
                effect=SummonToken(value=(Constant(1), Constant(Card(name="Squire", collectable=False, card_type=CardTypes.MINION, manacost=1, attack=2, health=2))),
                         method=Methods.TARGETED, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.BATTLECRY))
  spiteful_smith = Card(name="Spiteful Smith", card_type=CardTypes.MINION, manacost=5, attack=4, health=6,
              effect=ChangeStats(value=(If(Damaged(), Constant(2), Constant(0)), Constant(0)), trigger=Triggers.AURA, owner_filter=OwnerFilters.FRIENDLY, target=Targets.WEAPON, method=Methods.ALL))
  stranglethorn_tiger = Card(name="Stranglethorn Tiger", card_type=CardTypes.MINION, creature_type=CreatureTypes.BEAST, manacost=5,attack=5, health=5, attributes=[Attributes.STEALTH])
  
  venture_co_mercenary = Card(name="Venture Co. Mercenary", card_type=CardTypes.MINION, manacost=5, attack=7, health=6,
                effect=ChangeCost(value=Constant(3), target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, method=Methods.ALL, trigger=Triggers.AURA))

  # Common six drops
  frost_elemental = Card(name="Frost Elemental", card_type=CardTypes.MINION, creature_type=CreatureTypes.ELEMENTAL, manacost=6, attack=5, health=5,\
            effect=GiveAttribute(value=Constant(Attributes.FROZEN), trigger=Triggers.BATTLECRY, method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL, duration=Durations.PERMANENTLY))
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
                          effect=GiveAttribute(value=Constant(Attributes.TAUNT), method=Methods.ADJACENT, target=Targets.MINION,
                          owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.BATTLECRY))
  wild_pyromancer = Card(name="Wild Pyromancer", card_type=CardTypes.MINION, manacost=2, attack=3, health=2,\
                        effect=DualEffectSelf(DealDamage(trigger=Triggers.FRIENDLY_SPELL_CAST, method=Methods.ALL, value=Constant(1), target=Targets.MINION, owner_filter=OwnerFilters.ALL),\
                                              DealDamage(trigger=Triggers.FRIENDLY_SPELL_CAST, method=Methods.SELF, value=Constant(1), target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY)))

  # Rare three drops
  alarm_o_bot = Card(name="Alarm-o-Bot", card_type=CardTypes.MINION, manacost=3, attack=0, health=3, creature_type=CreatureTypes.MECH,\
                     effect=SwapWithMinion(trigger=Triggers.FRIENDLY_UNTAP, method=Methods.RANDOMLY, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY))
  arcane_golem = Card(name="Arcane Golem", card_type=CardTypes.MINION, manacost=3, attack=4, health=2, attributes=[Attributes.CHARGE],\
                       effect=GainMana(value=Constant(1), method=Methods.ALL, trigger=Triggers.BATTLECRY, owner_filter=OwnerFilters.ENEMY, duration=Durations.PERMANENTLY))
  coldlight_oracle = Card(name="Coldlight Oracle", card_type=CardTypes.MINION, manacost=3, attack=2, health=2, creature_type=CreatureTypes.MURLOC,\
                          effect=DrawCards(value=Constant(2), trigger=Triggers.BATTLECRY, method=Methods.ALL, owner_filter=OwnerFilters.ALL))
  coldlight_seer = Card(name="Coldlight Seer", card_type=CardTypes.MINION, manacost=3, attack=2, health=3, creature_type=CreatureTypes.MURLOC,\
                        effect=ChangeStats(value=(Constant(0), Constant(2)), trigger=Triggers.BATTLECRY, method=Methods.ALL,\
                                           target=Targets.MINION, owner_filter=OwnerFilters.ALL, type_filter=CreatureTypes.MURLOC, duration=Durations.PERMANENTLY))
  demolisher = Card(name="Demolisher", card_type=CardTypes.MINION, manacost=3, attack=1, health=3, creature_type=CreatureTypes.MECH,\
                    effect=DealDamage(value=Constant(2), method=Methods.RANDOMLY, trigger=Triggers.FRIENDLY_UNTAP, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY))
  emperor_cobra = Card(name="Emperor Cobra", card_type=CardTypes.MINION, manacost=3, attack=2, health=3, creature_type=CreatureTypes.BEAST, attributes=[Attributes.POISONOUS])
  imp_master = Card(name="Imp Master", card_type=CardTypes.MINION, manacost=3, attack=1, health=5,\
                    effect=DualEffectSelf(SummonToken(trigger=Triggers.FRIENDLY_END_TURN, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY,\
                                          value=(Constant(1), Constant(Card(name="Imp", card_type=CardTypes.MINION, collectable=False, manacost=1, attack=1, health=1, creature_type=CreatureTypes.DEMON)))),\
                                          DealDamage(value=Constant(1),method=Methods.SELF, trigger=Triggers.FRIENDLY_END_TURN, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY)))
  injured_blademaster = Card(name="Injured Blademaster", card_type=CardTypes.MINION, manacost=3, attack=4, health=7,\
                             effect=DealDamage(value=Constant(4), trigger=Triggers.BATTLECRY, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY))
  mind_control_tech = Card(name="Mind Control Tech", card_type=CardTypes.MINION, manacost=3, attack=3, health=3) #not implementing stealing
  questing_adventurer = Card(name="Questing Adventurer", card_type=CardTypes.MINION, manacost=3, attack=2, health=2,\
                             effect=ChangeStats(value=(Constant(1), Constant(1)), trigger=Triggers.FRIENDLY_CARD_PLAYED, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))

  # Rare four drops
  ancient_mage = Card(name="Ancient Mage", card_type=CardTypes.MINION, manacost=4, attack=2, health=5,\
                      effect=GiveAttribute(value=Constant(Attributes.SPELL_DAMAGE), method=Methods.ADJACENT, trigger=Triggers.BATTLECRY, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  defender_of_argus = Card(name="Defender of Argus", card_type=CardTypes.MINION, manacost=4, attack=2, health=3,
                          effect=DualEffect(ChangeStats(value=(Constant(1),Constant(1)), method=Methods.ADJACENT, target=Targets.MINION,
                          owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.BATTLECRY),
                          GiveAttribute(value=Constant(Attributes.TAUNT), method=Methods.ADJACENT, target=Targets.MINION,
                          owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.BATTLECRY)))
  twilight_drake = Card(name="Twilight Drake", card_type=CardTypes.MINION, manacost=4, attack=4, health=1, creature_type=CreatureTypes.DRAGON,\
                        effect=ChangeStats(value=(Constant(0), NumCardsInHand()), method=Methods.SELF, trigger=Triggers.BATTLECRY, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  violet_teacher = Card(name="Violet Teacher", card_type=CardTypes.MINION, manacost=4, attack=3, health=5,\
                       effect=SummonToken(value=(Constant(1), Constant(Card(name="Violet Apprentice", collectable=False, card_type=CardTypes.MINION, manacost=0, attack=1, health=1))),\
                                          trigger=Triggers.FRIENDLY_SPELL_CAST, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY))

  # Rare five drops
  abomination = Card(name="Abomination", card_type=CardTypes.MINION, manacost=5, attack=4, health=4, attributes=[Attributes.TAUNT],\
                     effect=DealDamage(value=Constant(2), trigger=Triggers.DEATHRATTLE, method=Methods.ALL, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL))
  azure_drake = Card(name="Azure Drake", card_type=CardTypes.MINION, manacost=5, attack=4, health=4, creature_type=CreatureTypes.DRAGON, attributes=[Attributes.SPELL_DAMAGE],\
                    effect=DrawCards(value=Constant(1), trigger=Triggers.BATTLECRY, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY))
  gadgetzan_auctioneer = Card(name="Gadgetzan Auctioneer", card_type=CardTypes.MINION, manacost=5, attack=4, health=4,\
                              effect=DrawCards(value=Constant(1), trigger=Triggers.FRIENDLY_SPELL_CAST, owner_filter=OwnerFilters.FRIENDLY, method=Methods.ALL))
  stampeding_kodo = Card(name="Stampeding Kodo", card_type=CardTypes.MINION, manacost=5, attack=3, health=5, creature_type=CreatureTypes.BEAST,\
                          effect=Destroy(value=LessThan(AttackValue(), Constant(3)),method=Methods.RANDOMLY, target=Targets.MINION, trigger=Triggers.BATTLECRY, owner_filter=OwnerFilters.ENEMY))

  # Rare six drops
  argent_commander = Card(name="Argent Commander", card_type=CardTypes.MINION, manacost=6, attack=4, health=2, attributes=[Attributes.CHARGE, Attributes.DIVINE_SHIELD])
  sunwalker = Card(name="Sunwalker", card_type=CardTypes.MINION, manacost=6, attack=4, health=5, attributes=[Attributes.TAUNT, Attributes.DIVINE_SHIELD])

  # Rare seven drops
  ravenholdt_assassin = Card(name="Ravenholdt Assassin", card_type=CardTypes.MINION, manacost=7, attack=7, health=5, attributes=[Attributes.STEALTH])

  # Combine
  rare_one_drops = [angry_chicken, bloodsail_corsair, lightwarden, murloc_tidecaller, secretkeeper, young_priestess]
  rare_two_drops = [ancient_watcher, crazed_alchemist, knife_juggler, mana_addict, mana_wraith, master_swordsmith, pint_sized_summoner, sunfury_protector, wild_pyromancer]
  rare_three_drops = [alarm_o_bot, arcane_golem, coldlight_oracle, coldlight_seer, demolisher, emperor_cobra, imp_master, injured_blademaster, mind_control_tech, questing_adventurer]
  rare_four_drops = [ancient_mage, defender_of_argus, twilight_drake, violet_teacher]
  rare_five_drops = [abomination, azure_drake, gadgetzan_auctioneer, stampeding_kodo]
  rare_six_drops = [argent_commander, sunwalker]
  rare_seven_drops = [ravenholdt_assassin]

  return rare_one_drops + rare_two_drops + rare_three_drops + rare_four_drops + rare_five_drops + rare_six_drops + rare_seven_drops

def get_epic_cards():
  # Epic one drops
  hungry_crab = Card(name="Hungry Crab", card_type=CardTypes.MINION, manacost=1, attack=1, health=2, creature_type=CreatureTypes.BEAST,\
                     effect=DualEffectSelf(Destroy(trigger=Triggers.BATTLECRY, target=Targets.MINION, owner_filter=OwnerFilters.ALL, type_filter=CreatureTypes.MURLOC, method=Methods.TARGETED),\
                                           ChangeStats(value=(Constant(2), Constant(2)),trigger=Triggers.BATTLECRY, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, method=Methods.SELF, duration=Durations.PERMANENTLY)))
  
  # Epic two drops
  captains_parrot = Card(name="Captain's Parrot", card_type=CardTypes.MINION, manacost=2, attack=1, health=1, creature_type=CreatureTypes.BEAST,\
                          effect=Tutor(trigger=Triggers.BATTLECRY, method=Methods.RANDOMLY, target=Targets.MINION, type_filter=CreatureTypes.PIRATE, owner_filter=OwnerFilters.FRIENDLY))
  doomsayer = Card(name="Doomsayer", card_type=CardTypes.MINION, manacost=2, attack=0, health=7,\
                        effect=DualEffectSelf(Destroy(trigger=Triggers.FRIENDLY_END_TURN, owner_filter=OwnerFilters.ALL, target=Targets.MINION, method=Methods.ALL),\
                                              Destroy(trigger=Triggers.FRIENDLY_END_TURN, owner_filter=OwnerFilters.FRIENDLY, target=Targets.MINION, method=Methods.SELF)))

  # Epic three drops
  big_game_hunter = Card(name="Big Game Hunter", card_type=CardTypes.MINION, manacost=3, attack=4, health=2,\
                          effect=Destroy(value=GreaterThan(AttackValue(), Constant(6)),method=Methods.TARGETED, target=Targets.MINION, trigger=Triggers.BATTLECRY, owner_filter=OwnerFilters.ALL))
  blood_knight = Card(name="Blood Knight", card_type=CardTypes.MINION, manacost=3, attack=3, health=3,\
                      effect=DualEffectSelf(RemoveAttribute(value=Constant(Attributes.DIVINE_SHIELD), method=Methods.ALL, trigger=Triggers.BATTLECRY, owner_filter=OwnerFilters.ALL, target=Targets.MINION),\
                                            ChangeStats(value=(Multiply(NumWithAttribute(Constant(Attributes.DIVINE_SHIELD), OwnerFilters.ALL), Constant(3)), Multiply(NumWithAttribute(Constant(Attributes.DIVINE_SHIELD), OwnerFilters.ALL), Constant(3))),\
                                                        trigger=Triggers.BATTLECRY, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY),\
                                            first_effect_first=False))
  murloc_warleader = Card(name="Murloc Warleader", card_type=CardTypes.MINION, manacost=3, attack=3, health=3, creature_type=CreatureTypes.MURLOC,\
                          effect=ChangeStats(value=(Constant(2), Constant(1)), method=Methods.ALL, trigger=Triggers.AURA, target=Targets.MINION, owner_filter=OwnerFilters.ALL, type_filter=CreatureTypes.MURLOC))
  southsea_captain = Card(name="Southsea Captain", card_type=CardTypes.MINION, manacost=3, attack=3, health=3, creature_type=CreatureTypes.PIRATE,\
                          effect=ChangeStats(value=(Constant(1), Constant(1)), trigger=Triggers.AURA, method=Methods.ALL, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, type_filter=CreatureTypes.PIRATE))

  # Epic five drops
  faceless_manipulator = Card(name="Faceless Manipulator", card_type=CardTypes.MINION, manacost=5, attack=3, health=3,\
                              effect=CopyMinion(method=Methods.TARGETED, trigger=Triggers.BATTLECRY, owner_filter=OwnerFilters.ALL))

  # Epic ten_plus_drops
  sea_giant = Card(name="Sea Giant", card_type=CardTypes.MINION, manacost=10, attack=8, health=8,\
                  effect=ChangeCost(value=Multiply(Add(NumOtherMinions(OwnerFilters.ALL), Constant(1)), Constant(-1)), method=Methods.SELF, trigger=Triggers.AURA, owner_filter=OwnerFilters.FRIENDLY, target=Targets.MINION))
  mountain_giant = Card(name="Mountain Giant", card_type=CardTypes.MINION, manacost=12, attack=8, health=8,\
                  effect=ChangeCost(value=Multiply(Add(CardsInHand(OwnerFilters.FRIENDLY), Constant(-1)), Constant(-1)), method=Methods.SELF, trigger=Triggers.AURA, owner_filter=OwnerFilters.FRIENDLY, target=Targets.MINION))
  molten_giant = Card(name="Molten Giant", card_type=CardTypes.MINION, manacost=20, attack=8, health=8,\
                  effect=ChangeCost(value=Multiply(DamageTaken(OwnerFilters.FRIENDLY), Constant(-1)), method=Methods.SELF, trigger=Triggers.AURA, owner_filter=OwnerFilters.FRIENDLY, target=Targets.MINION))

  # Combine
  epic_one_drops = [hungry_crab]
  epic_two_drops = [captains_parrot, doomsayer]
  epic_three_drops = [big_game_hunter, blood_knight, murloc_warleader, southsea_captain]
  epic_five_drops = [faceless_manipulator]
  epic_ten_plus_drops = [sea_giant, mountain_giant, molten_giant]

  return epic_one_drops + epic_two_drops + epic_three_drops + epic_five_drops + epic_ten_plus_drops

def get_hunter_cards():
  #Hunter basic cards
  hunters_mark = Card(name="Hunter's Mark", card_type=CardTypes.SPELL, manacost=0,\
                      effect=SetStats(value=(None, Constant(1)), method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.ALL))
  arcane_shot = Card(name="Arcane Shot", card_type=CardTypes.SPELL, manacost=1,\
                    effect=DealDamage(value=Constant(2), target=Targets.MINION_OR_HERO, method=Methods.TARGETED, owner_filter=OwnerFilters.ALL))
  timber_wolf = Card(name="Timber Wolf", card_type=CardTypes.MINION, manacost=1, attack=1, health=1, creature_type=CreatureTypes.BEAST,\
                      effect=ChangeStats(value=(Constant(1), Constant(0)), method=Methods.ALL, trigger=Triggers.AURA, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, type_filter=CreatureTypes.BEAST))
  tracking = Card(name="Tracking", card_type=CardTypes.SPELL, manacost=1,\
                     effect=Tutor(method=Methods.RANDOMLY, target=Targets.MINION, type_filter=CreatureTypes.BEAST, owner_filter=OwnerFilters.FRIENDLY)) #this is modified from the real tracking
  starving_buzzard = Card(name="Starving Buzzard", card_type=CardTypes.MINION, manacost=2, attack=2, health=1, creature_type=CreatureTypes.BEAST,\
                          effect=DrawCards(value=Constant(1), trigger=Triggers.FRIENDLY_SAME_TYPE_SUMMONED, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY)) 
  animal_companion = Card(name="Animal Companion", card_type=CardTypes.SPELL, manacost=3,\
                          effect=MultiEffectRandom([SummonToken(method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY, value=(Constant(1), Constant(Card(name="Huffer", collectable=False, card_type=CardTypes.MINION, manacost=3, attack=4, health=2, creature_type=CreatureTypes.BEAST, attributes=[Attributes.CHARGE])))),\
                                                    SummonToken(method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY, value=(Constant(1), Constant(Card(name="Leokk", collectable=False, card_type=CardTypes.MINION, manacost=3, attack=2, health=4, creature_type=CreatureTypes.BEAST,\
                                                                                                                                                 effect=ChangeStats(value=(Constant(1), Constant(0)), trigger=Triggers.AURA, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, method=Methods.ALL))))),\
                                                    SummonToken(method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY, value=(Constant(1), Constant(Card(name="Misha", collectable=False, card_type=CardTypes.MINION, manacost=3, attack=4, health=4, creature_type=CreatureTypes.BEAST, attributes=[Attributes.TAUNT]))))]))
  kill_command = Card(name="Kill Command", manacost=3, card_type=CardTypes.SPELL,\
                      effect=DealDamage(value=If(GreaterThan(NumWithCreatureType(CreatureTypes.BEAST, OwnerFilters.FRIENDLY), Constant(0)),Constant(5), Constant(3)),\
                                        method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL))
  houndmaster = Card(name="Houndmaster",card_type=CardTypes.MINION, manacost=4, attack=4, health=3,\
                    effect=DualEffect(ChangeStats(value=(Constant(2), Constant(2)), method=Methods.TARGETED, trigger=Triggers.BATTLECRY, target=Targets.MINION, type_filter=CreatureTypes.BEAST, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY),
                                      GiveAttribute(value=Constant(Attributes.TAUNT), method=Methods.TARGETED, trigger=Triggers.BATTLECRY, target=Targets.MINION, type_filter=CreatureTypes.BEAST, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY)))
  multishot = Card(name="Multi-Shot", card_type=CardTypes.SPELL, manacost=4,\
                  effect=DealDamage(value=Constant(3), method=Methods.RANDOMLY, random_count=2, random_replace=False, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY))
  tundra_rhino = Card(name="Tundra Rhino", card_type=CardTypes.MINION, manacost=5, attack=2, health=5, creature_type=CreatureTypes.BEAST, attributes=[Attributes.CHARGE],\
                      effect=GiveAttribute(value=Constant(Attributes.CHARGE), trigger=Triggers.AURA, method=Methods.ALL, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, type_filter=CreatureTypes.BEAST))

  #Hunter common cards
  explosive_trap = Card(name="Explosive Trap", card_type=CardTypes.SECRET, manacost=2,\
              effect=DealDamage(value=Constant(2), trigger=Triggers.HERO_ATTACKED, method=Methods.ALL, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ENEMY))
  freezing_trap = Card(name="Freezing Trap", card_type=CardTypes.SECRET, manacost=2,\
              effect=DualEffect(ReturnToHand(trigger=Triggers.ENEMY_MINION_ATTACKS, method=Methods.TRIGGERER, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY),\
                                ChangeCost(value=Constant(2), trigger=Triggers.ENEMY_MINION_ATTACKS, method=Methods.TRIGGERER, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY)))
  scavenging_hyena = Card(name="Scavenging Hyena", card_type=CardTypes.MINION, manacost=2, attack=2, health=2, creature_type=CreatureTypes.BEAST,\
                          effect=ChangeStats(value=(Constant(2), Constant(1)), trigger=Triggers.FRIENDLY_SAME_TYPE_DIES, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  snipe = Card(name="Snipe", card_type=CardTypes.SECRET, manacost=2,\
              effect=DealDamage(value=Constant(4), trigger=Triggers.ENEMY_MINION_SUMMONED, method=Methods.TRIGGERER, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY))
  deadly_shot = Card(name="Deadly Shot", card_type=CardTypes.SPELL, manacost=3,\
                    effect=Destroy(method=Methods.RANDOMLY, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY))
  unleash_the_hounds = Card(name="Unleash the Hounds", card_type=CardTypes.SPELL, manacost=3,\
                            effect=SummonToken(method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY,\
                                               value=(NumOtherMinions(OwnerFilters.ENEMY), Constant(Card(name="Hound", collectable=False, card_type=CardTypes.MINION, manacost=1, attack=1, health=1, creature_type=CreatureTypes.BEAST, attributes=[Attributes.CHARGE])))))
  
  #Hunter rare cards
  flare = Card(name="Flare", card_type=CardTypes.SPELL, manacost=1,\
              effect=Cantrip(DualEffectSecrets(RemoveAttribute(value=Constant(Attributes.STEALTH), target=Targets.MINION, owner_filter=OwnerFilters.ENEMY, method=Methods.ALL),\
                                       Destroy(method=Methods.ALL, target=Targets.SECRET, owner_filter=OwnerFilters.ENEMY))))
  misdirection = Card(name="Misdirection", card_type=CardTypes.SECRET, manacost=2,\
                      effect=Redirect(trigger=Triggers.ENEMY_MINION_ATTACKS))
  eaglehorn_bow = Card(name="Eaglehorn Bow", card_type=CardTypes.WEAPON, manacost=3, attack=3, health=2,\
                      effect=ChangeStats(value=(Constant(0), Constant(1)), trigger=Triggers.ANY_SECRET_REVEALED, method=Methods.SELF, target=Targets.WEAPON, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  explosive_shot = Card(name="Explosive Shot", card_type=CardTypes.SPELL, manacost=6,\
                        effect=DualEffect(DealDamage(method=Methods.TARGETED, value=Constant(3), target=Targets.MINION, owner_filter=OwnerFilters.ENEMY),\
                                          DealDamage(method=Methods.TARGETED, value=Constant(2), target=Targets.MINION, owner_filter=OwnerFilters.ENEMY, hits_adjacent=True)))
  savannah_highmane = Card(name="Savannah Highmane", card_type=CardTypes.MINION, manacost=6, attack=6, health=5, creature_type=CreatureTypes.BEAST,\
                          effect=SummonToken(method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.DEATHRATTLE,\
                                             value=(Constant(2), Constant(Card(name="Hyena", collectable=False, card_type=CardTypes.MINION, manacost=2, attack=2, health=2, creature_type=CreatureTypes.BEAST)))))
  
  # Hunter epic cards
  beastial_wrath = Card(name="Beastial Wrath", card_type=CardTypes.SPELL, manacost=1,\
                       effect=DualEffect(ChangeStats(value=(Constant(2), Constant(0)), target=Targets.MINION, owner_filter=OwnerFilters.ALL, method=Methods.TARGETED, duration=Durations.TURN, type_filter=CreatureTypes.BEAST),\
                                          GiveAttribute(value=Constant(Attributes.IMMUNE), target=Targets.MINION, owner_filter=OwnerFilters.ALL, method=Methods.TARGETED, duration=Durations.TURN, type_filter=CreatureTypes.BEAST)))
  snake_trap = Card(name="Snake Trap", card_type=CardTypes.SECRET, manacost=2,\
                    effect=SummonToken(owner_filter=OwnerFilters.FRIENDLY, method=Methods.ALL, trigger=Triggers.ENEMY_ATTACKS_MINION,\
                    value=(Constant(3), Constant(Card(name="Snake", collectable=False, card_type=CardTypes.MINION, manacost=0, attack=1, health=1, creature_type=CreatureTypes.BEAST)))))
  gladiators_longbow = Card(name="Gladiator's Longbow", card_type=CardTypes.WEAPON, manacost=7, attack=5, health=2, attributes=[Attributes.IMMUNE])
  # Combine
  basic_hunter_cards = [hunters_mark, arcane_shot, timber_wolf, tracking, starving_buzzard, animal_companion, kill_command, houndmaster, multishot, tundra_rhino]
  common_hunter_cards = [explosive_trap, freezing_trap, scavenging_hyena, snipe, deadly_shot, unleash_the_hounds]
  rare_hunter_cards = [flare, misdirection, eaglehorn_bow, explosive_shot, savannah_highmane]
  epic_hunter_cards = [beastial_wrath, snake_trap, gladiators_longbow]

  return basic_hunter_cards + common_hunter_cards + rare_hunter_cards + epic_hunter_cards

def get_mage_cards():
  # Mage basic cards
  arcane_missiles = Card(name="Arcane Missiles", manacost=1, card_type=CardTypes.SPELL,\
                         effect=DealDamage(value=Constant(1), random_count=3, method=Methods.RANDOMLY, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ENEMY))
  mirror_image = Card(name="Mirror Image", manacost=1, card_type=CardTypes.SPELL,\
                          effect=SummonToken(method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY,\
                                                value=(Constant(2), Constant(Card(name="Mirror Image Token", collectable=False, card_type=CardTypes.MINION, manacost=0, attack=0, health=2, attributes=[Attributes.TAUNT])))))
  arcane_explosion = Card(name="Arcane Explosion", manacost=2, card_type=CardTypes.SPELL,\
                          effect=DealDamage(value=Constant(1), target=Targets.MINION, method=Methods.ALL, owner_filter=OwnerFilters.ENEMY))
  frostbolt = Card(name="Frostbolt", manacost=2, card_type=CardTypes.SPELL,\
                   effect=DualEffect(DealDamage(value=Constant(3), target=Targets.MINION_OR_HERO, method=Methods.TARGETED, owner_filter=OwnerFilters.ALL),
                                     GiveAttribute(value=Constant(Attributes.FROZEN), target=Targets.MINION_OR_HERO, method=Methods.TARGETED, owner_filter=OwnerFilters.ALL, duration=Durations.PERMANENTLY)))
  arcane_intellect = Card(name="Arcane Intellect", card_type=CardTypes.SPELL, manacost=3,
                          effect=DrawCards(value=Constant(2), owner_filter=OwnerFilters.FRIENDLY, method=Methods.ALL))
  frost_nova = Card(name="Frost Nova", card_type=CardTypes.SPELL, manacost=3,\
                    effect=GiveAttribute(value=Constant(Attributes.FROZEN), method=Methods.ALL, owner_filter=OwnerFilters.ENEMY, target=Targets.MINION, duration=Durations.PERMANENTLY))
  fireball = Card(name="Fireball", card_type=CardTypes.SPELL, manacost=4, effect=DealDamage(
    value=Constant(6), method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL))
  polymorph = Card(name="Polymorph", card_type=CardTypes.SPELL, manacost=4,\
                  effect=ReplaceWithToken(method=Methods.TARGETED, owner_filter=OwnerFilters.ALL,\
                  value=(Constant(1), Constant(Card(name="Sheep", collectable=False, card_type=CardTypes.MINION, manacost=0, attack=1, health=1, creature_type=CreatureTypes.BEAST)))))
  water_elemental = Card(name="Water Elemental", card_type=CardTypes.MINION, manacost=4, attack=3, health=6, attributes=[Attributes.FREEZER])
  flamestrike = Card(name="Flamestrike", card_type=CardTypes.SPELL, manacost=7,\
                    effect=DealDamage(value=Constant(4), target=Targets.MINION, method=Methods.ALL, owner_filter=OwnerFilters.ENEMY))
  
  # Mage common cards
  ice_lance = Card(name="Ice Lance", card_type=CardTypes.SPELL, manacost=1,\
                  effect=DualEffect(DealDamage(value=If(TargetFrozen(), Constant(4), Constant(0)), method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL),\
                        GiveAttribute(value=Constant(Attributes.FROZEN), method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL, duration=Durations.PERMANENTLY)))
  mana_wyrm = Card(name="Mana Wyrm", card_type=CardTypes.MINION, manacost=1, attack=1, health=3,\
                  effect=ChangeStats(value=(Constant(1), Constant(0)), trigger=Triggers.FRIENDLY_SPELL_CAST, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  sorcerers_apprentice = Card(name="Sorcerer's Apprentice", card_type=CardTypes.MINION, manacost=2, attack=3, health=2,\
                              effect=ChangeCost(value=Constant(-1), trigger=Triggers.AURA, method=Methods.ALL, target=Targets.SPELL, owner_filter=OwnerFilters.FRIENDLY))
  ice_barrier = Card(name="Ice Barrier", card_type=CardTypes.SECRET, manacost=3,\
                     effect=GainArmor(value=Constant(8), trigger=Triggers.HERO_ATTACKED, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY))
  mirror_entity = Card(name="Mirror Entity", card_type=CardTypes.SECRET, manacost=3,\
                        effect=SummonToken(trigger=Triggers.ENEMY_MINION_SUMMONED, value=(Constant(1), Target()), method=Methods.TRIGGERER, owner_filter=OwnerFilters.FRIENDLY))
  cone_of_cold = Card(name="Cone of Cold", card_type=CardTypes.SPELL, manacost=4,\
                      effect=DualEffect(GiveAttribute(value=Constant(Attributes.FROZEN), method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.ALL, hits_adjacent=True, duration=Durations.PERMANENTLY),\
                                        DealDamage(value=Constant(1), method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.ALL, hits_adjacent=True)))

  # Mage rare cards
  counterspell = Card(name="Counterspell", card_type=CardTypes.SECRET, manacost=3,\
                      effect=Counterspell(method=Methods.ALL, trigger=Triggers.ENEMY_SPELL_COUNTERED, owner_filter=OwnerFilters.ENEMY))
  kirin_tor_mage = Card(name="Kirin Tor Mage", card_type=CardTypes.MINION, manacost=3, attack=4, health=3,\
                        effect=GiveAttribute(method=Methods.ALL, target=Targets.HERO, trigger=Triggers.BATTLECRY, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.TURN, value=Constant(Attributes.FREE_SECRET)))
  vaporize = Card(name="Vaporize", card_type=CardTypes.SECRET, manacost=3,\
                  effect=Destroy(trigger=Triggers.DESTROY_SECRET_REVEALED, method=Methods.TRIGGERER, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY))
  etherial_arcanist = Card(name="Etherial Arcanist", card_type=CardTypes.MINION, manacost=4, attack=3, health=3,\
                            effect=ChangeStats(trigger=Triggers.FRIENDLY_END_TURN, value=(If(HasSecret(),Constant(2),Constant(0)), If(HasSecret(),Constant(2),Constant(0))),\
                                                method=Methods.SELF, target=Targets.MINION, duration=Durations.PERMANENTLY, owner_filter=OwnerFilters.FRIENDLY))
  blizzard = Card(name="Blizzard", card_type=CardTypes.SPELL, manacost=6,\
                  effect=DualEffect(DealDamage(value=Constant(2), method=Methods.ALL, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY),\
                           GiveAttribute(value=Constant(Attributes.FROZEN), method=Methods.ALL, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY, duration=Durations.PERMANENTLY)))

  # Mage epic cards
  ice_block = Card(name="Ice Block", card_type=CardTypes.SECRET, manacost=3,\
                    effect=GiveAttribute(trigger=Triggers.LETHAL_DAMAGE, value=Constant(Attributes.IMMUNE), method=Methods.ALL, target=Targets.HERO, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.TURN))
  spellbender = Card(name="Spellbender", card_type=CardTypes.SECRET, manacost=3,\
                      effect=RedirectToToken(value=(Constant(1), Constant(Card(name="Spellbender Token", collectable=False, card_type=CardTypes.MINION, manacost=0, attack=1, health=3))),\
                                              trigger=Triggers.ENEMY_SPELL_REDIRECTED))
  pyroblast = Card(name="Pyroblast", card_type=CardTypes.SPELL, manacost=10,\
                    effect=DealDamage(value=Constant(10), method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL))

  basic_mage_cards = [arcane_missiles, mirror_image, arcane_explosion, frostbolt, arcane_intellect, frost_nova, fireball, polymorph, water_elemental, flamestrike]
  common_mage_cards = [ice_lance, mana_wyrm, sorcerers_apprentice, ice_barrier, mirror_entity, cone_of_cold]
  rare_mage_cards = [counterspell, kirin_tor_mage, vaporize, etherial_arcanist, blizzard]
  epic_mage_cards = [ice_block, spellbender, pyroblast]
  return basic_mage_cards + common_mage_cards + rare_mage_cards + epic_mage_cards

def get_warrior_cards():
  #Warrior basic cards
  execute = Card(name="Execute", card_type=CardTypes.SPELL, manacost=1,\
                 effect=Destroy(value=Damaged(), target=Targets.MINION, owner_filter=OwnerFilters.ALL, method=Methods.TARGETED))
  whirlwind = Card(name="Whirlwind", card_type=CardTypes.SPELL, manacost=1,\
                   effect=DealDamage(value=Constant(1), method=Methods.ALL, target=Targets.MINION, owner_filter=OwnerFilters.ALL))
  cleave = Card(name="Cleave", card_type=CardTypes.SPELL, manacost=2,\
                effect=DealDamage(value=Constant(2), random_count=2, random_replace=False, method=Methods.RANDOMLY, target=Targets.MINION, owner_filter=OwnerFilters.ENEMY))
  fiery_war_axe = Card(name="Fiery War Axe", card_type=CardTypes.WEAPON, manacost=2, attack=3, health=2)
  heroic_strike = Card(name="Heroic Strike", card_type=CardTypes.SPELL, manacost=2,\
                      effect=ChangeStats(value=(Constant(4), Constant(0)), method=Methods.ALL, target=Targets.HERO, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.TURN))
  charge = Card(name="Charge", card_type=CardTypes.SPELL, manacost=3,\
                effect=DualEffect(GiveAttribute(value=Constant(Attributes.CHARGE), method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY),\
                                  ChangeStats(value=(Constant(2), Constant(0)), method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY)))
  shield_block = Card(name="Shield Block", card_type=CardTypes.SPELL, manacost=3,\
                      effect=Cantrip(GainArmor(value=Constant(5), method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY)))
  warsong_commander = Card(name="Warsong Commander", card_type=CardTypes.MINION, manacost=3, attack=2, health=3,\
                          effect=GiveAttribute(trigger=Triggers.FRIENDLY_LESS_THAN_FOUR_ATTACK_SUMMONED, value=Constant(Attributes.CHARGE), method=Methods.TRIGGERER, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  korkron_elite = Card(name="Kor'kron Elite", card_type=CardTypes.MINION, manacost=4, attack=4, health=3, attributes=[Attributes.CHARGE])
  arcanite_reaper = Card(name="Arcanite Reaper", card_type=CardTypes.WEAPON, manacost=5, attack=5, health=2)

  #Warrior common cards
  inner_rage = Card(name="Inner Rage", card_type=CardTypes.SPELL, manacost=0,\
                    effect=DualEffect(DealDamage(value=Constant(1), target=Targets.MINION, method=Methods.TARGETED, owner_filter=OwnerFilters.ALL),\
                                      ChangeStats(value=(Constant(2), Constant(0)), target=Targets.MINION, method=Methods.TARGETED, owner_filter=OwnerFilters.ALL, duration=Durations.PERMANENTLY)))
  battle_rage = Card(name="Battle Rage", card_type=CardTypes.SPELL, manacost=2,\
                    effect=DrawCards(value=Add(NumDamaged(OwnerFilters.FRIENDLY), If(GreaterThan(DamageTaken(OwnerFilters.FRIENDLY), Constant(1)), Constant(1), Constant(0))),\
                                      method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY))
  cruel_taskmaster = Card(name="Cruel Taskmaster", card_type=CardTypes.MINION, manacost=2, attack=2, health=2,\
                    effect=DualEffect(DealDamage(value=Constant(1), trigger=Triggers.BATTLECRY, target=Targets.MINION, method=Methods.TARGETED, owner_filter=OwnerFilters.ALL),\
                                      ChangeStats(value=(Constant(2), Constant(0)), target=Targets.MINION, method=Methods.TARGETED, owner_filter=OwnerFilters.ALL, duration=Durations.PERMANENTLY)))
  rampage = Card(name="Rampage", card_type=CardTypes.SPELL, manacost=2,\
                effect=ChangeStats(value=(Constant(3), Constant(3)), method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.ALL, duration=Durations.PERMANENTLY, dynamic_filter=Damaged()))
  slam = Card(name="Slam", card_type=CardTypes.SPELL, manacost=2,\
              effect=DualEffect(DealDamage(value=Constant(2), method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.ALL),\
                                DrawCards(value=If(TargetAlive(), Constant(1), Constant(0)), owner_filter=OwnerFilters.FRIENDLY, method=Methods.ALL)))
  arathi_weaponsmith = Card(name="Arathi Weaponsmith", card_type=CardTypes.MINION, manacost=4, attack=3, health=3,\
                            effect=SummonToken(trigger=Triggers.BATTLECRY, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY,\
                            value=(Constant(1), Constant(Card(name="Battle Axe", collectable=False, card_type=CardTypes.WEAPON, manacost=1, attack=2, health=2)))))

  #Warrior rare cards
  upgrade = Card(name="Upgrade!", card_type=CardTypes.SPELL, manacost=1,\
                  effect=DynamicChoice(HasWeapon(OwnerFilters.FRIENDLY),
                                       ChangeStats(value=(Constant(1), Constant(1)), target=Targets.WEAPON, owner_filter=OwnerFilters.FRIENDLY, method=Methods.ALL, duration=Durations.PERMANENTLY),\
                                       SummonToken(trigger=Triggers.BATTLECRY, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY,\
                                                   value=(Constant(1), Constant(Card(name="Heavy Axe", collectable=False, card_type=CardTypes.WEAPON, manacost=1, attack=1, health=3))))))
  armorsmith = Card(name="Armorsmith", card_type=CardTypes.MINION, manacost=2, attack=1, health=4,\
                    effect=GainArmor(value=Constant(1), trigger=Triggers.FRIENDLY_MINION_DAMAGED, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY))
  commanding_shout = Card(name="Commanding Shout", card_type=CardTypes.SPELL, manacost=2,\
                          effect=Cantrip(GiveAttribute(value=Constant(Attributes.MINIONS_UNKILLABLE), method=Methods.ALL, target=Targets.HERO, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.TURN)))
  frothing_berserker = Card(name="Frothing Berserker", card_type=CardTypes.MINION, manacost=3, attack=2, health=4,\
                            effect=ChangeStats(value=(Constant(1), Constant(0)), trigger=Triggers.ANY_MINION_DAMAGED, method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  mortal_strike = Card(name="Mortal Strike", card_type=CardTypes.SPELL, manacost=4,\
                        effect=DealDamage(value=If(GreaterThan(DamageTaken(OwnerFilters.FRIENDLY), Constant(17)), Constant(6), Constant(4)),\
                                          method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL))

  #Warrior epic cards
  shield_slam = Card(name="Shield Slam", card_type=CardTypes.SPELL, manacost=1,\
                     effect=DealDamage(value=PlayerArmor(OwnerFilters.FRIENDLY), method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.ALL))
  brawl = Card(name="Brawl", card_type=CardTypes.SPELL, manacost=5,\
              effect=DualEffectBoard(GiveAttribute(value=Constant(Attributes.BRAWL_PROTECTION), method=Methods.RANDOMLY, target=Targets.MINION, owner_filter=OwnerFilters.ALL, duration=Durations.TURN),\
                                     DualEffect(Destroy(value=Not(SourceHasAttribute(Constant(Attributes.BRAWL_PROTECTION))), method=Methods.ALL, target=Targets.MINION, owner_filter=OwnerFilters.ALL),\
                                     RemoveAttribute(value=Constant(Attributes.BRAWL_PROTECTION), method=Methods.ALL, target=Targets.MINION, owner_filter=OwnerFilters.ALL))))
  gorehowl = Card(name="Gorehowl", card_type=CardTypes.WEAPON, manacost=7, attack=7, health=1, attributes=[Attributes.ATTACK_AS_DURABILITY])

  basic_warrior_cards = [execute, whirlwind, cleave, fiery_war_axe, heroic_strike, charge, shield_block, warsong_commander, korkron_elite, arcanite_reaper]
  common_warrior_cards = [inner_rage, battle_rage, cruel_taskmaster, rampage, slam, arathi_weaponsmith]
  rare_warrior_cards = [upgrade, armorsmith, commanding_shout, frothing_berserker, mortal_strike]
  epic_warrior_cards = [shield_slam, brawl, gorehowl]
  return basic_warrior_cards + common_warrior_cards + rare_warrior_cards + epic_warrior_cards

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
  gain_perm_mana = Card("Gain Perm Mana", card_type=CardTypes.SPELL, manacost=0,\
                        effect=GainMana(value=Constant(1), owner_filter=OwnerFilters.FRIENDLY, method=Methods.ALL, duration=Durations.PERMANENTLY))

  test_cards = [all_dam, generic_weapon, battlecry_weapon,
          windfury_weapon, battlecry_reduce_cost, gain_perm_mana]
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
    pool.extend(get_epic_cards())
  if CardSets.CLASSIC_HUNTER in set_names:
    pool.extend(get_hunter_cards())
  if CardSets.CLASSIC_MAGE in set_names:
    pool.extend(get_mage_cards())
  if CardSets.CLASSIC_WARRIOR in set_names:
    pool.extend(get_warrior_cards())
  if CardSets.OP_CARDS in set_names:
    pool.extend(get_op_cards())
  if CardSets.TEST_CARDS in set_names:
    pool.extend(get_test_cards())
  if CardSets.RANDOM_CARDS in set_names:
    pool.extend(get_random_cards(random_state))
  return pool
