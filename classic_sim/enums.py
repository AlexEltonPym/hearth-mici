from enum import Enum


class Attributes(Enum):
  TAUNT = 0
  LIFESTEAL = 1
  DIVINE_SHIELD = 2


class Triggers(Enum):
  BATTLECRY = 0
  DEATHRATTLE = 1
  CAST = 2


class Actions(Enum):
  ATTACK = 0
  CAST_MINION = 1
  CAST_HERO_POWER = 2
  CAST_SPELL = 3
  END_TURN = 4
  CAST_EFFECT = 5


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
  SELF = 3


class CardSets(Enum):
  CLASSIC_HUNTER = 0
  CLASSIC_NEUTRAL = 1
  OP_CARDS = 2


class Classes(Enum):
  HUNTER = 0


class CardTypes(Enum):
  MINION = 0
  SPELL = 1
  WEAPON = 2
  HERO_POWER = 3


class ParamTypes(Enum):
  Keyword = 0
  CreatureType = 1
  X = 2
  XY = 3
