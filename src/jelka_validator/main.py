import sys


def to_duration(minutes=0, seconds=0, fps=30) -> int:
    return (minutes * 60 + seconds) * fps


def encode_string(string: str, maxlen: int) -> bytes:
    if not isinstance(string, str):
        raise TypeError(f"Expected type 'str', found type {type(string)}.")
    if not isinstance(maxlen, int):
        raise TypeError("maxlen must be int.")

    if len(string) > maxlen:
        raise ValueError(f"String '{string}' is longer than {maxlen} characters.")
    if not string.replace(" ", "").isalnum():
        raise ValueError(
            f"String '{string}' should only contain alpha-numeric characters or spaces. Must include at least one alpha-numeric character."
        )

    return string.encode(encoding="utf-8")


def encode_header(author: str, title: str, led_count: int, duration: int) -> bytes:
    """author and title can be any alpha-numeric utf-8 string and can also include spaces.
    Their length must not exceed 50 characters.
    led_count must be an integer. duration is number of frames.
    """

    if not isinstance(led_count, int):
        raise TypeError(f"led_count must be int, found {type(led_count)}.")
    if not isinstance(duration, int):
        raise TypeError(f"duration must be int, found {type(duration)}.")

    # Change version if structure of data changes
    version = 0  # 0 for testing  # TODO: increase this
    return b"".join(
        (
            b"\x02",  # start of text
            version.to_bytes(length=1, byteorder="big"),  # 1 byte for version
            led_count.to_bytes(length=2, byteorder="big"),  # 2 bytes for led_count
            duration.to_bytes(
                length=2, byteorder="big"
            ),  # 2 bytes for duration (enough for up to 18 minutes at 60 fps)
            encode_string(author, maxlen=50),  # 1 to 50 bytes for author
            b"\x00",  # end of string
            encode_string(title, maxlen=50),  # 1 to 50 bytes for title
            b"\x00",  # end of string
            b"\x03",  # end of text
        )
    )


def decode_header(header: bytes) -> dict:
    if not isinstance(header, bytes):
        raise TypeError(f"Expected type 'bytes', found type {type(header)}.")

    if len(header) < 1:
        raise ValueError(
            f"Header is too short, expected at least 9 bytes, found {len(header)}."
        )

    if header[0] != 0x02 or header[-1] != 0x03:
        print(header)
        raise ValueError("Header must start with 0x02 and end with 0x03.")

    version = header[1]
    assert version == 0, f"Version must be 0, found {version}."  # 0 for testing  # TODO: increase this

    # Integer values
    led_count = int.from_bytes(header[2:4], byteorder="big")  # bytes 2 and 3
    duration = int.from_bytes(header[4:6], byteorder="big")  # bytes 4 and 5

    # Text strings
    author_end = header.find(b"\x00", 6)
    if author_end == -1:
        raise ValueError("Author string must end with 0x00.")
    author = header[6:author_end].decode(encoding="utf-8")
    title_end = header.find(b"\x00", author_end + 1)
    if title_end == -1:
        raise ValueError("Title string must end with 0x00.")
    title = header[author_end + 1 : title_end].decode(encoding="utf-8")

    return {
        "version": version,
        "led_count": led_count,
        "duration": duration,
        "author": author,
        "title": title,
    }


def encode_frame(frame: list, led_count: int) -> bytes:
    if len(frame) != led_count:
        raise ValueError(
            f"frame must have a value for every led, has {len(frame)}/{led_count}."
        )
    if not all(len(rgb) == 3 and (isinstance(v, int) for v in rgb) for rgb in frame):
        raise ValueError("frame must have an rbg tuple of ints for values.")

    data = (
        b"".join(
            v.to_bytes(length=1, byteorder="big")
            for rgb in frame
            for v in rgb  # flatten the list
        )
        .replace(b"\x0a", b"\x0b")
        .replace(b"\x0d", b"\x0c")
        .replace(b"\x0e", b"\x0f")
    )  # speed

    return b"".join(
        (
            b"\x02",  # start of text
            data.replace(b"\x02", b"\x01").replace(
                b"\x03", b"\x04"
            ),  # escape start and end of text
            b"\x03",  # end of text
        )
    )


