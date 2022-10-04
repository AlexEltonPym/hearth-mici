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
Frozen: Clears at end of turn, not missing next attack. This means if you freeze your own minion it will clear at end of turn, regardless of if its attacked or not


## Running the simulator
Create a virtual environment, then install the requirements:

python3 -m pip install -r requirements.txt

For an example of running the simulator, see classic_sim.py


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