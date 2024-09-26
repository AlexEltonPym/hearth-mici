import re
def get_average_fitness():
  with open('warriorv3/results.out', 'r', encoding='utf-8') as f:
    text = f.readlines()
    pattern = r"Average fitness"
    matched_lines = [line for line in text if re.match(pattern, line)]

    for line in matched_lines:
      print(line[:-1].split("s ")[1])

def get_most_fit():
  with open('warriorv3/results.out', 'r', encoding='utf-8') as f:
    text = f.readlines()
    pattern = r"Most fit:"
    matched_lines = [line for line in text if re.match(pattern, line)]
    for line in matched_lines:
      print(line.split("fitness': ")[1].split(", ")[0])

# get_most_fit()
get_average_fitness()