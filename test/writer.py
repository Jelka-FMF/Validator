import time
import sys

sys.path.append("/home/jostsmrt/Documents/Validator")

from src.jelka_validator.datawriter import DataWriter

lc = 500
n = 5400
ds = DataWriter("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=lc, duration=n, fps=60)
t = time.time()
for i in range(n):
    ds.write_frame([(i % 256, i % 256, i % 256)] * lc)
    if i % 100 == 0:
        print(f"Printed {i}-th frame at time {time.time() - t}")
