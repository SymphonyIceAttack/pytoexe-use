import time
from random import randint

take = 0
start = time.time()

num = 0

def find_time(target):
    while num != 5:
        num = randint(1, target)
        take += 1

    end = time.time()
    overall = end - start

    print(take, num, 'and it took', overall, 'seconds')

find_time(10000)


