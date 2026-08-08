"""Feature-based state encoder + small value network (pure numpy forward pass).

Design constraints, and why:
- Cards are encoded by WHAT THEY DO (stats, keywords, effect family, trigger,
  scope), never by identity. An ID embedding would be strictly easier to fit
  on the 221-card Classic pool, but it makes every future card a cold start.
  Feature encoding is what lets a net trained purely on the pre-Naxx world
  produce a meaningful (if imperfect) valuation of Webspinner or Death's Bite
  the first time it sees them - the unseen-card generalization experiment is
  the point of this whole phase (cf. ByteRL/LOCM 1.5 and Bertram et al. 2024,
  where feature/text card representations transfer to unseen cards and ID
  representations score near zero).
- The forward pass is pure numpy because inference runs inside the dwail
  workers (Python 3.8, no torch) at ~thousands of calls per game. Training
  happens elsewhere (torch mirror in examples/metagame_analysis) and exports
  a plain dict of arrays that this module consumes.
- Hidden information is respected: the encoder sees the acting player's own
  hand/deck contents but only COUNTS for the opponent's - same information a
  real player has. No oracle features, so the trained value function is
  legitimate to compare against human play.

Architecture (deep-sets style, ~50k params):
  per-minion  (static 60 + dynamic 9  = 69) -> 64 relu -> 32 relu, pooled sum+max per side
  per-hand-card (static 60 + playable 1 = 61) -> 64 relu -> 32 relu, pooled sum+max
  trunk: [my_board 64 | enemy_board 64 | my_hand 64 | globals 24] -> 128 relu -> 64 relu -> 1 tanh
Value is from the perspective of `me` (+1 = winning).
"""
import numpy as np

from enums import Attributes, CardTypes, CreatureTypes, Triggers, Methods, OwnerFilters, Classes
from effects import (DealDamage, Destroy, ChangeStats, SetStats, SwapStats, GainArmor, DrawCards,
                     Tutor, ReturnToHand, RestoreHealth, GiveAttribute, RemoveAttribute,
                     SummonToken, AddCardToHand, Resurrect, DoubleDeathrattles, TakeControl,
                     ReplaceWithToken, RedirectToToken, Silence, ChangeCost, SwapWithMinion,
                     CopyMinion, Redirect, Counterspell, GainMana)

CARD_TYPES = [CardTypes.MINION, CardTypes.SPELL, CardTypes.WEAPON, CardTypes.HERO_POWER, CardTypes.SECRET]
CREATURE_TYPES = [CreatureTypes.PIRATE, CreatureTypes.BEAST, CreatureTypes.ELEMENTAL, CreatureTypes.TOTEM,
                  CreatureTypes.MECH, CreatureTypes.MURLOC, CreatureTypes.DRAGON, CreatureTypes.DEMON]
KEYWORD_ATTRIBUTES = [Attributes.TAUNT, Attributes.LIFESTEAL, Attributes.DIVINE_SHIELD, Attributes.CHARGE,
                      Attributes.STEALTH, Attributes.WINDFURY, Attributes.HEXPROOF, Attributes.SPELL_DAMAGE,
                      Attributes.POISONOUS, Attributes.IMMUNE, Attributes.FREEZER, Attributes.CANT_ATTACK]
