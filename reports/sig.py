import random
import math
import statistics as stats
from scipy.stats import binomtest, ttest_1samp


random.seed(0)

population = [random.normalvariate(47.08411214953271, 11.335082644723329) for _ in range(1000)]

print(stats.mean(population))
print(stats.stdev(population))

sample = 45.23560209

single_sample_result = (ttest_1samp(population, sample))
print(f'{single_sample_result.pvalue:.20f}')

binomial_result = binomtest(int(0.356*1000), 1000, p=0.4984423676012461, alternative='two-sided')
print(f'{binomial_result.pvalue:.20f}')
