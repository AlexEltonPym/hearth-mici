import json

def print_elites(title, elites):
  print(f"\n--- {title} ---")
  print("x,y => fitness")
  [print(f"{x},{y} => {fitness:.2f}") for (x, y, fitness, sample) in elites]

def load_population(filename):
  population = []
  with open(filename, "r", encoding="utf-8") as f:
    archive_json = json.load(f)
    for entry in archive_json:
      population.append((entry['x'], entry['y'], entry['fitness'], entry['sample']))

    return [elite for elite in population if elite[2] != None]

population = load_population("data/map_archive.json")

for elite in population:
  print(elite[3])

top_tenth = sorted(population, key=lambda key: key[2], reverse=True)[:len(population)//10]
# print_elites("Top tenth", top_tenth)

by_hand_size = sorted(top_tenth, key=lambda key: (key[0], key[2]), reverse=True)
# print_elites("By hand size", by_hand_size)

by_turns_taken = sorted(top_tenth, key=lambda key: (key[1], key[2]), reverse=True)
# print_elites("By turns taken", by_turns_taken)

most_fit = top_tenth[0]
by_hand_size.remove(most_fit)
by_turns_taken.remove(most_fit)
biggest_hand = by_hand_size[0]
by_hand_size.remove(biggest_hand)
by_turns_taken.remove(biggest_hand)
smallest_hand = by_hand_size[-1]
by_hand_size.remove(smallest_hand)
by_turns_taken.remove(smallest_hand)
most_turns = by_turns_taken[0]
by_hand_size.remove(most_turns)
by_turns_taken.remove(most_turns)
least_turns = by_turns_taken[-1]

# print(f"{most_fit=}")
# print(f"{biggest_hand=}")
# print(f"{smallest_hand=}")
# print(f"{most_turns=}")
# print(f"{least_turns=}")

gauntlet = [most_fit, biggest_hand, smallest_hand, most_turns, least_turns]
with open("gauntlet.csv", mode="w", encoding="utf-8") as f:
  f.write("x,y,fitness,sample\n")
  for entry in gauntlet:
    f.write(f"{entry[0]},{entry[1]},{entry[2]},{entry[3]}\n")