#effect families: one slot per "kind of thing a card can do", shared by the
#effect classes that do that thing - new cards built from the same effect
#vocabulary land in existing slots automatically
EFFECT_FAMILIES = [
  (DealDamage,), (Destroy,), (ChangeStats, SwapStats), (SetStats,), (GainArmor, GainMana),
  (DrawCards,), (Tutor, AddCardToHand), (RestoreHealth,), (GiveAttribute,),
  (RemoveAttribute, Silence), (SummonToken, ReplaceWithToken), (Resurrect, DoubleDeathrattles),
  (TakeControl, CopyMinion, SwapWithMinion), (Redirect, RedirectToToken, Counterspell),
  (ReturnToHand,), (ChangeCost,),
]
#ongoing-trigger categories: without these, every triggered minion collapses
#into one flag (Undertaker would encode identically to Secretkeeper)
TRIGGER_CATEGORIES = [
  (Triggers.ANY_MINION_SUMMONED, Triggers.ANY_SAME_TYPE_SUMMONED, Triggers.FRIENDLY_MINION_SUMMONED,
   Triggers.FRIENDLY_SAME_TYPE_SUMMONED, Triggers.ENEMY_MINION_SUMMONED, Triggers.ENEMY_SAME_TYPE_SUMMONED,
   Triggers.FRIENDLY_LESS_THAN_FOUR_ATTACK_SUMMONED, Triggers.ANY_MINION_PLAYED,
   Triggers.FRIENDLY_MINION_PLAYED, Triggers.ENEMY_MINION_PLAYED),
  (Triggers.ANY_MINION_DIES, Triggers.FRIENDLY_MINION_DIES, Triggers.ENEMY_MINION_DIES,
   Triggers.FRIENDLY_SAME_TYPE_DIES, Triggers.LETHAL_DAMAGE),
  (Triggers.ANY_MINION_DAMAGED, Triggers.FRIENDLY_MINION_DAMAGED, Triggers.ENEMY_MINION_DAMAGED,
   Triggers.SELF_DAMAGE_TAKEN),
  (Triggers.ANY_SPELL_CAST, Triggers.FRIENDLY_SPELL_CAST, Triggers.ENEMY_SPELL_CAST,
   Triggers.ANY_SECRET_CAST, Triggers.FRIENDLY_SECRET_CAST, Triggers.ENEMY_SECRET_CAST,
   Triggers.ENEMY_SPELL_COUNTERED, Triggers.ENEMY_SPELL_REDIRECTED),
  (Triggers.ANY_HEALED, Triggers.FRIENDLY_HEALED, Triggers.ENEMY_HEALED),
  (Triggers.FRIENDLY_END_TURN, Triggers.ENEMY_END_TURN, Triggers.ANY_END_TURN,
   Triggers.FRIENDLY_UNTAP, Triggers.ENEMY_UNTAP, Triggers.ANY_UNTAP),
  (Triggers.HERO_ATTACKED, Triggers.ENEMY_MINION_ATTACKS, Triggers.ENEMY_ATTACKS_MINION),
  (Triggers.FRIENDLY_WEAPON_PLAYED, Triggers.ENEMY_WEAPON_PLAYED, Triggers.ANY_WEAPON_PLAYED,
   Triggers.FRIENDLY_CARD_PLAYED, Triggers.ENEMY_CARD_PLAYED, Triggers.ANY_CARD_PLAYED),
]
METHOD_FLAGS = [Methods.TARGETED, Methods.RANDOMLY, Methods.ALL, Methods.SELF, Methods.TRIGGERER, Methods.ADJACENT]
OWNER_FLAGS = [OwnerFilters.FRIENDLY, OwnerFilters.ENEMY, OwnerFilters.ALL]
CLASS_LIST = [Classes.HUNTER, Classes.MAGE, Classes.WARRIOR]

STATIC_DIM = 3 + len(CARD_TYPES) + len(CREATURE_TYPES) + len(KEYWORD_ATTRIBUTES) \
             + 3 + len(TRIGGER_CATEGORIES) + len(EFFECT_FAMILIES) + len(METHOD_FLAGS) \
             + len(OWNER_FLAGS) + 2 + 2  #= 68
DYNAMIC_DIM = 9
HAND_EXTRA_DIM = 1
GLOBAL_DIM = 18 + 2 * len(CLASS_LIST)  #= 24
MAX_BOARD = 7
MAX_HAND = 10

_static_cache = {}


