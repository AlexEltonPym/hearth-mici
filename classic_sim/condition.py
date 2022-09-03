class Condition():
  def __init__(self, requirement, result):
    self.requirement = requirement
    self.result = result
    if not 'attributes' in result:
      self.result['attributes'] = []
    if not 'temp_attack' in result:
      self.result['temp_attack'] = 0
    if not 'temp_health' in result:
      self.result['temp_health'] = 0
  
  def __srt__(self):
    return str((self.requirement, self.result))

  @staticmethod
  def get_available_conditions():
    return [Condition.has_weapon, Condition.damaged]
  
  @staticmethod
  def has_weapon(game, card):
    return game.current_player.weapon

  @staticmethod
  def damaged(game, card):
    return card.health < card.max_health
