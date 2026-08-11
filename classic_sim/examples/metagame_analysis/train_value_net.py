"""Value-net training driver: DouZero-style "train cheap, search at test time".

Loop per generation:
  1. Generate self-play games with the CURRENT cheap agent (gen 0 bootstraps
     from the GreedyActionSmart self-play champion; later gens use
     NeuralGreedy with the freshest net, mixed with some games against the
     linear champion as an anti-collapse anchor). Games run on the dwails via
     the established dill-over-stdin workers; sampled decision states with
     Monte Carlo outcome targets come back as compressed npz shards over scp.
  2. Train the torch mirror of neural_eval's net on a sliding window of
     recent shards (warm-started from the previous generation's weights),
     export back to the plain-numpy weight dict the workers/strategies use.
  3. Ladder the new net against the linear champion and the previous net on
     a FIXED evaluation set of real-deck matchups (no epsilon), so progress
     is comparable across generations.

No search anywhere in the training loop - MCTS only ever sees the finished
net at evaluation/play time (Scheiermann & Konen 2022; DouZero 2021). The
training world is pre_naxx: real Jan-Jul 2014 decks, classic pool only, so
Naxx cards stay unseen for the later generalization experiment.

Usage (from classic_sim/examples/metagame_analysis):
  python train_value_net.py --backend local --cores 4 --pairs 8 \
      --games-per-pair 4 --generations 2            # smoke test
  python train_value_net.py --backend ssh --generations 12    # real run
"""
import sys, csv, json, argparse, subprocess, ast, shutil
from pathlib import Path
from random import Random
from statistics import mean

sys.path.append('../../src')
import dill
import numpy as np
from joblib import Parallel, delayed

import neural_eval as ne
from value_net_selfplay import run_item, concatenate_samples, WORLDS

HERE = Path(__file__).parent
#module-level defaults; main() rebinds from --out-dir / --seeds
OUT_DIR = HERE / "data" / "value_net"
SHARD_DIR = OUT_DIR / "shards"
SEEDS_PATH = HERE.parent / "validation" / "data" / "naxx_seeds_pre_naxx.json"
CHAMPION_PATH = HERE / "data" / "self_play_champion.json"

CLASSES = ["HUNTER", "MAGE", "WARRIOR"]
HOSTS = ["dwail1", "dwail2"]
REMOTE_DIR = "~/classic_sim/examples/metagame_analysis/"

REPLAY_WINDOW = 3       #train on shards from the last N generations
ANCHOR_FRACTION = 0.3   #fraction of post-bootstrap games vs the linear champion
LADDER_PAIRS = 24
LADDER_GAMES = 24


#----------------------------------------------------------------------------
#torch model - an exact mirror of neural_eval's numpy forward (masked for
#padded batches). Kept inside the driver: torch exists only on this machine.

