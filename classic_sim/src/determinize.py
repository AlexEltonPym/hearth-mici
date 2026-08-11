"""Opponent-hand determinization for imperfect-information search.

The engine is internally perfect-information: both hands are plain zones on
the state. Search that reads the opponent's actual hand is therefore
cheating from a game-theoretic standpoint. These helpers let a search
evaluate candidate plans against PLAUSIBLE opponent hands instead
(determinization, as in ISMCTS): sample a hand consistent with everything
publicly observable, simulate the reply, average over samples.

Two knowledge models, compared as an experiment in their own right (the
in-house replication of Dockhorn's ~2-4-point true-hand-value finding):

- determinize_opponent_hand: KNOWN-DECKLIST mode. The agent knows the
  opponent's decklist (and therefore the multiset of hand+deck cards) but
  not which of those cards are currently held. Shuffle the hidden hand back
  into the deck and redeal the observed hand size.
- sample_class_prior_hand: CLASS-PRIOR mode. No decklist knowledge - the
  hand is sampled fresh from the opponent's class-legal pool weighted by
  real-world inclusion shares (the S3 adoption CSVs). The deck is left
  untouched in this mode, deliberately: both modes then share identical
  deck knowledge for the reply turn's single draw, isolating the hand
  model as the only experimental difference.

Both functions:
- must be called on CLONES only - they destructively rearrange zones.
- take a PRIVATE numpy RandomState, never the shared game stream (clones
  share the live master RandomState via utilities._revive, so using it
  here would corrupt the real game's draw sequence).
- leave non-collectable hand cards (the Coin) untouched: their presence is
  public knowledge, not hidden information.

Card movement uses Card.change_parent (remove-from-old + add-to-new, the
engine's own move primitive - see mulligan, game.py) for existing cards and
set_parent for freshly created ones (the add_coin pattern). Hand/deck
membership registers no triggers or auras, so swaps are engine-safe.
"""
from copy import deepcopy


def determinize_opponent_hand(opponent, rng):
  """Shuffle the opponent's hidden (collectable) hand cards back into their
  deck and redeal the same count uniformly from the combined pool, then
  randomize the deck's draw order. Known-decklist determinization."""
  hidden_cards = [card for card in list(opponent.hand.get_all()) if card.collectable]
  hand_size = len(hidden_cards)
  for card in hidden_cards:
    card.change_parent(opponent.deck)

  pool = list(opponent.deck.get_all())
  if hand_size:
    picks = [pool[index] for index in rng.choice(len(pool), size=hand_size, replace=False)]
    for card in picks:
      card.change_parent(opponent.hand)

  #draws pop from the END of deck.zone, so an in-place shuffle randomizes
  #the top of the deck as well - same zone, parents unchanged
  rng.shuffle(opponent.deck.zone)


def _public_card_counts(opponent):
  #cards the opponent has visibly committed: board, graveyard, weapon.
  #Secrets are face-down (name unknown) and the hand is what we're
  #replacing, so neither counts against the caps.
  visible = list(opponent.board.get_all()) + list(opponent.graveyard.get_all())
  if opponent.weapon:
    visible.append(opponent.weapon)
  counts = {}
  for card in visible:
    counts[card.name] = counts.get(card.name, 0) + 1
  return counts


def sample_class_prior_hand(opponent, rng, priors, legendary_names=None):
  """Replace the opponent's hidden hand with fresh cards sampled from their
  class pool weighted by `priors` ({card_name: inclusion_share}); cards
  absent from priors get a small floor weight so the whole pool stays
  reachable. Respects 2-copy/1-legendary caps net of publicly played cards
  (legendary_names optional - without it only the 2-copy cap applies).
  The deck is deliberately left untouched (see module docstring)."""
  legendary_names = legendary_names or set()
  hidden_cards = [card for card in list(opponent.hand.get_all()) if card.collectable]
  hand_size = len(hidden_cards)
  for card in hidden_cards:
    #hypothetical unknowns being replaced: drop them from the clone entirely
    #(the reset_game non-collectable pattern)
    card.parent.remove(card)

  if not hand_size:
    return

  game_manager = opponent.game_manager
  pool = game_manager.get_player_pool() if opponent.name == "player" else game_manager.get_enemy_pool()
  prototypes = {card.name: card for card in pool}
  names = sorted(prototypes)
  floor = 0.01
  weights = [max(priors.get(name, 0.0), floor) for name in names]

  counts = _public_card_counts(opponent)
  sampled = 0
  attempts = 0
  total = sum(weights)
  probabilities = [w / total for w in weights]
  while sampled < hand_size and attempts < hand_size * 20:
    attempts += 1
    name = names[rng.choice(len(names), p=probabilities)]
    cap = 1 if name in legendary_names else 2
    if counts.get(name, 0) >= cap:
      continue
    counts[name] = counts.get(name, 0) + 1
    new_card = deepcopy(prototypes[name])
    new_card.set_owner(opponent)
    new_card.set_parent(opponent.hand)
    sampled += 1
