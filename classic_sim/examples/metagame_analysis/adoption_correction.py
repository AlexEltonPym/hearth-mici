"""Level correction for predicted card-adoption shares (the "readout").

The evolution pipeline reports adoption as card-inclusion share over the
archive's elite decks. That raw readout has two level errors that Spearman
is blind to (it is monotone-invariant, so ranking looks fine while levels
are wrong):

  1. Finite-sample ceiling. A card in all k of k elites reads as exactly
     100%. With only 18-40 elites per bucket this saturates constantly.
  2. Mass inflation. Inclusion shares must sum to the mean number of
     DISTINCT cards per deck. Real 2014 decks average 17.5-18.9 distinct
     cards (heavy 2-of play); evolved elites average 19-23, so every share
     is inflated ~15-25% before any ranking question is asked.

mass_match fixes both with a Jeffreys point estimate plus a single logit
shift solved so total predicted mass equals the pre-shock real mass. It
imports ONE scalar (that target mass, from pre-shock data only - the same
information the no-change baseline has) and is monotone in the raw share,
so movers Spearman and top-N are preserved to the digit. Measured effect
on the rolling runs: levels MAE -21%, saturated cells 35 -> 0, movers
Spearman bit-identical (see the S3 rolling-readout results in
examples/validation/README.md; method validated in adoption_readout.py).

This is a REPORTING-time correction. The archives and raw *_predicted_*.csv
stay untouched as the record; callers apply mass_match when scoring or
plotting.
"""
import math


def mass_match(prediction, reference, pool, n_decks):
  """prediction, reference: {card: share}. pool: iterable of card names to
  correct over. reference is the pre-shock real adoption (supplies the
  target mass). n_decks: number of elite decks the prediction was read from
  (drives the Jeffreys smoothing). Returns {card: corrected share}."""
  target_mass = sum(reference.get(card, 0.0) for card in pool)
  cards = sorted(pool)
  logits = []
  for card in cards:
    share = prediction.get(card, 0.0)
    k = share * n_decks
    smoothed = min(1 - 1e-9, max(1e-9, (k + 0.5) / (n_decks + 1)))
    logits.append(math.log(smoothed / (1 - smoothed)))

  def mass(delta):
    return sum(1 / (1 + math.exp(-(z + delta))) for z in logits)

  lo, hi = -20.0, 20.0
  for _ in range(80):
    mid = (lo + hi) / 2
    if mass(mid) < target_mass:
      lo = mid
    else:
      hi = mid
  delta = (lo + hi) / 2
  return {card: 1 / (1 + math.exp(-(z + delta))) for card, z in zip(cards, logits)}
