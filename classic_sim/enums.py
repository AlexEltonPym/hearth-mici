from enum import Enum

class Attributes(Enum):
  TAUNT = 0
  LIFESTEAL = 1
  DIVINE_SHIELD = 2
  CHARGE = 3
  STEALTH = 4
  WINDFURY = 5
  HEXPROOF = 6
  FROZEN = 7


class Triggers(Enum):
  BATTLECRY = 0
  DEATHRATTLE = 1
  AURA = 2 #an aura is permentant until the source disapears
  ANY_MINION_DIES = 3
  FRIENDLY_MINION_DIES = 4
  ENEMY_MINION_DIES = 5
  CAST = 6
  ANY_HEALED = 7
  FRIENDLY_HEALED = 8
  ENEMY_HEALED = 9
  MINION_SUMMONED = 10
  TYPE_SUMMONED = 11
  FRIENDLY_MINION_SUMMONED = 12
  FRIENDLY_TYPE_SUMMONED = 13
  ENEMY_MINION_SUMMONED = 14
  ENEMY_TYPE_SUMMONED = 15
  SECRET_CAST = 16
  FRIENDLY_END_TURN = 17
  ENEMY_END_TURN = 18
  ANY_END_TURN = 19


class Actions(Enum):
  ATTACK = 0
  CAST_MINION = 1
  CAST_HERO_POWER = 2
  CAST_SPELL = 3
  CAST_WEAPON = 4
  END_TURN = 5
  CAST_EFFECT = 6
  CAST_SECRET = 7



class Targets(Enum):
  MINION = 0
  HERO = 1
  MINION_OR_HERO = 2
  WEAPON = 3
  SPELL = 4
  MINION_OR_SPELL = 5
  
class OwnerFilters(Enum):
  FRIENDLY = 0
  ENEMY = 1
  ALL = 2
  

class CreatureTypes(Enum):
  ALL = 0
  PIRATE = 1
  BEAST = 2
  ELEMENTAL = 3
  TOTEM = 4
  MECH = 5
  MURLOC = 6

class Durations(Enum):
  TURN = 0
  PERMANENTLY = 1


class Methods(Enum):
  TARGETED = 0
  RANDOMLY = 1
  ALL = 2
  ADJACENT = 3
  SELF = 4
  TRIGGERER = 5


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
  SECRET = 4


class ParamTypes(Enum):
  KEYWORD = 0
  CREATURE_TYPE = 1
  X = 2
  XY = 3
  NONE = 4
  TOKEN = 5
  DYNAMIC = 6
