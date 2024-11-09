from .utils import encode_header, encode_frame, to_duration


class DataWriter:
    """Writes jelka data to stdout. The data is written in the required format.
    Useful for testing and text files."""

    def __init__(
        self,
        author: str,
        title: str,
        shcool: str,
        led_count: int = 500,
        fps: int = 60,
        duration: int = to_duration(minutes=3),
    ) -> None:
        # Header values
        self.author = author
        self.title = title
        self.school = shcool
        self.fps = fps
        self.led_count = led_count
        self.duration = duration

        # Endoded header
        self.header: str = encode_header(
            author=self.author,
            title=self.title,
            school=self.school,
            led_count=self.led_count,
            duration=self.duration,
            fps=self.fps,
        )

        # State
        self.printed_header = False
        self.frame_count = 0

    def write_frame(self, frame: list):
        """Writes a frame to stdout. Raises a ValueError if the frame count exceeds the duration or
        if the frame does not have a valid shape (see encode_frame from utils).

        If the header has not been printed yet, it will be printed before the first frame.
        Prefixes encoded frame and header with a "#".
        """

        if self.frame_count >= self.duration:
            raise ValueError(f"Frame count exceeds duration of {self.duration}.")

        if not self.printed_header:
            print("#" + self.header)
            self.printed_header = True

        print("#" + encode_frame(frame, self.led_count))
        self.frame_count += 1
