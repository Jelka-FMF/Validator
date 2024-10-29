import sys
import json


def to_duration(minutes=0, seconds=0, fps=30) -> int:
    return (minutes * 60 + seconds) * fps


def encode_header(author: str, title: str, school: str, led_count: int, duration: int, fps: int) -> str:
    """author and title can be any alpha-numeric utf-8 string and can also include spaces.
    led_count must be an integer. duration is number of frames.
    """

    if not isinstance(led_count, int):
        raise TypeError(f"led_count must be int, found {type(led_count)}.")
    if not isinstance(duration, int):
        raise TypeError(f"duration must be int, found {type(duration)}.")
    if not isinstance(fps, int):
        raise TypeError(f"fps must be int, found {type(fps)}.")

    # Change version if structure of data changes
    version = 0  # 0 for testing  # TODO: increase this
    return json.dumps(
        {
            "version": version,
            "led_count": led_count,
            "duration": duration,
            "fps": fps,
            "author": str(author),
            "title": str(title),
            "school": str(school),
        },
        indent=None,
    )


def decode_header(header: str) -> dict:
    json_header = json.loads(header)
    if "version" not in json_header:
        raise ValueError("Header must contain a version.")

    if json_header["version"] == 0:
        if not all(key in json_header for key in ("led_count", "duration", "fps", "author", "title", "school")):
            raise ValueError(
                "Header (version 0) must contain led_count, duration, fps, author, title and school.")

    return json_header


def encode_frame(frame: list, led_count: int) -> str:
    if len(frame) != led_count:
        raise ValueError(
            f"frame must have a value for every led, has {len(frame)}/{led_count}.")
    if not all(len(rgb) == 3 and (isinstance(v, int) for v in rgb) for rgb in frame):
        raise ValueError("frame must have an rbg tuple of ints for values.")

    return "".join(hex(v)[2:].zfill(2) for rgb in frame for v in rgb)


def decode_frame(frame: str, led_count: int, version: int) -> list:
    assert version == 0
    if not isinstance(frame, str):
        raise TypeError(f"Expected type 'str', found type {type(frame)}.")

    expected_length = 3 * led_count * 2  # 3 * 2 characters per led
    if len(frame) != expected_length:
        raise ValueError(
            f"Frame is too short, expected exactly {expected_length} bytes, found {len(frame)}.")

    return [
        (
            int(frame[i:i + 2], 16),
            int(frame[i + 2:i + 4], 16),
            int(frame[i + 4:i + 6], 16)
        )
        for i in range(0, len(frame), 6)
    ]


class DataSender:
    def __init__(
        self,
        author: str,
        title: str,
        shcool: str,
        led_count: int = 300,  # TODO: change led_count
        fps: int = 60,
        duration: int = to_duration(minutes=3),
    ) -> None:
        self.author = author
        self.title = title
        self.school = shcool
        self.fps = fps
        self.led_count = led_count
        self.header = encode_header(
            self.author, self.title, self.school, led_count, duration, fps)
        self.printed_header = False
        self.duration = duration
        self.frame_count = 0

    def write_frame(self, frame: list):
        if self.frame_count >= self.duration:
            raise ValueError(
                f"Frame count exceeds duration of {self.duration}.")
        self.frame_count += 1
        if not self.printed_header:
            sys.stdout.buffer.write(("#" + self.header + "\n").encode("utf-8"))
            sys.stdout.flush()
            self.printed_header = True
        sys.stdout.buffer.write(("#" + encode_frame(frame, self.led_count) + "\n").encode("utf-8"))
        sys.stdout.flush()


class DataReceiver:
    def __init__(self, input_file=None) -> None:
        self.header = None
        self.header_end = None
        if input_file is None:
            self.input_file = sys.stdin
        else:
            self.input_file = input_file

        # Header values
        self.version = None
        self.duration = None
        self.led_count = None
        self.fps = None

        # Frame values
        self.frames = []
        self.frame_count = 0  # the last frame that should be read
        # actual frame data (latest avaiable that should already be read)
        self.current_frame = None

        # new input
        self.mode = "user"  # or "jelka" if in the middle of jelka data
        self.jelka_buffer = b""  # jelka data
        self.user_buffer = b""  # not jelka data

    def read(self):
        self.update_buffer()
        if not self.header:
            self.try_read_header()
        self.try_read_frame()

    def update_buffer(self):
        user_add = []
        jelka_add = []
        for byte in self.input_file.read1():
            if self.mode == "user" and byte == ord("#"):
                self.mode = "jelka"

            if self.mode == "jelka":
                jelka_add.append(byte.to_bytes(length=1))
            elif self.mode == "user":
                user_add.append(byte.to_bytes(length=1))

            if self.mode == "jelka" and byte in b"\x0a\x0d":
                self.mode = "user"

        self.user_buffer += b"".join(user_add)
        self.jelka_buffer += b"".join(jelka_add)

    def user_print(self, flush=True):
        print("User output:", self.user_buffer.decode(encoding="utf-8"), end="", flush=flush)
        self.user_buffer = b""

    def try_read_header(self):
        header_end = self.jelka_buffer.find(b"\x0a")
        if header_end == -1:
            header_end = self.jelka_buffer.find(b"\x0d")
        if header_end != -1:
            text = self.jelka_buffer[0: header_end + 1].decode(encoding="utf-8")
            text = text.removeprefix("#")
            text = text.strip()
            self.header = decode_header(text)
            self.version = self.header["version"]
            self.duration = self.header["duration"]
            self.led_count = self.header["led_count"]
            self.fps = self.header["fps"]
            self.jelka_buffer = self.jelka_buffer[header_end + 1:]

    def try_read_frame(self):
        frame_end = self.jelka_buffer.find(b"\x0a")
        if frame_end == -1:
            frame_end = self.jelka_buffer.find(b"\x0d")
        frame_start = 0
        while frame_end != -1:
            text = self.jelka_buffer[frame_start: frame_end + 1].decode(encoding="utf-8")
            text = text.removeprefix("#")
            text = text.strip()
            frame = decode_frame(text, self.led_count, self.version)
            self.frames.append(frame)
            frame_start = frame_end + 1
            frame_end = self.jelka_buffer.find(b"\x0a", frame_start + 1)
            if frame_end == -1:
                frame_end = self.jelka_buffer.find(b"\x0d", frame_start + 1)
        self.jelka_buffer = self.jelka_buffer[frame_start + 1:]

    def __iter__(self):
        return self

    def __next__(self):
        self.read()
        self.frame_count += 1
        if self.duration and self.frame_count > self.duration:
            raise StopIteration

        if self.frames:
            return self.frames[min(self.frame_count - 1, len(self.frames) - 1)]

        return [(0, 0, 0)] * (self.led_count or 0)
