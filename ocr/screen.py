import pytesseract
from PIL import ImageGrab, ImageChops
from typing import NamedTuple, List
from .color import *
from datetime import datetime as dt
from pathlib import Path
from .utils import sanitize_image


pytess_config = "--psm 3"


class Pixel(NamedTuple):
    x: int
    y: int


class Bounds(NamedTuple):
    start: Pixel
    end: Pixel


class Section(object):
    def __init__(self, bounds: Bounds, debug=False):
        self.bounds = bounds
        self.start = self.bounds.start
        self.end = self.bounds.end
        self.width = self.end.x - self.start.x
        self.height = self.end.y - self.start.y
        self.center = Pixel(int(self.width / 2), int(self.height / 2))
        self.image = None

    def grab_image(self):
        image = ImageGrab.grab(bbox=[*self.start, *self.end])
        return image

    def get_text(self, to_lower=False, use_inverted=True, config=None) -> str:
        if config is None:
            config = pytess_config
        self.image = self.grab_image()
        processed = sanitize_image(self.image)
        if use_inverted:
            final_image = ImageChops.invert(processed)
        else:
            final_image = processed
        text = pytesseract.image_to_string(final_image, config=pytess_config).strip()
        if to_lower:
            text = text.lower()
        return text

    def save_debug_image(self):
        print("Saving debug image...")
        if self.image is None:
            self.image = self.grab_image()
        save_suffix = f"{dt.now().strftime('%Y-%m-%d-%H_%M_%S')}.png"
        debug_save_dir = Path(
            r"C:\Users\TheBoss\Documents\Development\Github.com\RickyGrassmuck\DKO-Leaderboard-Query\debug"
        )
        if not debug_save_dir.exists():
            debug_save_dir.mkdir(parents=True)
        ImageChops.invert(self.image).save(
            debug_save_dir.joinpath(f"inverted-{save_suffix}")
        )
        self.image.save(debug_save_dir.joinpath(f"original-{save_suffix}"))

    def get_coordinate_color(self, coordinate: Pixel):
        """Given a PIL Image, return the RGB color of the specified pixel"""
        image = self.grab_image()
        r, g, b = image.getpixel(coordinate)
        color = Color(r, g, b)
        return color


class Checkpoint(Section):
    def __init__(
        self, coordinates: List[int], color: Color, threshold: int = 6, name=None
    ):
        Section.__init__(
            self,
            Bounds(
                Pixel(coordinates[0], coordinates[1]),
                Pixel(coordinates[2], coordinates[3]),
            ),
        )
        self.color = color
        self.threshold = threshold
        self.name = name

    def test(self) -> bool | None:
        pixel_color = self.get_coordinate_color(self.center)
        return color_delta(self.color, pixel_color) < self.threshold


def new_section(coordinates: List[int], debug=False):
    start = Pixel(coordinates[0], coordinates[1])
    end = Pixel(coordinates[2], coordinates[3])
    return Section(Bounds(start, end))


CHECKPOINTS = {
    "home_screen": [
        Checkpoint([2197, 89, 2203, 95], Color(10, 113, 155)),
        Checkpoint([180, 85, 190, 95], Color(255, 255, 255)),
        Checkpoint([2132, 1112, 2135, 1115], Color(16, 135, 180)),
    ],
    "character_select": {
        "god_select_frame": [
            Checkpoint([543, 849, 553, 859], Color(7, 108, 144)),
            Checkpoint([160, 1100, 166, 1106], Color(4, 96, 134)),
        ],
        "lock_in_button": [Checkpoint([1058, 1169, 1068, 1179], Color(255, 184, 0))],
    },
}


def get_screens(debug=False):
    return {
        "queue_detection": {
            "checkpoints": [
                *CHECKPOINTS["home_screen"],
            ],
            "locations": [new_section([2033, 1040, 2235, 1128])],
            "valid_queues": [
                {"name": "1v1 duel", "must_contain": ["1", "v", "1"]},
                {"name": "2v2 brawl", "must_contain": ["2", "v", "2"]},
                {"name": "3v3 brawl", "must_contain": ["2", "v", "2"]},
            ],
        },
        "match_results": {
            "2v2 brawl": {
                "checkpoints": [
                    Checkpoint([463, 535, 469, 541], Color(0, 107, 151)),
                    Checkpoint([463, 843, 469, 849], Color(223, 24, 24)),
                    Checkpoint([463, 535, 469, 541], Color(223, 24, 24)),
                    Checkpoint([463, 843, 469, 849], Color(0, 107, 151)),
                ],
                "locations": [new_section([1025, 240, 1550, 344])],
            },
        },
        "character_selection": {
            "2v2 brawl": {
                "checkpoints": [
                    *CHECKPOINTS["character_select"]["god_select_frame"],
                    *CHECKPOINTS["character_select"]["lock_in_button"],
                    Checkpoint(
                        [2235, 535, 2241, 541], Color(190, 20, 20)
                    ),  # red_team_box
                ],
                "locations": [
                    new_section([1930, 484, 2218, 519]),
                    new_section([1958, 612, 2218, 658], debug=True),
                ],
            },
            "3v3 Arcade": {
                "checkpoints": [
                    *CHECKPOINTS["character_select"]["god_select_frame"],
                    *CHECKPOINTS["character_select"]["lock_in_button"],
                    Checkpoint(
                        [2235, 930, 2241, 935], Color(190, 20, 20)
                    ),  # red_team_box3
                ],
                "locations": [
                    new_section([1930, 595, 2218, 650]),
                    new_section([1930, 730, 2218, 783]),
                    new_section([1930, 860, 2218, 920]),
                ],
            },
            "1v1 duel": {
                "checkpoints": [
                    *CHECKPOINTS["character_select"]["god_select_frame"],
                    *CHECKPOINTS["character_select"]["lock_in_button"],
                    Checkpoint(
                        [2245, 320, 2251, 326], Color(188, 20, 17)
                    ),  # red_team_box
                ],
                "locations": [
                    new_section([1989, 347, 2213, 387]),
                ],
            },
        },
    }
