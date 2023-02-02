from typing import NamedTuple


class Color(NamedTuple):
    red: int
    green: int
    blue: int


def color_delta(color1: Color, color2: Color) -> int:
    """Given two RGB Colors, return the cumulative difference between their values"""
    return int(sum([abs(color1[i] - color2[i]) for i in range(3)]))
