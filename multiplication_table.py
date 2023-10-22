#!/usr/bin/env python3

"""Small program for children to practice their multiplication tables
"""

from collections import OrderedDict
from math import ceil
from os import system
from pprint import pprint
from random import choice
from statistics import mean
from time import time

RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[m'

stats = OrderedDict()
system("clear")
while True:
    r = range(2,10)
    x, y = choice(r), choice(r)

    eq = f"{x}*{y}"
    res = x * y

    start_time = time()
    ans = input(f"{eq} = ")
    end_time = time()

    if ans == "x":
        break

    timer = end_time - start_time
    correct = int(res) == int(ans)

    system("clear")
    color = GREEN if correct else RED
    print(color + f"{eq} = {res}" + RESET + "\n")

    # add time to solve to equation in stats dict
    stats[eq] = stats.setdefault(eq, [])
    stats[eq].append(timer)

# print the top 5 that that took the longest to solve (mean average)
for k,v in stats.items():
    stats[k] = mean(v)
stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)

system("clear")
print("TOP 5 SLOWEST ANSWERS\n")
print("EQ\tTIME")
for k, v in stats[:4]:
    print(k, f"\t{v:.2f}s")  # only 2 decimal points
