class Action():
  def __init__(self, action_type, source, targets):
    self.action_type = action_type
    self.source = source
    self.targets = targets
  
  def __str__(self):
    return str((self.action_type, self.source, self.targets))
    
     
  def __repr__(self):
    return str((self.action_type, self.source, self.targets))
    