import json

with open('newRawCard.json', 'r') as f:
  newRawCard = json.load(f)

newRawCard["isSpell"] = False
newRawCard["name"] = "Custom Card"
newRawCard["type"] = "MINION"
newRawCard["rarity"] = "COMMON"
newRawCard["description"] = "Custom card"
newRawCard["collectible"] = True
newRawCard["set"] = "CUSTOM"
newRawCard["fileFormatVersion"] = 1

with open('processedCard.json', 'w') as outfile:
  json.dump(newRawCard, indent=4, fp=outfile)