def _dynamics_magnitude(value, depth=0):
  """Best-effort numeric size of an effect value: plain ints, ConstantInt
  leaves, and the mean over conditional branches (IfInt(cond, 6, 4) -> 5).
  Crude, but it separates Fireball from Arcane Shot within the same family."""
  if isinstance(value, (int, float)):
    return abs(value)
  if isinstance(value, tuple):
    return sum(_dynamics_magnitude(v, depth + 1) for v in value)
  constant = getattr(value, "constant", None)
  if isinstance(constant, (int, float)):
    return abs(constant)
  result, alternative = getattr(value, "result", None), getattr(value, "alternative", None)
  if depth < 3 and result is not None and alternative is not None:
    return (_dynamics_magnitude(result, depth + 1) + _dynamics_magnitude(alternative, depth + 1)) / 2.0
  return 0.0


def _walk_effects(effect):
  """Flatten an effect tree (DualEffect/Cantrip/MultiEffectRandom nesting)."""
  if effect is None:
    return []
  found = [effect]
  for attr in ("first_effect", "second_effect"):
    child = getattr(effect, attr, None)
    if child is not None:
      found.extend(_walk_effects(child))
  for child in getattr(effect, "effects", None) or []:
    found.extend(_walk_effects(child))
  return found


def card_static_features(card):
  """60-dim description of the pristine card. Cached by (name, original stats)
  so nerf-patched pools (same name, different cost) encode correctly."""
  key = (card.name, card.original_manacost, card.original_attack, card.original_health)
  cached = _static_cache.get(key)
  if cached is not None:
    return cached

  features = np.zeros(STATIC_DIM, dtype=np.float32)
  i = 0
  features[i] = card.original_manacost / 10.0; i += 1
  features[i] = (card.original_attack or 0) / 10.0; i += 1
  features[i] = (card.original_health or 0) / 10.0; i += 1
  for j, card_type in enumerate(CARD_TYPES):
    features[i + j] = 1.0 if card.card_type == card_type else 0.0
  i += len(CARD_TYPES)
  for j, creature_type in enumerate(CREATURE_TYPES):
    features[i + j] = 1.0 if card.creature_type == creature_type else 0.0
  i += len(CREATURE_TYPES)
  for j, attribute in enumerate(KEYWORD_ATTRIBUTES):
    features[i + j] = 1.0 if attribute in (card.original_attributes or []) else 0.0
  i += len(KEYWORD_ATTRIBUTES)

  effects = _walk_effects(card.original_effect)
  triggers = [e.trigger for e in effects if getattr(e, "trigger", None) is not None]
  features[i] = 1.0 if Triggers.BATTLECRY in triggers else 0.0
  features[i + 1] = 1.0 if Triggers.DEATHRATTLE in triggers else 0.0
  features[i + 2] = 1.0 if Triggers.AURA in triggers else 0.0
  i += 3
  for j, category in enumerate(TRIGGER_CATEGORIES):
    features[i + j] = 1.0 if any(t in category for t in triggers) else 0.0
  i += len(TRIGGER_CATEGORIES)
  for effect in effects:
    for j, family in enumerate(EFFECT_FAMILIES):
      if isinstance(effect, family):
        features[i + j] = 1.0
  i += len(EFFECT_FAMILIES)
  methods = [getattr(e, "method", None) for e in effects]
  for j, method in enumerate(METHOD_FLAGS):
    features[i + j] = 1.0 if method in methods else 0.0
  i += len(METHOD_FLAGS)
  owners = [getattr(e, "owner_filter", None) for e in effects]
  for j, owner in enumerate(OWNER_FLAGS):
    features[i + j] = 1.0 if owner in owners else 0.0
  i += len(OWNER_FLAGS)
  magnitude = sum(_dynamics_magnitude(getattr(e, "value", None)) for e in effects)
  features[i] = min(magnitude, 12.0) / 10.0
  features[i + 1] = min(len(effects), 3) / 3.0
  i += 2
  features[i] = 1.0 if card.original_condition is not None else 0.0
  features[i + 1] = 1.0 if any(getattr(e, "dynamic_filter", None) is not None for e in effects) else 0.0

  _static_cache[key] = features
  return features


