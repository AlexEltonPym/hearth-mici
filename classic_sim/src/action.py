class Action():
  def __init__(self, action_type, source, targets, triggerer=None):
    self.action_type = action_type
    self.source = source
    self.targets = targets
    self.triggerer = triggerer #the card/player that fired a triggered effect, when there is one
  
  def __str__(self):
    return str((self.action_type, self.source, self.targets))
    
     
  def __repr__(self):
    return str((self.action_type, self.source, self.targets))
    