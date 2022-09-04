from enum import Enum


class Attributes(Enum):
  TAUNT = 0
  LIFESTEAL = 1
  DIVINE_SHIELD = 2
  CHARGE = 3
  STEALTH = 4
  WINDFURY = 5
  HEXPROOF = 6


class Triggers(Enum):
  BATTLECRY = 0
  DEATHRATTLE = 1
  AURA = 2 #an aura is permentant until the source disapears


class Events(Enum):
  WEAPON_PLAYED = 3
  WEAPON_DESTROYED = 4
  MINION_DIES = 5
  SPELL_CAST = 6
  CHARACTER_HEALED = 7
  MURLOC_SUMMONED = 8


class Actions(Enum):
  ATTACK = 0
  CAST_MINION = 1
  CAST_HERO_POWER = 2
  CAST_SPELL = 3
  CAST_WEAPON = 4
  END_TURN = 5
  CAST_EFFECT = 6


class Targets(Enum):
  MINIONS = 0
  HEROES = 1
  MINIONS_OR_HEROES = 2
  WEAPONS = 3

class OwnerFilters(Enum):
  FRIENDLY = 0
  ENEMY = 1
  ALL = 2
  

class CreatureTypes(Enum):
  ALL = 0
  PIRATES = 1
  BEASTS = 2
  ELEMENTALS = 3
  TOTEMS = 4

class Durations(Enum):
  TURN = 0
  PERMANENTLY = 1


class Methods(Enum):
  TARGETED = 0
  RANDOMLY = 1
  ALL = 2
  ADJACENT = 3


class CardSets(Enum):
  CLASSIC_HUNTER = 0
  CLASSIC_NEUTRAL = 1
  OP_CARDS = 2
  TEST_CARDS = 3
  RANDOM_CARDS = 4
  CLASSIC_MAGE = 5

class Classes(Enum):
  HUNTER = 0
  MAGE = 1


class CardTypes(Enum):
  MINION = 0
  SPELL = 1
  WEAPON = 2
  HERO_POWER = 3


class ParamTypes(Enum):
  KEYWORD = 0
  CREATURE_TYPE = 1
  X = 2
  XY = 3
  NONE = 4
