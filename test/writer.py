import time
from random import randint, seed
from validator.validator import DataSender
import sys

ds = DataSender("Jošt Smrtnik", "Najboljši vzorec", 500)
n = 5400
t = time.time()
for i in range(n):
    ds.write_frame([(i % 256, i % 256, i % 256)] * 500)
    if i % 100 == 0:
        print(f"Printed {i}-th frame at time {time.time() - t}", randint(0, 100))
sys.stderr.write(f"time {time.time() - t}")