def build_torch_model():
  import torch
  from torch import nn

  board_in = ne.STATIC_DIM + ne.DYNAMIC_DIM
  hand_in = ne.STATIC_DIM + ne.HAND_EXTRA_DIM
  trunk_in = 3 * (2 * ne.EMBED_DIM) + ne.GLOBAL_DIM

  class ValueNet(nn.Module):
    def __init__(self):
      super().__init__()
      self.board1 = nn.Linear(board_in, ne.EMBED_HIDDEN)
      self.board2 = nn.Linear(ne.EMBED_HIDDEN, ne.EMBED_DIM)
      self.hand1 = nn.Linear(hand_in, ne.EMBED_HIDDEN)
      self.hand2 = nn.Linear(ne.EMBED_HIDDEN, ne.EMBED_DIM)
      self.trunk1 = nn.Linear(trunk_in, ne.TRUNK_HIDDEN)
      self.trunk2 = nn.Linear(ne.TRUNK_HIDDEN, ne.TRUNK_HIDDEN2)
      self.trunk3 = nn.Linear(ne.TRUNK_HIDDEN2, 1)

    def _pool(self, layer1, layer2, rows, count):
      #rows (B, R, F), count (B,) -> (B, 2*EMBED_DIM), matching numpy's
      #sum+max over REAL rows only (padding must not leak through the biases)
      h = torch.relu(layer2(torch.relu(layer1(rows))))
      mask = (torch.arange(rows.shape[1], device=rows.device)[None, :] < count[:, None])
      h = h * mask[:, :, None]
      pooled_sum = h.sum(dim=1)
      pooled_max = h.masked_fill(~mask[:, :, None], float("-inf")).max(dim=1).values
      pooled_max = torch.where(count[:, None] > 0, pooled_max, torch.zeros_like(pooled_max))
      return torch.cat([pooled_sum, pooled_max], dim=1)

    def forward(self, my_board, their_board, hand, globals_vec, counts):
      mine = self._pool(self.board1, self.board2, my_board, counts[:, 0])
      theirs = self._pool(self.board1, self.board2, their_board, counts[:, 1])
      hand_pooled = self._pool(self.hand1, self.hand2, hand, counts[:, 2])
      x = torch.cat([mine, theirs, hand_pooled, globals_vec], dim=1)
      x = torch.relu(self.trunk1(x))
      x = torch.relu(self.trunk2(x))
      return torch.tanh(self.trunk3(x)).squeeze(-1)

  return ValueNet()


TORCH_TO_NUMPY = {
  "board1": ("board_w1", "board_b1"), "board2": ("board_w2", "board_b2"),
  "hand1": ("hand_w1", "hand_b1"), "hand2": ("hand_w2", "hand_b2"),
  "trunk1": ("trunk_w1", "trunk_b1"), "trunk2": ("trunk_w2", "trunk_b2"),
  "trunk3": ("trunk_w3", "trunk_b3"),
}


def export_to_numpy(model):
  #torch Linear stores weight as (out, in); the numpy forward uses (in, out)
  weights = {}
  state = model.state_dict()
  for torch_name, (w_name, b_name) in TORCH_TO_NUMPY.items():
    weights[w_name] = state[f"{torch_name}.weight"].numpy().T.astype(np.float32).copy()
    weights[b_name] = state[f"{torch_name}.bias"].numpy().astype(np.float32).copy()
  return weights


def import_from_numpy(model, weights):
  import torch
  state = {}
  for torch_name, (w_name, b_name) in TORCH_TO_NUMPY.items():
    state[f"{torch_name}.weight"] = torch.from_numpy(weights[w_name].T.copy())
    state[f"{torch_name}.bias"] = torch.from_numpy(weights[b_name].copy())
  model.load_state_dict(state)


def self_check():
  """Torch forward and numpy forward must agree - guards every refactor of
  either side. Run with --selfcheck."""
  import torch
  model = build_torch_model()
  weights = export_to_numpy(model)
  rng = np.random.RandomState(0)
  for _ in range(20):
    n_mine, n_theirs, n_hand = rng.randint(0, 8), rng.randint(0, 8), rng.randint(0, 11)
    my_board = rng.rand(ne.MAX_BOARD, ne.STATIC_DIM + ne.DYNAMIC_DIM).astype(np.float32)
    their_board = rng.rand(ne.MAX_BOARD, ne.STATIC_DIM + ne.DYNAMIC_DIM).astype(np.float32)
    hand = rng.rand(ne.MAX_HAND, ne.STATIC_DIM + ne.HAND_EXTRA_DIM).astype(np.float32)
    globals_vec = rng.rand(ne.GLOBAL_DIM).astype(np.float32)
    numpy_value = ne.forward(weights, my_board[:n_mine], their_board[:n_theirs],
                             hand[:n_hand], globals_vec)
    counts = torch.tensor([[n_mine, n_theirs, n_hand]])
    with torch.no_grad():
      torch_value = model(torch.from_numpy(my_board)[None], torch.from_numpy(their_board)[None],
                          torch.from_numpy(hand)[None], torch.from_numpy(globals_vec)[None],
                          counts).item()
    assert abs(numpy_value - torch_value) < 1e-5, (numpy_value, torch_value)
  print("self-check passed: torch forward == numpy forward")


