"""Single source of truth for the linear heuristic state features.

Historically the 26 state features were duplicated between
GreedyActionSmart.get_score (strategy.py) and evaluate_position
(montecarlotreesearch.py), with the count hardcoded in lockstep at four
sites and a silent-misalignment trap whenever a 27-long greedy vector
(turn_passed first) was passed to the 26-feature evaluator. This module is
now the only implementation; both consumers call extract_features.

Conventions:
- extract_features(state, me): the 26 state features from `me`'s
  perspective, in the historical order. GreedyActionSmart prepends
  turn_passed (its weights stay 27-long); evaluate_position uses these 26
  directly.
- extract_candidate_features(state, me): NEW candidate features under
  information-theoretic evaluation (see README S5) - kept separate so the
  current 27-weight champion vectors remain valid until candidates are
  formally adopted into FEATURE_NAMES after the usefulness study.
"""
from enums import Attributes, Triggers
from neural_eval import _walk_effects

OTHER_POSITIVE_ATTRIBUTES = [Attributes.CHARGE, Attributes.STEALTH, Attributes.WINDFURY,
                             Attributes.HEXPROOF, Attributes.POISONOUS, Attributes.IMMUNE,
                             Attributes.FREEZER]

FEATURE_NAMES = [
  "hp", "enemy_hp", "health_difference", "armor_difference",
  "num_minions_difference", "total_minion_attack_difference", "total_minion_health_difference",
  "num_minions_with_taunt", "num_enemy_minions_with_taunt",
  "num_minions_with_divine_shield", "num_enemy_minions_with_divine_shield",
  "num_minions_with_lifesteal", "num_enemy_minions_with_lifesteal",
  "num_minions_with_spell_damage", "num_enemy_minions_with_spell_damage",
  "num_other_positive_attributes", "num_other_enemy_positive_attributes",
  "num_cards_in_hand_difference", "num_cards_in_library_difference",
  "num_cards_in_secrets_zone_difference",
  "lethal_margin_mine", "lethal_margin_theirs", "weapon_durability_difference",
  "fatigue_proximity", "hero_power_available_difference", "unused_mana",
]

CANDIDATE_NAMES = [
  "deathrattle_count_difference", "taunt_health_difference",
  "their_hand_mana_threat", "my_playable_next_turn",
  "divine_shield_attack_difference", "enemy_weapon_damage_pending",
]


def extract_features(state, me):
  """The historical 26 state features from `me`'s perspective. Order and
  arithmetic are byte-identical to the pre-refactor duplicated versions."""
  them = me.other_player

  #one attribute snapshot per minion instead of one aura scan per (minion, attribute)
  my_attrs = [minion.get_all_attributes() for minion in me.board]
  their_attrs = [minion.get_all_attributes() for minion in them.board]
  total_my_attack = sum(minion.get_attack() for minion in me.board)
  total_their_attack = sum(minion.get_attack() for minion in them.board)
  my_weapon, their_weapon = me.weapon, them.weapon

  return [
    me.health, them.health, me.health - them.health,
    me.armor - them.armor,
    len(me.board) - len(them.board),
    total_my_attack - total_their_attack,
    sum(minion.get_health() for minion in me.board) - sum(minion.get_health() for minion in them.board),
    sum(1 for attrs in my_attrs if Attributes.TAUNT in attrs),
    sum(1 for attrs in their_attrs if Attributes.TAUNT in attrs),
    sum(1 for attrs in my_attrs if Attributes.DIVINE_SHIELD in attrs),
    sum(1 for attrs in their_attrs if Attributes.DIVINE_SHIELD in attrs),
    sum(1 for attrs in my_attrs if Attributes.LIFESTEAL in attrs),
    sum(1 for attrs in their_attrs if Attributes.LIFESTEAL in attrs),
    sum(1 for attrs in my_attrs if Attributes.SPELL_DAMAGE in attrs),
    sum(1 for attrs in their_attrs if Attributes.SPELL_DAMAGE in attrs),
    sum(sum(1 for attrs in my_attrs if attribute in attrs) for attribute in OTHER_POSITIVE_ATTRIBUTES),
    sum(sum(1 for attrs in their_attrs if attribute in attrs) for attribute in OTHER_POSITIVE_ATTRIBUTES),
    len(me.hand) - len(them.hand),
    len(me.deck) - len(them.deck),
    len(me.secrets_zone) - len(them.secrets_zone),
    (me.get_attack() + total_my_attack) - them.health,  #lethal_margin_mine
    (them.get_attack() + total_their_attack) - me.health,  #lethal_margin_theirs
    (my_weapon.get_health() if my_weapon else 0) - (their_weapon.get_health() if their_weapon else 0),
    1 / (len(them.deck) + 1) - 1 / (len(me.deck) + 1),  #fatigue_proximity
    (0 if me.used_hero_power else 1) - (0 if them.used_hero_power else 1),
    me.current_mana,  #unused_mana
  ]


def _has_deathrattle(card):
  return any(getattr(effect, "trigger", None) == Triggers.DEATHRATTLE
             for effect in _walk_effects(card.effect))


def extract_candidate_features(state, me):
  """Candidate features under evaluation - Naxx mechanics (board
  stickiness) and observable opponent-threat / own-hand-playability proxies
  the original set lacks. Cheap and static only: no simulation here."""
  them = me.other_player

  my_attrs = [minion.get_all_attributes() for minion in me.board]
  their_attrs = [minion.get_all_attributes() for minion in them.board]

  deathrattle_count_difference = (sum(1 for minion in me.board if _has_deathrattle(minion))
                                  - sum(1 for minion in them.board if _has_deathrattle(minion)))

  taunt_health_difference = (
    sum(minion.get_health() for minion, attrs in zip(me.board, my_attrs) if Attributes.TAUNT in attrs)
    - sum(minion.get_health() for minion, attrs in zip(them.board, their_attrs) if Attributes.TAUNT in attrs))

  their_next_mana = min(them.max_mana + 1, 10)
  their_hand_mana_threat = len(them.hand) * their_next_mana

  my_next_mana = min(me.max_mana + 1, 10)
  my_playable_next_turn = sum(1 for card in me.hand if card.get_manacost() <= my_next_mana)

  divine_shield_attack_difference = (
    sum(minion.get_attack() for minion, attrs in zip(me.board, my_attrs) if Attributes.DIVINE_SHIELD in attrs)
    - sum(minion.get_attack() for minion, attrs in zip(them.board, their_attrs) if Attributes.DIVINE_SHIELD in attrs))

  their_weapon = them.weapon
  enemy_weapon_damage_pending = (their_weapon.get_attack() * their_weapon.get_health()) if their_weapon else 0

  return [
    deathrattle_count_difference, taunt_health_difference,
    their_hand_mana_threat, my_playable_next_turn,
    divine_shield_attack_difference, enemy_weapon_damage_pending,
  ]