def decode_frame(frame: bytes, led_count: int, version: int) -> list:
    assert version == 0
    if not isinstance(frame, bytes):
        raise TypeError(f"Expected type 'bytes', found type {type(frame)}.")

    expected_length = 3 * led_count + 2  # 3 bytes per led + start and end of text
    if len(frame) != expected_length:
        raise ValueError(
            f"Frame is too short, expected exactly {expected_length} bytes, found {len(frame)}."
        )

    if frame[0] != 0x02 or frame[-1] != 0x03:
        raise ValueError("Frame must start with 0x02 and end with 0x03.")

    return [
        tuple(frame[led_index + i] for i in range(3))
        for led_index in range(led_count)
    ]  # split into rgb tuples


class DataSender:
    def __init__(
        self,
        author: str,
        title: str,
        led_count: int = 300,
        duration: int = to_duration(minutes=3),
    ) -> None:  # TODO: change led_count
        self.author = author
        self.title = title
        self.led_count = led_count
        self.header = encode_header(self.author, self.title, led_count, duration)
        self.printed_header = False
        self.duration = duration
        self.frame_count = 0

    def write_frame(self, frame: list):
        if self.frame_count >= self.duration:
            raise ValueError(f"Frame count exceeds duration of {self.duration}.")
        self.frame_count += 1
        if not self.printed_header:
            sys.stdout.buffer.write(self.header)
            self.printed_header = True
        sys.stdout.buffer.write(encode_frame(frame, self.led_count))
        sys.stdout.flush()


class DataReceiver:
    def __init__(self, input_file=None) -> None:
        self.header = None
        self.header_end = None
        if input_file is None:
            self.input_file = sys.stdin.buffer
        else:
            self.input_file = input_file

        # Header values
        self.version = None
        self.duration = None
        self.led_count = None
        self.author = None
        self.title = None

        # Frame values
        self.frames = []
        self.frame_count = 0  # the last frame that should be read
        self.current_frame = None  # actual frame data (latest avaiable that should already be read)

        # new input
        self.mode = "user"  # or "jelka" if in the middle of jelka data
        self.jelka_buffer = b""  # jelka data
        self.user_buffer = b""  # not jelka data
        self.data_start = b"\x02"
        self.data_end = b"\x03"
    
    def read(self):
        self.update_buffer()
        if not self.header:
            self.try_read_header()
        self.try_read_frame()
    
    def update_buffer(self):
        user_add = []
        jelka_add = []
        for byte in self.input_file.read1():
            if self.mode == "user" and byte == 2:
                self.mode = "jelka"
            
            if self.mode == "jelka":
                jelka_add.append(byte.to_bytes(length=1))
            elif self.mode == "user":
                user_add.append(byte.to_bytes(length=1))
            
            if self.mode == "jelka" and byte == 3:
                self.mode = "user"
        self.user_buffer += b"".join(user_add)
        self.jelka_buffer += b"".join(jelka_add)

    def user_print(self, flush=True):
        print(self.user_buffer.decode(encoding="utf-8"), end="", flush=flush)
        self.user_buffer = b""
    
    def try_read_header(self):
        header_end = self.jelka_buffer.find(self.data_end)
        if header_end != -1:
            self.header = decode_header(self.jelka_buffer[0:header_end + 1])
            self.version = self.header["version"]
            self.duration = self.header["duration"]
            self.led_count = self.header["led_count"]
            self.author = self.header["author"]
            self.title = self.header["title"]
            self.jelka_buffer = self.jelka_buffer[header_end + 1:]

    def try_read_frame(self):
        frame_end = self.jelka_buffer.find(self.data_end)
        frame_start = 0
        while frame_end != -1:
            frame = decode_frame(self.jelka_buffer[frame_start:frame_end + 1], self.led_count, self.version)
            self.frames.append(frame)
            frame_start = frame_end + 1
            frame_end = self.jelka_buffer.find(self.data_end, frame_start + 1)
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
        
        return [(0, 0, 0)] * self.led_count

