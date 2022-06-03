import json

with open('experiment_cards/new_raw_card.json', 'r') as f:
  new_raw_card = json.load(f)

new_raw_card["isSpell"] = False
new_raw_card["name"] = "Custom Card"
new_raw_card["type"] = "MINION"
new_raw_card["rarity"] = "COMMON"
new_raw_card["description"] = "Custom card"
new_raw_card["collectible"] = True
new_raw_card["set"] = "CUSTOM"
new_raw_card["fileFormatVersion"] = 1

with open('experiment_cards/processed_card.json', 'w') as outfile:
  json.dump(new_raw_card, indent=4, fp=outfile)


