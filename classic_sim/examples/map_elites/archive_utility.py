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


with open("gauntlet.csv", mode="w", encoding="utf-8") as f:
  f.write("agent_file,agent_class,niche,x,y,fitness,sample\n")
    
  for (agent_file, agent_class) in [("magev3", "M"), ("hunterv3", "H"), ("warriorv3", "W")]:
    population = load_population(f"archive/{agent_file}/map_archive.json")

    top_tenth = sorted(population, key=lambda key: key[2], reverse=True)[:len(population)//10]
    by_hand_size = sorted(top_tenth, key=lambda key: (key[0], key[2]), reverse=True)
    by_turns_taken = sorted(top_tenth, key=lambda key: (key[1], key[2]), reverse=True)

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


    gauntlet = {"most_fit": most_fit, "biggest_hand": biggest_hand, "smallest_hand": smallest_hand, "most_turns": most_turns, "least_turns": least_turns}
    for name, entry in gauntlet.items():
      f.write(f"{agent_file},{agent_class},{name},{entry[0]},{entry[1]},{entry[2]},{entry[3]}\n")