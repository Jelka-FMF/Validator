import pytest

from src.jelka_validator import DataReader
from src.jelka_validator.utils import encode_header, encode_frame

from random import Random
import json


def random_frame(led_count, seed):
    rnd = Random()
    rnd.seed(seed)
    randint = rnd.randint
    return [(randint(0, 255), randint(0, 255), randint(0, 255)) for _ in range(led_count)]


def header(author, title, school, led_count, duration, fps):
    hd = "#" + encode_header(author, title, school, led_count, duration, fps) + "\n"
    return BytesMaker(led_count, [hd], user=[], jelka=[])


class BytesMaker:
    """Helper class for creating bytes from strings and frames - bad design, don't reuse this code"""

    def __init__(self, led_count, entries=None, user=None, jelka=None):
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
            self.entries.append(other)
            self.user.append(other)

        return self

    def copy(self):
        return BytesMaker(self.led_count, self.entries.copy(), self.user.copy(), self.jelka.copy())

    def as_bytes(self):
        return "".join(self.entries).encode("utf-8")

    def read(self):
        bs = self.as_bytes()
        self.entries.clear()
        return bs


class TestDataReader:
    def test_header(self):
        data = header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=1, duration=1, fps=60)

        dr = DataReader(data.read)
        dr.update()

        assert dr.header == {
            "author": "Jošt Smrtnik",
            "title": "Najboljši vzorec",
            "school": "FMF",
            "led_count": 1,
            "duration": 1,
            "fps": 60,
            "version": 0,
        }

    def test_header_comment(self):
        data = header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=150, duration=1, fps=60) + "This is a random comment"

        dr = DataReader(data.read)
        dr.update()

        assert dr.header == {
            "author": "Jošt Smrtnik",
            "title": "Najboljši vzorec",
            "school": "FMF",
            "led_count": 150,
            "duration": 1,
            "fps": 60,
            "version": 0,
        }

    def test_comment_header(self):
        data = header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=500, duration=5400, fps=60)
        data.entries.insert(0, "This is a random comment\n")

        dr = DataReader(data.read)
        dr.update()

        assert dr.header == {
            "author": "Jošt Smrtnik",
            "title": "Najboljši vzorec",
            "school": "FMF",
            "led_count": 500,
            "duration": 5400,
            "fps": 60,
            "version": 0,
        }

    def test_invalid_header(self):
        data = header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=1, duration=1, fps=60)
        data.entries[0] = "#Invalid header\n"

        dr = DataReader(data.read)
        dr.update_buffer()
        with pytest.raises(ValueError):
            dr.try_read_header()

        assert dr.header is None

    def test_invalid_header_values(self):
        data = header("", "", "", led_count=1, duration=1, fps=60)
        d = {"abc": 1}
        data.entries[0] = f"#{json.dumps(d)}\n"

        dr = DataReader(data.read)
        dr.update_buffer()
        with pytest.raises(ValueError):
            dr.try_read_header()

        assert dr.header is None

    def test_frame(self):
        data = header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=1, duration=1, fps=60) + 0

        dr = DataReader(data.read)
        dr.update()

        assert dr.frames == [data.jelka[0]]

    def test_comments(self, capfd):
        data = (
            header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=1, duration=1, fps=60)
            + "abc"
            + 0
            + "This is a random comment"
            + "nst\n"
            + "hmhm"
        )
        data.entries.insert(0, "This is a random comment before everything")
        data.user.insert(0, "This is a random comment before everything")

        dr = DataReader(data.read)
        dr.update()

        assert dr.frames == [data.jelka[0]]
        assert data.user == ["This is a random comment before everything", "abc", "This is a random comment", "nst\n", "hmhm"]

        dr.user_print()
        out, err = capfd.readouterr()
        assert out == "This is a random comment before everythingabcThis is a random commentnst\nhmhm"
    
    def test_frames(self):
        data = header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=1, duration=4, fps=60) + 0 + 1

        dr = DataReader(data.read)

        for i, frame in enumerate(dr):
            assert frame == data.jelka[i]

            if i == 1:
                # add some more frames
                data + 2 + 3
    
    def test_frames_missing(self):
        data = header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=1, duration=4, fps=60) + 0 + 1

        dr = DataReader(data.read)

        for i, frame in enumerate(dr):
            # missing frames should be the last avaiable frame
            assert frame == data.jelka[min(i, len(data.jelka) - 1)]
        
        assert len(dr.frames) == 2
    
    def test_no_frames(self):
        data = header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=5, duration=4, fps=60)

        dr = DataReader(data.read)

        for frame in dr:
            assert frame == [(0, 0, 0)] * 5
    
    def test_frames_late(self):
        """First frames come after they were required, the last two frames never come."""

        data = header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=5, duration=4, fps=60)

        dr = DataReader(data.read)

        for i, frame in enumerate(dr):
            if i <= 1:
                assert frame == [(0, 0, 0)] * 5
            if i == 1:
                data + 0 + 1
            if i >= 2:
                assert frame == random_frame(5, 1)
    
    def test_invalid_frame(self):
        data = header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=1, duration=4, fps=60)
        data.entries.append("#Invalid frame\n")
        
        dr = DataReader(data.read)

        with pytest.raises(ValueError):
            dr.update()

    def test_all_basic(self):
        led_count = 3
        duration = 4
        data = (
            header("Jošt Smrtnik", "Najboljši vzorec", "FMF", led_count=led_count, duration=duration, fps=60)
            + 0
            + "Random text"
            + 1
            + 2
            + 4
            + "jabfhsb"
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
