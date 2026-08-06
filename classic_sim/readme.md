## Classic sim

# How cards work
Each card has a mana cost. Minions and weapons have attack and health
Cards may have an effect (spells should always have an effect)
Minions and weapons may have a condition which provides buffs if the condition is met
Minions and weapons may have attributes, the evergreen keywords of HS

# How effects work
Each effect has the following properties, some may not be allowed or required:
Method: Whether the effect picks a target, picks a random target, or selects all valid targets
Target: Whether the effect targets minions, heroes, minions or heroes, or weapons 
OwnerFilter: Valid owners for targets, friendly, enemy or all
TypeFitler: Whether a particular creature type is selected
Duration: Should the effect last for just the current turn or be permentant
Trigger: When should the effect occur, or is the effect an aura. Note spells dont need a trigger because they are always on-cast.

# How actions work
To change the game-state, an action must be performed. Each action has a type, source and targets. For each target, the source's effect is applied. Note that game.perform_action is done inplace, if you need a forward-model make sure to deepcopy the game before performing actions.

# Card changes
Not all cards can be implemented directly, so the following cards are implemented slighly differently:
Mind control tech: Has no effect
Tracking: Tutor for a beast instead of draw 3 discard 2
Arcane Missiles: Can overkill a minion
Brawl: Cannot be cast if there are no minions on the board

Legendaries added Aug 2026 with known deviations (see card_sets.py comments for the exact reasoning at each):
Ysera: adds 1 of 4 real Dream Cards (Emerald Drake, Laughing Sister, Dream, Ysera Awakens) at end of turn, not the full 5-card pool. Ysera Awakens deals its 5 damage to Ysera herself too (DealDamage has no per-target exception mechanism, and the real card excludes her specifically). Nightmare (the 5th Dream Card) is omitted outright - a Card has exactly one effect slot, so giving an arbitrary minion a fresh end-of-turn Destroy would silently overwrite whatever ability it already had.
Nozdormu: vanilla stats only. Its real text ("each player only has 15 seconds to take their turn") has no meaning for a non-realtime simulator.
Elite Tauren Chieftain: vanilla stats only. Real ETC starts a hero-power-replacement chain reaction the engine has no mechanism for (hero powers aren't swappable mid-game at all currently).
Millhouse Manastorm: vanilla stats only. Real text ("enemy spells cost (0) this turn") needs a cost change that both (a) evaluates per-card rather than one shared value for the whole target list, and (b) automatically reverts at end of turn - ChangeCost currently does neither (see effects.py).

## Known engine quirks not currently worth fixing
Sequential per-target AOE damage resolution means a minion that dies alongside other minions in the same AOE (e.g. Whirlwind) won't see deaths processed after its own - its death-triggered effects only fire for minions that died earlier in that same resolution loop. Verified this doesn't affect any card currently in the pool (a *surviving* minion tracking multiple simultaneous deaths, e.g. Flesheating Ghoul off two Wisps dying to one Whirlwind, works correctly - it's specifically a *dying* minion's own trigger that can miss later deaths in the batch, and a dead minion's own buff is moot regardless).

Random deck generation (`Deck.generate_random` and friends, used by MAP-Elites/agent-generated decks) has no legendary-uniqueness constraint - a randomly generated deck can contain 2+ copies of the same legendary, unlike a real Hearthstone deck. Decklists supplied via `generate_from_decklist` (used for validation-study decks built from real archives) aren't affected, since they contain exactly what's given.

## Running the simulator
Create a virtual environment, then install the requirements:

python3 -m pip install -r requirements.txt

For an example of running the simulator, see classic_sim.py


## Running the tests
From `classic_sim/tests`, with `PYTHONPATH=../src`:

    PYTHONPATH=../src python -m pytest card_tests.py dynamics_tests.py agent_tests.py

This runs the **fast tier** only (unit-style card/mechanic tests, a few hundred
of them, a few seconds total) - `pytest.ini` marks anything that plays out
real games (MCTS search, multi-game `simulate()` calls) as `slow` and excludes
it by default, so editing a card doesn't mean waiting minutes for a full MCTS
ladder to re-run. Run the slow tier explicitly when you want it:

    PYTHONPATH=../src python -m pytest agent_tests.py -m slow

or drop `-m slow`'s default exclusion for everything:

    PYTHONPATH=../src python -m pytest card_tests.py dynamics_tests.py agent_tests.py -m slow

New tests that spin up `GameManager.simulate(...)` with many games, or run
`MCTS`, should get `@pytest.mark.slow` (see `agent_tests.py` for examples).

## Profiling the code:
First you will need to install kernprof/line_profiler https://github.com/rkern/line_profiler:

You may be able to install it with pip:
python3 -m pip install line_profiler

To profile a part of the program do the following:

1. Put a @profile decorator before the function to profile.
2. Run the following:
kernprof -l script_to_profile.py
3. Interpret the created lprof file with:
python3 -m line_profiler script_to_profile.py.lprof



#todo:

seperate cast and summon
secrets on enemy turn only?
frozen skips next attack, does not unfreeze on end turn necessarily
check dead on swap, set and change stats
silence should unswap stats that have been swapped
do some auras need to effect themselves?
dynamic change stats to replace gain weapon attack
dynamic set stats to replace swap stats
spell damage from weapon and player?
use all instead of targeted to prevent stealth/hexproof issues
test self targeting secrets?
expand dynamics
mind control tech