def _minion_dynamic_features(minion):
  features = np.zeros(DYNAMIC_DIM, dtype=np.float32)
  attributes = minion.get_all_attributes()
  attack, health = minion.get_attack(), minion.get_health()
  features[0] = attack / 10.0
  features[1] = health / 10.0
  features[2] = 1.0 if health < minion.get_max_health() else 0.0  #damaged (enrage etc)
  can_attack = (minion.attacks_this_turn == 0
                or (minion.attacks_this_turn == -1 and Attributes.CHARGE in attributes)
                or (minion.attacks_this_turn == 1 and Attributes.WINDFURY in attributes))
  features[3] = 1.0 if (can_attack and attack > 0 and Attributes.FROZEN not in attributes
                        and Attributes.CANT_ATTACK not in attributes) else 0.0
  features[4] = 1.0 if Attributes.FROZEN in attributes else 0.0
  features[5] = 1.0 if Attributes.TAUNT in attributes else 0.0
  features[6] = 1.0 if Attributes.DIVINE_SHIELD in attributes else 0.0
  features[7] = 1.0 if Attributes.STEALTH in attributes else 0.0
  features[8] = 1.0 if Attributes.WINDFURY in attributes else 0.0
  return features


def _board_matrix(player):
  rows = []
  for minion in list(player.board)[:MAX_BOARD]:
    rows.append(np.concatenate([card_static_features(minion), _minion_dynamic_features(minion)]))
  if not rows:
    return np.zeros((0, STATIC_DIM + DYNAMIC_DIM), dtype=np.float32)
  return np.stack(rows)


def _hand_matrix(player):
  rows = []
  mana = player.current_mana
  for card in player.hand:
    playable = np.array([1.0 if card.get_manacost() <= mana else 0.0], dtype=np.float32)
    rows.append(np.concatenate([card_static_features(card), playable]))
  if not rows:
    return np.zeros((0, STATIC_DIM + HAND_EXTRA_DIM), dtype=np.float32)
  return np.stack(rows)


def global_features(me, them):
  my_weapon, their_weapon = me.weapon, them.weapon
  features = [
    me.health / 30.0, them.health / 30.0,
    me.armor / 10.0, them.armor / 10.0,
    me.current_mana / 10.0, me.max_mana / 10.0, them.max_mana / 10.0,
    (my_weapon.get_attack() if my_weapon else 0) / 10.0,
    (my_weapon.get_health() if my_weapon else 0) / 10.0,
    (their_weapon.get_attack() if their_weapon else 0) / 10.0,
    (their_weapon.get_health() if their_weapon else 0) / 10.0,
    len(me.hand) / 10.0, len(them.hand) / 10.0,
    len(me.deck) / 30.0, len(them.deck) / 30.0,
    len(me.secrets_zone) / 5.0, len(them.secrets_zone) / 5.0,
    (0.0 if me.used_hero_power else 1.0) - (0.0 if them.used_hero_power else 1.0),
  ]
  for player_class in CLASS_LIST:
    features.append(1.0 if me.player_class == player_class else 0.0)
  for player_class in CLASS_LIST:
    features.append(1.0 if them.player_class == player_class else 0.0)
  return np.array(features, dtype=np.float32)


def encode_state(state, me=None):
  """Returns the four input blocks for the net, from `me`'s perspective
  (default: state.current_player)."""
  me = me if me is not None else state.current_player
  them = me.other_player
  return _board_matrix(me), _board_matrix(them), _hand_matrix(me), global_features(me, them)


def encode_state_padded(state, me=None):
  """Fixed-size float16 blocks + row counts, for training-sample storage.
  The torch trainer masks padding rows by count; the play-time numpy forward
  never sees padding (it gets the variable-row matrices from encode_state)."""
  my_board, their_board, my_hand, globals_vec = encode_state(state, me)
  my_board_p = np.zeros((MAX_BOARD, STATIC_DIM + DYNAMIC_DIM), dtype=np.float16)
  their_board_p = np.zeros((MAX_BOARD, STATIC_DIM + DYNAMIC_DIM), dtype=np.float16)
  hand_p = np.zeros((MAX_HAND, STATIC_DIM + HAND_EXTRA_DIM), dtype=np.float16)
  for target, source in ((my_board_p, my_board), (their_board_p, their_board), (hand_p, my_hand)):
    n = min(len(source), len(target))
    if n:
      target[:n] = source[:n]
  counts = np.array([min(len(my_board), MAX_BOARD), min(len(their_board), MAX_BOARD),
                     min(len(my_hand), MAX_HAND)], dtype=np.uint8)
  return my_board_p, their_board_p, hand_p, globals_vec.astype(np.float16), counts


