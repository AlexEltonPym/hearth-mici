import random
import math
import statistics as stats
from scipy.stats import binomtest, ttest_1samp, ttest_ind_from_stats


random.seed(0)

population = [random.normalvariate(47.08411214953271, 11.335082644723329) for _ in range(1000)]
sample = [random.normalvariate(51.08411214953271, 10.335082644723329) for _ in range(1000)]

mean_pop = stats.mean(population)
std_pop = stats.stdev(population)
mean_sample = stats.mean(sample)
std_sample = stats.stdev(sample)

print(stats.mean(population))
print(stats.stdev(population))


single_sample_result = (ttest_1samp(population, mean_sample))
print(f'{single_sample_result.pvalue:.20f}')

from_stats_result = ttest_ind_from_stats(mean_pop, std_pop, 1000, mean_sample, std_sample, 1000, equal_var=False, alternative='two-sided')
print(f'{from_stats_result.pvalue:.20f}')

binomial_result = binomtest(int(mean_sample*1000), 1000, p=mean_pop, alternative='two-sided')
print(f'{binomial_result.pvalue:.20f}')
