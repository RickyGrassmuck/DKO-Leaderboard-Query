import click
import pytesseract
from dko_api import lookup
from ocr import ocr, utils, screen
import time
from typing import TypedDict, List
from ocr.utils import queues
from tracker.matches import MatchHistory

debug_mode = False
SCREENS = screen.get_screens()


class QueueDetection(TypedDict):
    Name: str
    Valid: bool


class Opponents(TypedDict):
    Name: str
    Valid: bool


def detect_queue() -> QueueDetection:
    result = QueueDetection(Name="", Valid=False)
    queue_detect_box = SCREENS["queue_detection"]
    valid_queues = queue_detect_box["valid_queues"]
    detected = False
    while not detected:
        found = ocr.detect_screen(queue_detect_box, debug=debug_mode)
        if found:
            print("Queue detected")
            detected = True
            break
        if debug_mode:
            print("Queue not detected")
            time.sleep(2)
        else:
            time.sleep(0.5)

    process_results = ocr.process_locations(
        queue_detect_box["locations"], text_to_lower=True
    )
    if len(process_results) == 0:
        print("No queue text detected")
        return result
    queue_text = process_results[0]
    print(f"Found queue text: {queue_text}")
    for queue in valid_queues:
        filtered = ocr.filter_characters(queue_text, queue["name"])
        if ocr.contains_characters(filtered, queue["must_contain"]):
            result["Name"] = queue["name"]
            result["Valid"] = True
            break
    else:
        result["Name"] = queue_text
    return result


def detect_opponent_names(box: dict, queue: str):
    while ocr.detect_screen(box):
        results = ocr.process_locations(
            SCREENS["character_selection"][queue]["locations"],
            text_to_lower=False,
            debug=debug_mode,
        )
        if len(results) > 0:
            return results
        time.sleep(3)
    return None


def detect_match_results(queue: str):
    while not ocr.detect_screen(
        SCREENS["match_results"][queue], debug=debug_mode, test_threshold=2
    ):
        time.sleep(3)

    results = ocr.process_locations(
        SCREENS["match_results"][queue]["locations"],
        text_to_lower=True,
        config="--psm 7",
        debug=debug_mode,
    )
    if debug_mode:
        print(f"[detect_match_results]: {results}")
    return results


def save_match_results(db: MatchHistory, opponents: List[str], game_mode: str):
    results = detect_match_results(game_mode)
    result = None
    if len(results) > 0:
        if results[0] == "defeat":
            result = 0
        elif results[0] == "victory":
            result = 1
    if result is None:
        click.echo("No match results detected")
        res = click.prompt("Did you win or lose? (y/n)", type=click.Choice(["y", "n"]))
        result = 1 if res == "y" else 0
    db.add_result(game_mode, result, *opponents)
    if result == 1:
        click.echo("You have won!")
    else:
        click.echo("You have been defeated!")


def print_last_5_matches(db: MatchHistory, game_mode: str):
    last_5_matches = db.get_results(game_mode, 5)
    if len(last_5_matches) > 0:
        click.echo("\nLast 5 Matches")
        click.echo(db.history_to_table(last_5_matches))
        summary = db.get_win_loss(game_mode=game_mode)
        click.echo(f"Total Wins: {summary['wins']} Losses: {summary['losses']}")


@click.command()
@click.option(
    "--tesseract-cmd",
    default=r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    help="Location of the tesseract executable.",
)
@click.option(
    "--queue",
    required=False,
    type=click.Choice(["1v1", "2v2", "3v3"], case_sensitive=True),
    help="Name of the queue to look for. Skips queue detection if provided.",
)
def run(tesseract_cmd, queue):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    print("Starting...")
    leaders = lookup.Leaderboard()
    queue_name = queues.get(queue)
    match_history = MatchHistory("match_history.db")

    if queue_name is None:
        print("Invalid queue name provided, exiting...")
        return
    while True:
        # Detect queue
        if queue is None:
            queue_detection = QueueDetection(Name=queue_name, Valid=True)
            print("Waiting for queue to start...")
            queue_detection = detect_queue()
            while not queue_detection["Valid"]:
                print(f"Invalid queue name detected {queue_detection['Name']}")
                time.sleep(5)
                queue_detection = detect_queue()
            print(
                f"Valid Queue Name detected: {queue_detection['Name']}, waiting for match to start..."
            )
            print_last_5_matches(match_history, queue_detection["Name"])
        else:
            print(
                f"Skipping queue detection, waiting for {queue} character selection screen..."
            )
            queue_detection = QueueDetection(Name=queue_name, Valid=True)
            print_last_5_matches(match_history, queue_detection["Name"])

        char_select_box = SCREENS["character_selection"][queue_detection["Name"]]
        while not ocr.detect_screen(char_select_box):
            time.sleep(3)

        # Character selection screen detected, looking for opponent names
        print("Found character selection screen, looking for opponent names...")
        opponents = detect_opponent_names(char_select_box, queue_detection["Name"])
        if (opponents is not None) and (len(opponents) > 0):
            matches = []
            for opponent in opponents:
                leaderboard_entries = leaders.lookup(opponent)
                if len(leaderboard_entries) > 0:
                    matches.extend(leaderboard_entries)

            if len(matches) == 0:
                print(
                    f"Not found on the leaderboard: {', '.join(opponents)}, have fun!"
                )
            else:
                body = []
                for match in matches:
                    body.append(
                        f"Player: {match['name']} | Queue: {match['queue']} | Rank: {match['rank']} | Gods: {', '.join(match['gods'])}"
                    )

                utils.print_surrounded("Leaderboard Alert", "\n".join(body))
            print("Good luck! Waiting for match results...")
            save_match_results(match_history, opponents, queue_detection["Name"])
        else:
            print("No opponents were able to be detected, restarting detection...")


if __name__ == "__main__":
    run()
