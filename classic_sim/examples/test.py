
def get_sublist(lst, num_cores, core_num):
  start_index = core_num * (len(lst) // num_cores) + min(core_num, (len(lst) % num_cores))
  end_index = start_index + (len(lst) // num_cores) + (1 if core_num < (len(lst) % num_cores) else 0)
  return lst[start_index:end_index]


print(get_sublist([0], 10, 1))