def train_net(shard_paths, previous_weights, epochs, learning_rate, seed, batch_size=1024):
  import torch
  torch.manual_seed(seed)
  bundles = []
  for path in shard_paths:
    with np.load(path) as data:
      bundles.append({key: data[key] for key in data.files})
  merged = {key: np.concatenate([bundle[key] for bundle in bundles]) for key in bundles[0]}
  n = len(merged["target"])

  tensors = {
    "my_board": torch.from_numpy(merged["my_board"].astype(np.float32)),
    "their_board": torch.from_numpy(merged["their_board"].astype(np.float32)),
    "hand": torch.from_numpy(merged["hand"].astype(np.float32)),
    "globals": torch.from_numpy(merged["globals"].astype(np.float32)),
    "counts": torch.from_numpy(merged["counts"].astype(np.int64)),
    "target": torch.from_numpy(merged["target"]),
  }
  permutation = torch.randperm(n)
  n_val = max(1, int(n * 0.05))
  val_idx, train_idx = permutation[:n_val], permutation[n_val:]

  model = build_torch_model()
  if previous_weights is not None:
    import_from_numpy(model, previous_weights)
  optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
  loss_fn = torch.nn.MSELoss()

  def batch(indices):
    return (tensors["my_board"][indices], tensors["their_board"][indices],
            tensors["hand"][indices], tensors["globals"][indices], tensors["counts"][indices])

  best_val, best_state, since_best = float("inf"), None, 0
  for epoch in range(epochs):
    model.train()
    shuffled = train_idx[torch.randperm(len(train_idx))]
    total, seen = 0.0, 0
    for start in range(0, len(shuffled), batch_size):
      indices = shuffled[start:start + batch_size]
      optimizer.zero_grad()
      prediction = model(*batch(indices))
      loss = loss_fn(prediction, tensors["target"][indices])
      loss.backward()
      optimizer.step()
      total += loss.item() * len(indices)
      seen += len(indices)
    model.eval()
    with torch.no_grad():
      val_loss = loss_fn(model(*batch(val_idx)), tensors["target"][val_idx]).item()
    print(f"    epoch {epoch + 1}: train_mse={total / seen:.4f} val_mse={val_loss:.4f}", flush=True)
    if val_loss < best_val - 1e-4:
      best_val, since_best = val_loss, 0
      best_state = {key: value.clone() for key, value in model.state_dict().items()}
    else:
      since_best += 1
      if since_best >= 2:
        break
  if best_state is not None:
    model.load_state_dict(best_state)
  return export_to_numpy(model), best_val, n


#----------------------------------------------------------------------------
#dispatch: local joblib or the dwails via dill-over-stdin + scp'd shards

def run_local(payload, cores):
  results = Parallel(n_jobs=cores)(delayed(run_item)(item) for item in payload["items"])
  shard_path = None
  samples = concatenate_samples([r for r in results if isinstance(r, dict)])
  if samples is not None:
    SHARD_DIR.mkdir(parents=True, exist_ok=True)
    shard_path = SHARD_DIR / f"{payload['tag']}.npz"
    np.savez_compressed(shard_path, **samples)
  summaries = [({"games": r["games"], "wins_a": r["wins_a"],
                 "n_samples": int(len(r["samples"]["target"])) if r["samples"] else 0}
                if isinstance(r, dict) else float(r)) for r in results]
  return {"shard": str(shard_path) if shard_path else None, "summaries": summaries}


