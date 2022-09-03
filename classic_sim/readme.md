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
Fireblast: can target self
Dire Wolf Alpha: effects all cards, suggest nerf attack and mana
Mad Bomber: damage not split