import random
import math

import statistics as stats
from scipy.stats import binomtest, ttest_1samp, ttest_ind_from_stats
import json
import pprint

nearly_sig = 0.1
global_sig = 0.05
really_sig = 0.001
max_sig = 0.1
user = "liam"

outjson = {}

with open('database.json', 'r') as db:
    data = json.load(db)

    for key in list(filter(lambda x: 'user' in data[x] and \
                                  data[x]['user'] == user, data)):

        player = data[key]['player'].split("_2")[0]
        enemy = data[key]['enemy']
        card_id = data[key]['card_id']

        if player == enemy:
            enemy += "_MIRROR"


        baseline = data[f"{player}_v_{enemy}"]['stats'][0]
        sample = data[key]['stats'][0]
        outjson[f"{user}_{card_id}_{player}_v_{enemy}"] = {}

        for base, sample in zip(baseline, sample):
            base_mean = base[1][0]
            base_std = base[1][1]
            sample_mean = sample[1][0]
            sample_std = sample[1][1]

            if(base[0] == 'WIN_RATE'):
                p = binomtest(int(sample_mean*1000), 1000, p=base_mean, alternative='two-sided').pvalue
            else:
                p = ttest_ind_from_stats(base_mean, base_std, 1000, sample_mean, sample_std, 1000, equal_var=False, alternative='two-sided').pvalue
            
            if(sample_mean != 0 and p < max_sig):
                outjson[f"{user}_{card_id}_{player}_v_{enemy}"][base[0]] = [base[0],player,enemy,base_mean, sample_mean,p]

with open("../hearth-mici/src/code/report.json", "w") as report_json:
    json.dump(outjson, report_json)