def run_host(host, payload):
  if not payload["items"]:
    return {"shard": None, "summaries": []}
  print(f"  {host}: {len(payload['items'])} items...", flush=True)
  command = f'cd {REMOTE_DIR} && source ~/.profile && pyenv activate venv && python3 value_net_remote_worker.py'
  ssh = subprocess.Popen(["ssh", host, command], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, stdin=subprocess.PIPE)
  result, err = ssh.communicate(input=dill.dumps(payload, fmode='wb'))
  for line in result.decode(errors="replace").splitlines():
    if line[:3] == ">>>":
      parsed = ast.literal_eval(line[3:])
      if parsed["shard"]:
        SHARD_DIR.mkdir(parents=True, exist_ok=True)
        local_shard = SHARD_DIR / Path(parsed["shard"]).name
        subprocess.run(["scp", "-q", f"{host}:{parsed['shard']}", str(local_shard)], check=True)
        parsed["shard"] = str(local_shard)
      return parsed
    print(f"  {host}> {line}", flush=True)
  raise RuntimeError(f"{host} never returned a >>> result line:\n{err.decode(errors='replace')[-2000:]}")


def dispatch(items, tag, backend, cores):
  """Returns (flat summaries aligned with items, list of local shard paths)."""
  if backend == "local":
    parsed = run_local({"tag": tag, "cores": cores, "items": items}, cores)
    return parsed["summaries"], [parsed["shard"]] if parsed["shard"] else []
  chunks = [items[i::len(HOSTS)] for i in range(len(HOSTS))]
  payloads = [{"tag": f"{tag}_{host}", "cores": -1, "items": chunk}
              for chunk, host in zip(chunks, HOSTS)]
  host_results = Parallel(n_jobs=len(HOSTS), backend="threading")(
    delayed(run_host)(host, payload) for host, payload in zip(HOSTS, payloads))
  summaries = [None] * len(items)
  shards = []
  for host_index, parsed in enumerate(host_results):
    for offset, summary in enumerate(parsed["summaries"]):
      summaries[host_index + offset * len(HOSTS)] = summary
    if parsed["shard"]:
      shards.append(parsed["shard"])
  return summaries, shards


#----------------------------------------------------------------------------

def load_seeds():
  with SEEDS_PATH.open(encoding="utf-8") as f:
    return json.load(f)


def load_champion_weights():
  with CHAMPION_PATH.open(encoding="utf-8") as f:
    loaded = json.load(f)
  return loaded.get("champion_weights") or loaded["weights"]


def sample_pair(seeds, rng):
  class_a, class_b = rng.choice(CLASSES), rng.choice(CLASSES)
  return (rng.choice(seeds[class_a]), class_a, rng.choice(seeds[class_b]), class_b)


def build_generate_items(seeds, rng, generation, pairs, games_per_pair, sample_rate,
                          epsilon, world, net_weights, champion_weights,
                          anchor_fraction=ANCHOR_FRACTION, selfplay_spec=None):
  """selfplay_spec overrides the ("net", net_weights) spec used for the
  current-agent side once net_weights is set - e.g. ("beam", (net_weights,
  beam_width, depth)) to close the loop with turn-plan search generating the
  training games themselves, instead of the DouZero-style "no search in the
  training loop" default (see module docstring - this is a deliberate,
  opt-in deviation from that design, not the default)."""
  items = []
  for i in range(pairs):
    deck_a, class_a, deck_b, class_b = sample_pair(seeds, rng)
    current_spec = selfplay_spec if selfplay_spec is not None else ("net", net_weights)
    if net_weights is None:
      spec_a = spec_b = ("linear", champion_weights)
    elif rng.random() < anchor_fraction:
      spec_a, spec_b = current_spec, ("linear", champion_weights)
    else:
      spec_a = spec_b = current_spec
    items.append(("generate", deck_a, class_a, deck_b, class_b, spec_a, spec_b,
                  world, games_per_pair, sample_rate, epsilon,
                  generation * 100003 + i))
  return items