#----------------------------------------------------------------------------
#network: init / forward / save / load. Weights are a plain dict[str, ndarray]
#so they dill-serialize into worker payloads and round-trip through .npz.

EMBED_HIDDEN = 64
EMBED_DIM = 32
TRUNK_HIDDEN = 128
TRUNK_HIDDEN2 = 64


def init_weights(seed=None):
  rng = np.random.RandomState(seed)

  def he(fan_in, fan_out):
    return (rng.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)).astype(np.float32)

  board_in = STATIC_DIM + DYNAMIC_DIM
  hand_in = STATIC_DIM + HAND_EXTRA_DIM
  trunk_in = 3 * (2 * EMBED_DIM) + GLOBAL_DIM  #my board + their board + my hand + globals
  return {
    "board_w1": he(board_in, EMBED_HIDDEN), "board_b1": np.zeros(EMBED_HIDDEN, dtype=np.float32),
    "board_w2": he(EMBED_HIDDEN, EMBED_DIM), "board_b2": np.zeros(EMBED_DIM, dtype=np.float32),
    "hand_w1": he(hand_in, EMBED_HIDDEN), "hand_b1": np.zeros(EMBED_HIDDEN, dtype=np.float32),
    "hand_w2": he(EMBED_HIDDEN, EMBED_DIM), "hand_b2": np.zeros(EMBED_DIM, dtype=np.float32),
    "trunk_w1": he(trunk_in, TRUNK_HIDDEN), "trunk_b1": np.zeros(TRUNK_HIDDEN, dtype=np.float32),
    "trunk_w2": he(TRUNK_HIDDEN, TRUNK_HIDDEN2), "trunk_b2": np.zeros(TRUNK_HIDDEN2, dtype=np.float32),
    "trunk_w3": he(TRUNK_HIDDEN2, 1), "trunk_b3": np.zeros(1, dtype=np.float32),
  }


def _embed_pool(matrix, w1, b1, w2, b2):
  """Shared per-card MLP then sum+max pool -> fixed 2*EMBED_DIM vector."""
  if matrix.shape[0] == 0:
    return np.zeros(2 * EMBED_DIM, dtype=np.float32)
  h = np.maximum(matrix @ w1 + b1, 0.0)
  h = np.maximum(h @ w2 + b2, 0.0)
  return np.concatenate([h.sum(axis=0), h.max(axis=0)])


def forward(weights, my_board, their_board, my_hand, globals_vec):
  mine = _embed_pool(my_board, weights["board_w1"], weights["board_b1"],
                     weights["board_w2"], weights["board_b2"])
  theirs = _embed_pool(their_board, weights["board_w1"], weights["board_b1"],
                       weights["board_w2"], weights["board_b2"])
  hand = _embed_pool(my_hand, weights["hand_w1"], weights["hand_b1"],
                     weights["hand_w2"], weights["hand_b2"])
  x = np.concatenate([mine, theirs, hand, globals_vec])
  x = np.maximum(x @ weights["trunk_w1"] + weights["trunk_b1"], 0.0)
  x = np.maximum(x @ weights["trunk_w2"] + weights["trunk_b2"], 0.0)
  return float(np.tanh(x @ weights["trunk_w3"] + weights["trunk_b3"])[0])


def evaluate_state(weights, state, me=None):
  """Value in [-1, 1] from `me`'s perspective (default current_player)."""
  my_board, their_board, my_hand, globals_vec = encode_state(state, me)
  return forward(weights, my_board, their_board, my_hand, globals_vec)


def save_weights(weights, path):
  np.savez(path, **weights)


def load_weights(path):
  with np.load(path) as data:
    return {key: data[key] for key in data.files}
