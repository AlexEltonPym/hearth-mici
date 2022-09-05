from card import Card
from condition import Condition
from enums import *
from effects import *
from card_generator import make_random_card
from copy import deepcopy

def get_utility_card(utility_card):
  the_coin = Card(name="The Coin", collectable=False, card_type=CardTypes.SPELL, mana=0, \
                  effect=GainMana(value = 1, method = Methods.TARGETED,\
                  duration = Durations.TURN, target=Targets.HERO, owner_filter=OwnerFilters.FRIENDLY))
  utility_cards = {"Coin": the_coin}
  return utility_cards[utility_card]

def get_hero_power(hero_class): 
  steady_shot = Card(name="Steady Shot", collectable=False, card_type=CardTypes.HERO_POWER, mana=2, \
                          effect=DealDamage(value=2, method=Methods.ALL, \
                          target=Targets.HERO, owner_filter=OwnerFilters.ENEMY))
  fireblast = Card(name="Fireblast", collectable=False, card_type=CardTypes.HERO_POWER, mana=2,\
                          effect=DealDamage(value=1, method=Methods.TARGETED, target=Targets.MINION_OR_HERO,\
                            owner_filter=OwnerFilters.ALL))
  hero_powers = {Classes.HUNTER: steady_shot, Classes.MAGE: fireblast}
  return hero_powers[hero_class]

def get_hunter_cards():
  hunter_cards = []

  return hunter_cards

def get_op_cards():
  op_cards = []
  return op_cards