def build_ladder_items(ladder_pairs, generation, spec_a, spec_b, world, games):
  return [("ladder", deck_a, class_a, deck_b, class_b, spec_a, spec_b, world, games,
           generation * 900007 + i)
          for i, (deck_a, class_a, deck_b, class_b) in enumerate(ladder_pairs)]


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--backend", choices=["local", "ssh"], default="local")
  parser.add_argument("--cores", type=int, default=4)
  parser.add_argument("--generations", type=int, default=12)
  parser.add_argument("--pairs", type=int, default=300)
  parser.add_argument("--games-per-pair", type=int, default=30)
  parser.add_argument("--sample-rate", type=float, default=0.15)
  parser.add_argument("--epsilon", type=float, default=0.1)
  parser.add_argument("--world", choices=list(WORLDS), default="pre_naxx")
  parser.add_argument("--epochs", type=int, default=10)
  parser.add_argument("--seed", type=int, default=0)
  parser.add_argument("--ladder-pairs", type=int, default=LADDER_PAIRS)
  parser.add_argument("--ladder-games", type=int, default=LADDER_GAMES)
  parser.add_argument("--anchor-fraction", type=float, default=ANCHOR_FRACTION,
                       help="fraction of self-play games vs the linear champion (drift anchor)")
  parser.add_argument("--init-net", default=None,
                       help="warm-start .npz net: skips the linear bootstrap generation and "
                            "generates gen-0 data with this net")
  parser.add_argument("--gate", action="store_true",
                       help="promotion gate: only adopt a new net for data generation if its "
                            "champion-ladder score doesn't regress below the best seen so far")
  parser.add_argument("--init-best", type=float, default=None,
                       help="known champion-ladder score of --init-net: seeds the gate baseline "
                            "and best-checkpoint tracking (without it, gen 0 can silently adopt "
                            "a net weaker than the warm start)")
  parser.add_argument("--learning-rate", type=float, default=None,
                       help="override the warm-start learning rate (default 3e-4; 1e-3 cold)")
  parser.add_argument("--seeds", default=None,
                       help="seed-decklist json override (default: pre-Naxx seeds)")
  parser.add_argument("--out-dir", default=None,
                       help="output directory override (default: data/value_net)")
  parser.add_argument("--selfplay-agent", choices=["net", "beam"], default="net",
                       help="agent that generates self-play games once net_weights is set. "
                            "'beam' closes the loop with turn-plan search generating the "
                            "training games themselves - a deliberate deviation from the "
                            "DouZero 'no search in the training loop' default, to test "
                            "whether beam-search self-play data trains a stronger net than "
                            "greedy self-play data did (which plateaued - see README S4).")
  parser.add_argument("--selfplay-beam-width", type=int, default=3)
  parser.add_argument("--selfplay-depth", type=int, default=3)
  parser.add_argument("--selfcheck", action="store_true")
  args = parser.parse_args()

  if args.selfcheck:
    self_check()
    return

  global OUT_DIR, SHARD_DIR, SEEDS_PATH
  if args.out_dir:
    OUT_DIR = Path(args.out_dir)
    SHARD_DIR = OUT_DIR / "shards"
  if args.seeds:
    SEEDS_PATH = Path(args.seeds)

  rng = Random(args.seed)
  seeds = load_seeds()
  champion_weights = load_champion_weights()
  OUT_DIR.mkdir(parents=True, exist_ok=True)

  #fixed evaluation set: same real-deck matchups every generation
  ladder_pairs = [sample_pair(seeds, Random(args.seed + 777))
                  for _ in range(args.ladder_pairs)]

  net_weights = ne.load_weights(args.init_net) if args.init_net else None
  shard_history = []  #list of lists, one per generation
  history = []
  best_win, best_weights = None, None
  if args.init_best is not None and net_weights is not None:
    best_win, best_weights = args.init_best, net_weights
  log_path = OUT_DIR / "training_log.csv"

  for generation in range(args.generations):
    selfplay_label = "bootstrap linear" if net_weights is None else f"{args.selfplay_agent} self-play"
    print(f"gen {generation}: generating "
          f"{args.pairs * args.games_per_pair} games ({selfplay_label})...", flush=True)
    selfplay_spec = None
    if net_weights is not None and args.selfplay_agent == "beam":
      selfplay_spec = ("beam", (net_weights, args.selfplay_beam_width, args.selfplay_depth))
    items = build_generate_items(seeds, rng, generation, args.pairs, args.games_per_pair,
                                  args.sample_rate, args.epsilon, args.world,
                                  net_weights, champion_weights, args.anchor_fraction,
                                  selfplay_spec=selfplay_spec)
    summaries, shards = dispatch(items, f"gen{generation}", args.backend, args.cores)
    games = sum(s["games"] for s in summaries)
    n_samples = sum(s["n_samples"] for s in summaries)
    shard_history.append(shards)
    window = [path for generation_shards in shard_history[-REPLAY_WINDOW:]
              for path in generation_shards]
    print(f"  {games} games, {n_samples} new samples; training on {len(window)} shards...", flush=True)

    learning_rate = args.learning_rate or (1e-3 if net_weights is None else 3e-4)
    new_weights, val_mse, n_train = train_net(window, net_weights, args.epochs,
                                              learning_rate, args.seed + generation)
    ne.save_weights(new_weights, OUT_DIR / f"net_gen{generation}.npz")

    #fixed-set ladder: new net vs linear champion, and vs previous net
    ladder_vs_champion = build_ladder_items(ladder_pairs, generation,
                                            ("net", new_weights), ("linear", champion_weights),
                                            args.world, args.ladder_games)
    ladder_results, _ = dispatch(ladder_vs_champion, f"ladder{generation}c", args.backend, args.cores)
    win_vs_champion = mean(ladder_results)
    win_vs_previous = None
    if net_weights is not None:
      ladder_vs_previous = build_ladder_items(ladder_pairs, generation + 5000,
                                              ("net", new_weights), ("net", net_weights),
                                              args.world, args.ladder_games)
      ladder_results, _ = dispatch(ladder_vs_previous, f"ladder{generation}p", args.backend, args.cores)
      win_vs_previous = mean(ladder_results)

    print(f"  gen {generation}: val_mse={val_mse:.4f} n_train={n_train} "
          f"win_vs_champion={win_vs_champion:.3f}"
          + (f" win_vs_previous={win_vs_previous:.3f}" if win_vs_previous is not None else ""), flush=True)

    if best_win is None or win_vs_champion > best_win:
      best_win, best_weights = win_vs_champion, new_weights

    #promotion gate: a net that regressed on the external anchor ladder keeps
    #generating data with the incumbent instead - checks self-play drift
    adopted = True
    if args.gate and best_win is not None and win_vs_champion < best_win - 0.02:
      adopted = False
      print(f"  gen {generation}: NOT adopted (win_vs_champion {win_vs_champion:.3f} "
            f"< best {best_win:.3f} - 0.02)", flush=True)

    history.append({"generation": generation, "games": games, "n_samples": n_samples,
                    "n_train": n_train, "val_mse": round(val_mse, 5),
                    "win_vs_champion": round(win_vs_champion, 4),
                    "win_vs_previous": round(win_vs_previous, 4) if win_vs_previous is not None else "",
                    "adopted": adopted})
    with log_path.open("w", newline="", encoding="utf-8") as f:
      writer = csv.DictWriter(f, fieldnames=list(history[0].keys()))
      writer.writeheader()
      writer.writerows(history)

    if adopted:
      net_weights = new_weights

  #the champion is the BEST net by external ladder, not the last one - the
  #adopt-always default can end on a self-play-drift downswing
  ne.save_weights(best_weights, OUT_DIR / "value_net_champion.npz")
  print(f"\nbest win_vs_champion={best_win:.3f}; "
        f"wrote {OUT_DIR / 'value_net_champion.npz'} and {log_path}")


if __name__ == "__main__":
  main()
