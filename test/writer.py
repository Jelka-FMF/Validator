import time
from random import randint
import sys
sys.path.append("/home/jostsmrt/Documents/Validator")
print(sys.path, file=sys.stderr)

from src.jelka_validator.main import DataSender

lc = 500
ds = DataSender("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=lc)
n = 5400
t = time.time()
for i in range(n):
    ds.write_frame([(i % 256, i % 256, i % 256)] * lc)
    time.sleep(0.01)
    print(f"Printed {i}-th frame at time {time.time() - t}", randint(0, 100))
sys.stderr.write(f"time {time.time() - t}")
