from .utils import encode_header, to_duration
import json


if __name__ == "__main__":
    print("This module helps you write headers so you can copy paste it into your program."
          "There are 500 LEDs, 60 fps and default duration of 3 minutes (10800 frames).\n"
          "If some characters are changed to something like \\u010d or some \\ are added it is correct.")
    author = input("Author: ")
    title = input("Title: ")
    school = input("School: ")
    header = encode_header(author, title, school, led_count=500, duration=to_duration(minutes=3), fps=60)
    print("Your encoded header is:")
    print(json.dumps("#" + header + "\n"))
