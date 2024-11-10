from test.simulator import Simulation

from subprocess import Popen, PIPE
import sys
import time
from src.jelka_validator.datareader import DataReader


if __name__ == "__main__":
    # Popen(["-m", "writer.py"], executable=sys.executable, stdout=PIPE)
    # Popen(["writer.exe"], stdout=PIPE)
    with Popen(["-m", "test/writer.py"], executable=sys.executable, stdout=PIPE, bufsize=500) as p:
        sim = Simulation()
        dr = DataReader(p.stdout.read1)
        dr.update()
        # assert dr.header is not None
        sim.init()
        time.sleep(1)
        while sim.running:
            c = next(dr)
            assert all(c[i] == c[0] for i in range(len(c)))
            dr.user_print()
            sim.set_colors(dict(zip(range(len(c)), c)))
            sim.frame()
        sim.quit()