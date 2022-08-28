from enum import Enum


class Attributes(Enum):
  TAUNT = 0
  LIFESTEAL = 1


class Triggers(Enum):
  BATTLECRY = 0
  DEATHRATTLE = 1


class Actions(Enum):
  ATTACK = 0
  CAST_MINION = 1
  CAST_HERO_POWER = 2
  CAST_SPELL = 3
  END_TURN = 4


class Targets(Enum):
  MINIONS = 0
  HEROES = 1
  MINIONS_OR_HEROES = 2
  PIRATES = 3
  BEASTS = 4
  ELEMENTALS = 5
  TOTEMS = 6
  WEAPONS = 7


class Filters(Enum):
  FRIENDLY = 0
  ENEMY = 1
  ALL = 2



class Durations(Enum):
  TURN = 0
  PERMANENTLY = 1


class Methods(Enum):
  TARGETED = 0
  RANDOMLY = 1
  ALL = 2
  NONE = 3


class CardSets(Enum):
  CLASSIC_HUNTER = 0
  CLASSIC_NEUTRAL = 1
  OP_CARDS = 2


class Classes(Enum):
  HUNTER = 0


class CardType(Enum):
  MINION = 0
  SPELL = 1
  WEAPON = 2
  HERO_POWER = 3

class EffectType(Enum):
  GAIN_MANA = 0
  DEAL_DAMAGE = 1
  CHANGE_STATS = 2
