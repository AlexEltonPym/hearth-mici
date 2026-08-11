"""Information-theoretic usefulness analysis of the heuristic features.

Reads the dataset from gen_feature_dataset.py and reports, per feature:
- univariate mutual information with the game outcome, against a
  shuffled-label noise floor (estimator sanity check);
- held-out incremental value: logistic regression on the current 26 ->
  add each candidate singly -> delta AUC and delta log-loss;
- the same treatment (removal) for the two suspected-dead current
  features (weapon_durability_difference, unused_mana);
- permutation importance on the full model;
- max |correlation| of each candidate with any current feature
  (redundancy flag).

Decision rule (the M5 gate): adopt a candidate iff its held-out delta AUC
is positive and its MI clears the shuffled-label noise floor.

Usage: python analyze_feature_usefulness.py [--data data/feature_study/feature_dataset.npz]
"""
import sys, json, argparse
from pathlib import Path

sys.path.append('../../src')
import numpy as np
from sklearn.feature_selection import mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss
from sklearn.preprocessing import StandardScaler

from heuristic_features import FEATURE_NAMES, CANDIDATE_NAMES

N_CURRENT = len(FEATURE_NAMES)
ALL_NAMES = FEATURE_NAMES + CANDIDATE_NAMES
DROP_SUSPECTS = ["weapon_durability_difference", "unused_mana"]


def fit_auc(train_x, train_y, test_x, test_y, seed=0):
  scaler = StandardScaler().fit(train_x)
  model = LogisticRegression(max_iter=2000, random_state=seed)
  model.fit(scaler.transform(train_x), train_y)
  probabilities = model.predict_proba(scaler.transform(test_x))[:, 1]
  return roc_auc_score(test_y, probabilities), log_loss(test_y, probabilities), model, scaler


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--data", default="data/feature_study/feature_dataset.npz")
  parser.add_argument("--out", default="data/feature_study/usefulness.json")
  parser.add_argument("--seed", type=int, default=0)
  args = parser.parse_args()

  with np.load(args.data) as data:
    features = data["features"].astype(np.float64)
    target = (data["target"] > 0).astype(int)
  n = len(target)
  assert features.shape[1] == len(ALL_NAMES), \
    f"dataset has {features.shape[1]} columns, expected {len(ALL_NAMES)}"
  print(f"{n} samples, {features.shape[1]} features, base rate {target.mean():.3f}")

  rng = np.random.RandomState(args.seed)
  order = rng.permutation(n)
  split = int(n * 0.8)
  train_idx, test_idx = order[:split], order[split:]

  #--- univariate MI + shuffled-label noise floor
  mi = mutual_info_classif(features, target, random_state=args.seed)
  shuffled = target.copy()
  rng.shuffle(shuffled)
  mi_floor = mutual_info_classif(features, shuffled, random_state=args.seed)
  noise_ceiling = float(mi_floor.max())
  print(f"\nnoise floor (max MI vs shuffled labels): {noise_ceiling:.5f}")

  #--- baseline: current 26 features
  base_auc, base_ll, base_model, base_scaler = fit_auc(
    features[train_idx][:, :N_CURRENT], target[train_idx],
    features[test_idx][:, :N_CURRENT], target[test_idx], args.seed)
  print(f"baseline (26 current): AUC={base_auc:.4f} logloss={base_ll:.4f}")

  results = {"n_samples": int(n), "noise_floor_mi": noise_ceiling,
             "baseline_auc": float(base_auc), "baseline_logloss": float(base_ll),
             "features": {}}

  #--- candidates: add singly to the 26
  print("\ncandidates (added singly to the current 26):")
  for k, name in enumerate(CANDIDATE_NAMES):
    columns = list(range(N_CURRENT)) + [N_CURRENT + k]
    auc, ll, _, _ = fit_auc(features[train_idx][:, columns], target[train_idx],
                             features[test_idx][:, columns], target[test_idx], args.seed)
    corr = max(abs(np.corrcoef(features[:, N_CURRENT + k], features[:, j])[0, 1])
               for j in range(N_CURRENT))
    feature_mi = float(mi[N_CURRENT + k])
    adopt = auc > base_auc and feature_mi > noise_ceiling
    results["features"][name] = {
      "kind": "candidate", "mi": feature_mi, "delta_auc": float(auc - base_auc),
      "delta_logloss": float(ll - base_ll), "max_corr_with_current": float(corr),
      "adopt": bool(adopt)}
    print(f"  {name:34s} MI={feature_mi:.5f} dAUC={auc - base_auc:+.5f} "
          f"dLL={ll - base_ll:+.5f} maxcorr={corr:.2f} -> {'ADOPT' if adopt else 'reject'}")

  #--- drop suspects: remove singly from the 26
  print("\ndrop suspects (removed singly from the current 26):")
  for name in DROP_SUSPECTS:
    j = FEATURE_NAMES.index(name)
    columns = [c for c in range(N_CURRENT) if c != j]
    auc, ll, _, _ = fit_auc(features[train_idx][:, columns], target[train_idx],
                             features[test_idx][:, columns], target[test_idx], args.seed)
    feature_mi = float(mi[j])
    #dropping is safe if removal does not hurt held-out AUC
    drop = auc >= base_auc - 1e-4
    results["features"][name] = {
      "kind": "drop_suspect", "mi": feature_mi, "delta_auc_when_removed": float(auc - base_auc),
      "drop": bool(drop)}
    print(f"  {name:34s} MI={feature_mi:.5f} dAUC(removed)={auc - base_auc:+.5f} "
          f"-> {'DROP' if drop else 'keep'}")

  #--- permutation importance on the full model (all columns)
  full_auc, _, full_model, full_scaler = fit_auc(
    features[train_idx], target[train_idx], features[test_idx], target[test_idx], args.seed)
  print(f"\nfull model (26+{len(CANDIDATE_NAMES)}): AUC={full_auc:.4f}; permutation importances:")
  importances = []
  test_x = full_scaler.transform(features[test_idx])
  test_y = target[test_idx]
  for j, name in enumerate(ALL_NAMES):
    permuted = test_x.copy()
    permuted[:, j] = rng.permutation(permuted[:, j])
    drop_auc = full_auc - roc_auc_score(test_y, full_model.predict_proba(permuted)[:, 1])
    importances.append((name, float(drop_auc)))
  for name, importance in sorted(importances, key=lambda kv: -kv[1])[:12]:
    print(f"  {name:34s} {importance:+.5f}")
  results["permutation_importance"] = dict(importances)
  results["full_model_auc"] = float(full_auc)

  out = Path(args.out)
  out.parent.mkdir(parents=True, exist_ok=True)
  with out.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
  print(f"\nwrote {out}")


if __name__ == "__main__":
  main()