def get_classic_cards():
  #Common one drops
  wisp = Card(name="Wisp", card_type = CardTypes.MINION, mana = 0, attack = 1, health = 1)
  abusive_sergeant = Card(name="Abusive Sergeant", card_type=CardTypes.MINION, mana=1, attack=1, health=1,\
                          effect=ChangeStats(value=(2,0), method = Methods.TARGETED,\
                          target=Targets.MINION, owner_filter = OwnerFilters.ALL, duration = Durations.TURN,\
                          trigger= Triggers.BATTLECRY, type_filter=CreatureTypes.ALL))
  argent_squire = Card(name="Argent Squire", card_type=CardTypes.MINION, mana = 1, attack=1, health=1,\
                       attributes=[Attributes.DIVINE_SHIELD])
  leper_gnome = Card(name="Leper Gnome", card_type=CardTypes.MINION, mana=1, attack=2, health=1,\
                    effect=DealDamage(value=2, method=Methods.ALL, target=Targets.HERO,\
                    owner_filter=OwnerFilters.ENEMY, trigger=Triggers.DEATHRATTLE))
  shieldbearer = Card(name="Shieldbearer", card_type=CardTypes.MINION, mana=1, attack=0, health=4, attributes=[Attributes.TAUNT])
  southsea_deckhand = Card(name="Southsea Deckhand", card_type=CardTypes.MINION, creature_type=CreatureTypes.PIRATE, mana=1, attack=2, health=1,\
                          condition=Condition(requirement=Condition.has_weapon, result={'attributes': [Attributes.CHARGE]}))
  worgen_infiltrator = Card(name="Worgen Infiltrator", card_type=CardTypes.MINION, mana=1, attack=2, health=1, attributes=[Attributes.STEALTH])
  young_dragonhawk = Card(name="Young Dragonhawk", card_type=CardTypes.MINION, mana=1, attack=1, health=1, attributes=[Attributes.WINDFURY])
  
  #Common two drops
  amani_berserker = Card(name="Amani Berserker", card_type=CardTypes.MINION, mana=2, attack=2, health=3, condition=Condition(requirement=Condition.damaged, result={'temp_attack': 3}))
  bloodsail_raider = Card(name="Bloodsail Raider", card_type=CardTypes.MINION, mana=2, attack=2, health=3,\
                         effect=GainWeaponAttack(method=Methods.TARGETED, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
  dire_wolf_alpha = Card(name="Dire Wolf Alpha", card_type=CardTypes.MINION, mana=2, attack=2, health=2, effect=ChangeStats(value=(1,0), trigger=Triggers.AURA, method=Methods.ADJACENT, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, type_filter=CreatureTypes.ALL)) #gives all minions +1 including self, nerf attack by 1, mana by 1?
  faerie_dragon = Card(name="Faerie Dragon", card_type=CardTypes.MINION, mana=2, attack=3, health=2, attributes=[Attributes.HEXPROOF])
  loot_hoarder = Card(name="Loot Hoarder", card_type=CardTypes.MINION, mana=2, attack=2, health=1,\
                      effect=DrawCards(value=1, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.DEATHRATTLE))
  mad_bomber = Card(name="Mad Bomber", card_type=CardTypes.MINION, mana=2, attack=3, health=2,\
                    effect=DealDamage(value=1, random_count=3, method = Methods.RANDOMLY, target=Targets.MINION_OR_HERO,\
                    owner_filter=OwnerFilters.ALL, trigger=Triggers.BATTLECRY))
  youthful_brewmaster = Card(name="Youthful Brewmaster", card_type=CardTypes.MINION, mana=2, attack=3, health=2,\
                          effect=ReturnToHand(method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.BATTLECRY))

  #Common three drops
  earthen_ring_farseer = Card(name="Earthen Ring Farseer", card_type=CardTypes.MINION, mana=3, attack=3, health=3,\
                              effect=RestoreHealth(value=3, method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL, trigger=Triggers.BATTLECRY))
  flesheating_ghoul = Card(name="Flesheating Ghoul", card_type=CardTypes.MINION, mana=3, attack=3, health=3,\
                                              effect=ChangeStats(value=(1,0), method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.MINION_DIES))
  harvest_golem = Card(name="Harvest Golem", card_type=CardTypes.MINION, creature_type=CreatureTypes.MECH, mana=3, attack=2, health=3,\
                        effect=SummonToken(value=Card(name="Damaged Golem", collectable=False, card_type=CardTypes.MINION, creature_type=CreatureTypes.MECH, mana=1, attack=2, health=1),\
                        method=Methods.TARGETED, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.DEATHRATTLE))
  ironbeak_owl = Card(name="Ironbeak Owl", card_type=CardTypes.MINION, mana=3, attack=2, health=1,\
                      effect=Silence(method=Methods.TARGETED, owner_filter=OwnerFilters.ALL, target=Targets.MINION, trigger=Triggers.BATTLECRY))


  #Rare four drops
  defender_of_argus = Card(name="Defender of Argus", card_type=CardTypes.MINION, mana=4, attack=3, health=3,\
                          effect=DuelAction(ChangeStats(value=(1,1), method=Methods.ADJACENT, target=Targets.MINION,\
                          owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.BATTLECRY),
                                            GiveKeyword(value=Attributes.TAUNT, method=Methods.ADJACENT, target=Targets.MINION,\
                          owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.BATTLECRY)))


  common_one_drops = [wisp, abusive_sergeant, argent_squire, leper_gnome, shieldbearer, southsea_deckhand, worgen_infiltrator, young_dragonhawk]
  common_two_drops = [amani_berserker, bloodsail_raider, dire_wolf_alpha, faerie_dragon, loot_hoarder, mad_bomber, youthful_brewmaster]
  common_three_drops = [earthen_ring_farseer, flesheating_ghoul, harvest_golem, ironbeak_owl]

  rare_four_drops = [defender_of_argus]
  return common_one_drops + common_two_drops + common_three_drops + rare_four_drops

def get_mage_cards():
  fireball = Card(name="Fireball", card_type=CardTypes.SPELL, mana=4, effect=DealDamage(value=6, method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL))
  return [fireball]

def get_test_cards():
  all_dam = Card("All Damage", card_type=CardTypes.SPELL, mana=0,\
                effect=DealDamage(value=3, method=Methods.ALL, target=Targets.MINION_OR_HERO,\
                  owner_filter=OwnerFilters.ALL)
    )
  generic_weapon = Card("Generic Weapon", card_type=CardTypes.WEAPON, mana=1,\
                        attack=3, health=2)
  battlecry_weapon = Card("Battlecry Weapon", card_type=CardTypes.WEAPON, mana=1, attack=3, health=2,\
                          effect=DealDamage(value=1, method=Methods.ALL, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL, trigger=Triggers.BATTLECRY))
  windfury_weapon = Card("Windfury Weapon", card_type=CardTypes.WEAPON, mana=0, attack=2, health=2, attributes=[Attributes.WINDFURY])
  test_cards = [all_dam, generic_weapon, battlecry_weapon, windfury_weapon]
  return test_cards

def get_random_cards(random_state):
  rand_cards = [make_random_card(i,random_state) for i in range(100)]
  return rand_cards

def build_pool(set_names, random_state):
  pool = []
  if CardSets.CLASSIC_NEUTRAL in set_names:
    pool.extend(get_classic_cards())
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

def get_from_name(pool, name):
  for card in pool:
    if card.name == name:
      return deepcopy(card)
  
  raise KeyError("Could not find card")