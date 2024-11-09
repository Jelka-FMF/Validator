from src.jelka_validator import DataReader
from src.jelka_validator.utils import encode_header, encode_frame

from random import Random


def random_frame(led_count, seed):
    rnd = Random()
    rnd.seed(seed)
    randint = rnd.randint
    return [(randint(0, 255), randint(0, 255), randint(0, 255)) for _ in range(led_count)]


def header(author, title, school, led_count, duration, fps):
    hd = "#" + encode_header(author, title, school, led_count, duration, fps) + "\n"
    return BytesMaker(led_count, [hd], user=[], jelka=[])


class BytesMaker:
    def __init__(self, led_count, entries = None, user = None, jelka = None):
        self.entries = entries or []
        self.user = user or []
        self.jelka = jelka or []
        self.led_count = led_count
    
    def __add__(self, other: str | int):
        """Jelka data"""
        if isinstance(other, int):
            frame = random_frame(self.led_count, other)
            self.jelka.append(frame)
            self.entries.append("#" + encode_frame(frame, self.led_count) + "\n")
        else:
            self.entries.append(other + "\n")
            self.user.append(other)

        return BytesMaker(self.led_count, self.entries, self.user, self.jelka)
    
    def copy(self):
        return BytesMaker(self.led_count, self.entries.copy(), self.user.copy(), self.jelka.copy())
    
    def as_bytes(self):
        return "".join(self.entries).encode("utf-8")
    
    def read(self):
        bs = self.as_bytes()
        self.entries.clear()
        return bs
    

class TestDataReader:
    def test_all_basic(self):
        led_count = 3
        duration = 4
        data = (
            header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=led_count, duration=duration, fps=60)
            + 0 + "Random text" + 1 + 2 + 4 + "jabfhsb"
        )

        dr = DataReader(data.copy().read)

        print("".join(data.entries))

        dr.update_buffer()
        dr.try_read_header()

        assert dr.header == {
            "author": "Jošt Smrtnik",
            "title": "Najboljši vzorec",
            "school": "FMF",
            "led_count": led_count,
            "duration": duration,
            "fps": 60,
            "version": 0,
        }

        dr.try_read_frames()

        assert dr.frames == data.jelka
        
        for framei, frame in enumerate(DataReader(data.copy().read)):
            assert frame == data.jelka[framei]
