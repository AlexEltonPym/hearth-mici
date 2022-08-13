class Card():
    def __init__(self, id, name, card_details):
        self.id = id
        self.name = name
        self.card_details = card_details
        self.owner = None
        self.has_attacked = True
        self.parent = None


    def __str__(self):
        return str((self.name, self.card_details['attack'], self.card_details['health']))

    def __repr__(self):
        return str((self.name, self.card_details['attack'], self.card_details['health']))
