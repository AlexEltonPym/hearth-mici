class Card():
    def __init__(self, id, name, card_details):
        self.id = id
        self.name = name
        self.card_details = card_details
        if('attributes' not in self.card_details):
            self.card_details['attributes'] = []
        self.owner = None
        self.has_attacked = True
        self.parent = None

    def get_string(self):
        if(self.card_details['card_type'] == 'minion'):
            return str((self.name, self.card_details['mana'], str(self.card_details['attack'])+"/"+str(self.card_details['health'])))
        else:
            return str((self.name, self.card_details['mana']))

    def __str__(self):
        return self.get_string()

    def __repr__(self):
        return self.get_string()

    def __eq__(self, other):
        return self.name == other.name and self.card_details == other.card_details
