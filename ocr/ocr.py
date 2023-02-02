#! /usr/bin/env python3

from PIL import Image, ImageGrab, ImageChops
from typing import List
from .screen import Section, Checkpoint


def detect_screen(box_item: dict, debug=False, test_threshold=None) -> bool | None:
    checkpoints = box_item["checkpoints"]
    checks_passed = test_checkpoints(checkpoints, debug, test_threshold)
    return checks_passed


def test_checkpoints(checkpoints: List[Checkpoint], debug=False, threshold=None) -> bool | None:
    results = []
    for checkpoint in checkpoints:
        if checkpoint.test():
            results.append(True)
        # Future Debugging
        else:
            if debug:
                print(
                    f"Checkpoint failed: pixel {[(checkpoint.bounds.start.x + checkpoint.center.x), (checkpoint.start.y + checkpoint.center.y)]}, color {checkpoint.color}"
                )

    # If we have more than half the checkpoints, we're good
    if threshold is not None:
       if len(results) >= threshold:
           return True 
    else:
        if len(results) == len(checkpoints):
            return True
    return False


def process_locations(
    locations: List[Section],
    text_to_lower: bool,
    use_inverted=True,
    config=None,
    debug=False,
) -> List[str]:
    """Given a list of boxes, return a list of strings of the text in each box"""
    results = []
    for section in locations:
        if debug:
            section.save_debug_image()
        boxText = section.get_text(text_to_lower, use_inverted, config)

        if (boxText is not None) and (len(boxText) > 0):
            results.append(boxText)
    return results


def filter_characters(input: str, filter_list: List[str]):
    return "".join([c for c in input if c in filter_list])


def contains_characters(input: str, characters: List[str]):
    for character in characters:
        if character not in input:
            return False
    return True
