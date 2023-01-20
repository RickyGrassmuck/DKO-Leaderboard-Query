import click
import pytesseract
from lib import lookup, ocr, utils
import time
from typing import TypedDict

class QueueDetection(TypedDict):
  Name: str
  Valid: bool

class Opponents(TypedDict):
  Name: str
  Valid: bool

def detect_queue() -> QueueDetection:
  result = QueueDetection(Name="", Valid=False)
  queue_detect_box = ocr.BOXES["queue_detection"]
  valid_queues = queue_detect_box["valid_queues"]
  detected = False
  while not detected:
    found = ocr.detect_screen(queue_detect_box)
    if found:
      print("Queue detected")
      detected = True
      break
    time.sleep(2)

  process_results = ocr.process_locations(queue_detect_box["locations"], text_to_lower=True)
  if len(process_results) == 0:
    print("No queue text detected")
    return result
  queue_text = process_results[0]
  print(f"Found queue text: {queue_text}")
  for queue in valid_queues:
    filtered = ocr.filter_characters(queue_text, queue['name'])
    if ocr.contains_characters(filtered, queue['must_contain']):
      result["Name"] = queue['name']
      result["Valid"] = True
      break
  else:
    result["Name"] = queue_text
  return result

def detect_opponent_names(box: dict, queue: str):
  while ocr.detect_screen(box):
    results = ocr.process_locations(ocr.BOXES["character_selection"][queue]['locations'], text_to_lower=False)
    if len(results) > 0:
      return results
    time.sleep(3)
  return None



@click.command()
@click.option('--tesseract-cmd', default=r'C:\Program Files\Tesseract-OCR\tesseract.exe', help='Location of the tesseract executable.')
def run(tesseract_cmd):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    print("Starting...")
    leaders = lookup.Leaderboard()      
    while True:
      # Detect queue
      print("Waiting for queue to start...")
      queue_detection = detect_queue()
      while not queue_detection["Valid"]:
        print(f"Invalid queue name detected {queue_detection['Name']}")
        time.sleep(5)
        queue_detection = detect_queue()

      # Valid queue was detected, waiting for character selection screen
      print(f"Valid Queue Name detected: {queue_detection['Name']}, waiting for match to start...")
      char_select_box = ocr.BOXES["character_selection"][queue_detection["Name"]]
      while not ocr.detect_screen(char_select_box):
        time.sleep(3)
      
      # Character selection screen detected, looking for opponent names
      print("Found character selection screen, looking for opponent names...")
      opponents = detect_opponent_names(char_select_box, queue_detection["Name"])
      if (opponents is not None) and (len(opponents) > 0):
        # Since we extracted opponent names, we can sleep long enough to get
        # past the character selection screen and start the loop over
        sleep_time = 30 
        #Looking up opponents on leaderboard
        matches = []
        for opponent in opponents:
          leaderboard_entries = leaders.lookup(opponent)
          if len(leaderboard_entries) > 0:
            matches.extend(leaderboard_entries)
        
        if len(matches) == 0:
          print(f"Not found on the leaderboard: {', '.join(opponents)}, have fun!")
        else:
          body = []
          for match in matches:
            body.append(f"Player: {match['name']} | Queue: {match['queue']} | Rank: {match['rank']} | Gods: {', '.join(match['gods'])}")
          
          utils.print_surrounded("Leaderboard Alert", '\n'.join(body))
        print("Good luck! Restarting detection...")
      else:
        print("No opponents were able to be detected, restarting detection...")



if __name__ == '__main__':
    run()

