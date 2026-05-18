import random
import time
import os

programs=[
    'cmd.exe'
    ]
print("hj")
try:
    while True:
        time.sleep(3)
        random_program=random.choice(programs)

        os.system(f'start {random_program}')
except KeyboardInterrupt:
    print('hjyhhh')
