"""hearth-rs backend for the metagame pipelines.

Drop-in replacement for run_matchups_local / run_matchups_ssh in
evolve_metagame_shift.py: same work-item shape in, same result shape out,
but games run on the hearth-rs Rust engine (correct rules, pure
enumeration, net-guided search agents) via its PyO3 `hearth` module.
Batch API contract: hearth-rs docs/meta_prediction_requests.md.

Why: the S4 correction (validation README) showed this Python engine's
search results were artifact-dominated; the rerun campaign moves all
game-playing onto hearth-rs while the evolution/probe/scoring loops stay
here.

Work item in (classic_sim shape):
  (deck, player_class, opponent_deck, opponent_class, era, eval_weights
   [, min_games, max_games])
eval_weights is IGNORED (hearth agents carry their own evaluators); the
piloting agent is the module-level AGENT_SPEC (both sides, self-play,
matching the old pipeline's symmetric-pilot convention). min/max games:
fixed-games items (min==max) use that count; exploratory items use
DEFAULT_GAMES (hearth has no early stopping - games are cheap now).

Result out, per item: (winrate, avg_hand_size, avg_turns) with draws
counted 0.5, hand size = the PLAYER side's per-turn average, matching
_run_one in evolve_metagame_shift.py.

Module location: set HEARTHRS_PYD_DIR to a directory containing
hearth.pyd, or pip-install the maturin wheel; default falls back to the
hearth-rs release build (hearth.dll copied to hearth.pyd on first use).
"""
import os
import shutil
import sys
from pathlib import Path

HEARTH_RS = Path(os.environ.get("HEARTHRS_REPO", r"C:\Users\alexe\post_sub\hearth-rs"))
DEFAULT_GAMES = 12
AGENT_SPEC = "az3:400@" + str(HEARTH_RS / "tests" / "data" / "az3_net.json")
BASE_SEED = 0

ERA_MAP = {
    "naxx_launch": "naxx_launch",
    "buzzard_nerf": "post_nerf",
}

_hearth = None


def _load_hearth():
    global _hearth
    if _hearth is not None:
        return _hearth
    try:
        import hearth
    except ImportError:
        pyd_dir = os.environ.get("HEARTHRS_PYD_DIR")
        if pyd_dir is None:
            # fall back to the release build; the cdylib imports fine once
            # named .pyd (abi3), copied next to itself to avoid touching
            # the cargo output
            release = HEARTH_RS / "target" / "release"
            pyd = release / "hearth.pyd"
            dll = release / "hearth.dll"
            if not pyd.exists() and dll.exists():
                shutil.copyfile(dll, pyd)
            pyd_dir = str(release)
        sys.path.insert(0, pyd_dir)
        import hearth
    _hearth = hearth
    return hearth


def configure(agent_spec=None, default_games=None, base_seed=None):
    global AGENT_SPEC, DEFAULT_GAMES, BASE_SEED
    if agent_spec is not None:
        AGENT_SPEC = agent_spec
    if default_games is not None:
        DEFAULT_GAMES = default_games
    if base_seed is not None:
        BASE_SEED = base_seed


def _translate(item, index):
    deck, player_class, opp_deck, opp_class, era = item[0], item[1], item[2], item[3], item[4]
    n_games = int(item[6]) if len(item) >= 8 else DEFAULT_GAMES
    if era not in ERA_MAP:
        raise ValueError(f"unmapped era {era!r} (known: {sorted(ERA_MAP)})")
    # index-derived seeds so duplicate matchups stay independent while the
    # whole batch remains reproducible from BASE_SEED
    seed = (BASE_SEED * 1_000_003 + index * 7_919 + 1) & 0x7FFFFFFF
    return (list(deck), player_class.lower(), list(opp_deck), opp_class.lower(),
            ERA_MAP[era], AGENT_SPEC, n_games, seed)


def run_matchups_hearthrs(work_items, cores=0):
    """Interface-compatible with run_matchups_local/_ssh (cores=0: all)."""
    hearth = _load_hearth()
    batch = [_translate(item, i) for i, item in enumerate(work_items)]
    raw = hearth.simulate_batch(batch, threads=max(0, cores))
    results = []
    for (wins1, losses1, draws, games) in raw:
        n = wins1 + losses1 + draws
        winrate = (wins1 + 0.5 * draws) / n if n else 0.5
        avg_hand = sum(g[2] for g in games) / len(games) if games else 0.0
        avg_turns = sum(g[1] for g in games) / len(games) if games else 0.0
        results.append((winrate, avg_hand, avg_turns))
    return results


if __name__ == "__main__":
    # self-test: one real matchup per era through the full translation
    import json
    seeds_dir = Path(__file__).parent / ".." / "validation" / "data"
    prenerf = json.load((seeds_dir / "naxx_seeds_naxx_prenerf.json").open(encoding="utf-8"))
    configure(agent_spec="mcts-guided:100", default_games=4)
    work = [
        (prenerf["HUNTER"][0], "HUNTER", prenerf["MAGE"][0], "MAGE", "naxx_launch", None),
        (prenerf["HUNTER"][0], "HUNTER", prenerf["MAGE"][0], "MAGE", "buzzard_nerf", None),
    ]
    for (wr, hand, turns), era in zip(run_matchups_hearthrs(work), ("naxx_launch", "buzzard_nerf")):
        print(f"{era:14s} winrate={wr:.3f} avg_hand={hand:.2f} avg_turns={turns:.1f}")
    print("hearthrs_backend self-test ok")
