from card import Card
from condition import Condition
from enums import *
from effects import *
from card_generator import make_random_card
from copy import deepcopy
from dynamics import *


def get_utility_card(utility_card):
    the_coin = Card(name="The Coin", collectable=False, card_type=CardTypes.SPELL, manacost=0,
                    effect=GainMana(value=1, method=Methods.TARGETED,
                                    duration=Durations.TURN, target=Targets.HERO, owner_filter=OwnerFilters.FRIENDLY))
    utility_cards = {"Coin": the_coin}
    return utility_cards[utility_card]


def get_hero_power(hero_class):
    steady_shot = Card(name="Steady Shot", collectable=False, card_type=CardTypes.HERO_POWER, manacost=2,
                            effect=DealDamage(value=2, method=Methods.ALL,
                                              target=Targets.HERO, owner_filter=OwnerFilters.ENEMY))
    fireblast = Card(name="Fireblast", collectable=False, card_type=CardTypes.HERO_POWER, manacost=2,
                     effect=DealDamage(value=1, method=Methods.TARGETED, target=Targets.MINION_OR_HERO,
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
    # Common one drops
    wisp = Card(name="Wisp", card_type=CardTypes.MINION,
                manacost=0, attack=1, health=1)
    abusive_sergeant = Card(name="Abusive Sergeant", card_type=CardTypes.MINION, manacost=1, attack=1, health=1,
                            effect=ChangeStats(value=(2, 0), method=Methods.TARGETED,
                                               target=Targets.MINION, owner_filter=OwnerFilters.ALL, duration=Durations.TURN,
                                               trigger=Triggers.BATTLECRY, type_filter=CreatureTypes.ALL))
    argent_squire = Card(name="Argent Squire", card_type=CardTypes.MINION, manacost=1, attack=1, health=1,
                         attributes=[Attributes.DIVINE_SHIELD])
    leper_gnome = Card(name="Leper Gnome", card_type=CardTypes.MINION, manacost=1, attack=2, health=1,
                       effect=DealDamage(value=2, method=Methods.ALL, target=Targets.HERO,
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
    bloodsail_raider = Card(name="Bloodsail Raider", card_type=CardTypes.MINION, manacost=2, attack=2, health=3,
                            effect=GainWeaponAttack(method=Methods.TARGETED, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY))
    dire_wolf_alpha = Card(name="Dire Wolf Alpha", card_type=CardTypes.MINION, manacost=2, attack=2, health=2, effect=ChangeStats(value=(1, 0), trigger=Triggers.AURA, method=Methods.ADJACENT,
                           target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, type_filter=CreatureTypes.ALL))  # gives all minions +1 including self, nerf attack by 1, mana by 1?
    faerie_dragon = Card(name="Faerie Dragon", card_type=CardTypes.MINION,
                         manacost=2, attack=3, health=2, attributes=[Attributes.HEXPROOF])
    loot_hoarder = Card(name="Loot Hoarder", card_type=CardTypes.MINION, manacost=2, attack=2, health=1,
                        effect=DrawCards(value=1, method=Methods.ALL, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.DEATHRATTLE))
    mad_bomber = Card(name="Mad Bomber", card_type=CardTypes.MINION, manacost=2, attack=3, health=2,
                      effect=DealDamage(value=1, random_count=3, method=Methods.RANDOMLY, target=Targets.MINION_OR_HERO,
                                        owner_filter=OwnerFilters.ALL, trigger=Triggers.BATTLECRY))
    youthful_brewmaster = Card(name="Youthful Brewmaster", card_type=CardTypes.MINION, manacost=2, attack=3, health=2,
                               effect=ReturnToHand(method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.BATTLECRY))

    # Common three drops
    earthen_ring_farseer = Card(name="Earthen Ring Farseer", card_type=CardTypes.MINION, manacost=3, attack=3, health=3,
                                effect=RestoreHealth(value=3, method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL, trigger=Triggers.BATTLECRY))
    flesheating_ghoul = Card(name="Flesheating Ghoul", card_type=CardTypes.MINION, manacost=3, attack=3, health=3,
                             effect=ChangeStats(value=(1, 0), method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.ANY_MINION_DIES))
    harvest_golem = Card(name="Harvest Golem", card_type=CardTypes.MINION, creature_type=CreatureTypes.MECH, manacost=3, attack=2, health=3,
                         effect=SummonToken(value=Card(name="Damaged Golem", collectable=False, card_type=CardTypes.MINION, creature_type=CreatureTypes.MECH, manacost=1, attack=2, health=1),
                                            method=Methods.TARGETED, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.DEATHRATTLE))
    ironbeak_owl = Card(name="Ironbeak Owl", card_type=CardTypes.MINION, creature_type=CreatureTypes.BEAST, manacost=3, attack=2, health=1,
                        effect=Silence(method=Methods.TARGETED, owner_filter=OwnerFilters.ALL, target=Targets.MINION, trigger=Triggers.BATTLECRY))
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
                       effect=DrawCards(value=1, method=Methods.TARGETED, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.FRIENDLY_MINION_DIES))
    dark_iron_dwarf = Card(name="Dark Iron Dwarf", card_type=CardTypes.MINION, manacost=4, attack=4, health=4,
                           effect=ChangeStats(value=(2, 0), method=Methods.TARGETED, target=Targets.MINION, owner_filter=OwnerFilters.ALL, duration=Durations.TURN, trigger=Triggers.BATTLECRY))
    dread_corsair = Card(name="Dread Corsair", card_type=CardTypes.MINION, manacost=4, attack=3, health=3, creature_type=CreatureTypes.PIRATE,
                         effect=ChangeCost(value=Multiply(WeaponAttack(), Constant(-1)), method=Methods.SELF, target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.AURA))
    mogushan_warden = Card(name="Mogushan Warden", card_type=CardTypes.MINION,
                           manacost=4, attack=1, health=7, attributes=[Attributes.TAUNT])
    silvermoon_guardian = Card(name="Silvermoon Guardian", card_type=CardTypes.MINION,
                               manacost=4, attack=3, health=3, attributes=[Attributes.DIVINE_SHIELD])

    # Common five drops
    fen_creeper = Card(name="Fen Creeper", card_type=CardTypes.MINION,
                       manacost=5, attack=3, health=6, attributes=[Attributes.TAUNT])
    silver_hand_knight = Card(name="Silver Hand Knight", card_type=CardTypes.MINION, manacost=5, attack=4, health=4,
                              effect=SummonToken(value=Card(name="Squire", collectable=False, card_type=CardTypes.MINION, manacost=1, attack=2, health=2),
                                                 method=Methods.TARGETED, owner_filter=OwnerFilters.FRIENDLY, trigger=Triggers.BATTLECRY))
    spiteful_smith = Card(name="Spiteful Smith", card_type=CardTypes.MINION, manacost=5, attack=4, health=6,
                          effect=ChangeStats(value=(2, 0), trigger=Triggers.AURA, owner_filter=OwnerFilters.FRIENDLY, target=Targets.WEAPON, method=Methods.ALL))
    stranglethorn_tiger = Card(name="Stranglethorn Tiger", card_type=CardTypes.MINION, creature_type=CreatureTypes.BEAST, manacost=5,attack=5, health=5, attributes=[Attributes.STEALTH])
    
    venture_co_mercenary = Card(name="Venture Co. Mercenary", card_type=CardTypes.MINION, manacost=5, attack=7, health=6,
                                effect=ChangeCost(value=Constant(3), target=Targets.MINION, owner_filter=OwnerFilters.FRIENDLY, method=Methods.ALL, trigger=Triggers.AURA))

    #Common six drops
    frost_elemental = Card(name="Frost Elemental", card_type=CardTypes.MINION, creature_type=CreatureTypes.ELEMENTAL, manacost=6, attack=5, health=5,\
                        effect=GiveKeyword(value=Attributes.FROZEN, trigger=Triggers.BATTLECRY, method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL, duration=Durations.PERMANENTLY))

    # Rare four drops
    defender_of_argus = Card(name="Defender of Argus", card_type=CardTypes.MINION, manacost=4, attack=3, health=3,
                             effect=DuelAction(ChangeStats(value=(1, 1), method=Methods.ADJACENT, target=Targets.MINION,
                                                           owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.BATTLECRY),
                                               GiveKeyword(value=Attributes.TAUNT, method=Methods.ADJACENT, target=Targets.MINION,
                                                           owner_filter=OwnerFilters.FRIENDLY, duration=Durations.PERMANENTLY, trigger=Triggers.BATTLECRY)))

    common_one_drops = [wisp, abusive_sergeant, argent_squire, leper_gnome,
                        shieldbearer, southsea_deckhand, worgen_infiltrator, young_dragonhawk]
    common_two_drops = [amani_berserker, bloodsail_raider, dire_wolf_alpha,
                        faerie_dragon, loot_hoarder, mad_bomber, youthful_brewmaster]
    common_three_drops = [earthen_ring_farseer, flesheating_ghoul, harvest_golem, ironbeak_owl,
                          jungle_panther, raging_worgen, scarlet_crusader, tauren_warrior, thrallmar_farseer]
    common_four_drops = [ancient_brewmaster, cult_master, dark_iron_dwarf,
                         dread_corsair, mogushan_warden, silvermoon_guardian]
    common_five_drops = [fen_creeper, silver_hand_knight, spiteful_smith, stranglethorn_tiger, venture_co_mercenary]
    common_six_drops = [frost_elemental]
    rare_four_drops = [defender_of_argus]
    return common_one_drops + common_two_drops + common_three_drops + common_four_drops + common_five_drops + common_six_drops + rare_four_drops


def get_mage_cards():
    fireball = Card(name="Fireball", card_type=CardTypes.SPELL, manacost=4, effect=DealDamage(
        value=6, method=Methods.TARGETED, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL))
    return [fireball]


def get_test_cards():
    all_dam = Card("All Damage", card_type=CardTypes.SPELL, manacost=0,
                   effect=DealDamage(value=3, method=Methods.ALL, target=Targets.MINION_OR_HERO,
                                     owner_filter=OwnerFilters.ALL)
                   )
    generic_weapon = Card("Generic Weapon", card_type=CardTypes.WEAPON, manacost=1,
                          attack=3, health=2)
    battlecry_weapon = Card("Battlecry Weapon", card_type=CardTypes.WEAPON, manacost=1, attack=3, health=2,
                            effect=DealDamage(value=1, method=Methods.ALL, target=Targets.MINION_OR_HERO, owner_filter=OwnerFilters.ALL, trigger=Triggers.BATTLECRY))
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
