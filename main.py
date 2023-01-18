import requests
from pprint import pprint as pp

twos = 469
ones = 511
queues = [{"id": 469, "name": "2v2"}, {"id": 511, "name": "1v1"}]
god_keys = ["god_1", "god_2", "god_3"]
bros_of_the_sun = ["JovialWalrus", "joyrida", "pazapaza", "wheels775", "maofish"] 

def get_leaderboard():
    r = requests.get("https://api2.hirezstudios.com/stats/leaderboard")
    results = r.json()
    leaders = results["rows"]
    _temp_lb = {"1v1": {}, "2v2": {}}
    leaderboard = {"1v1": {}, "2v2": {}}
    _temp_lb["1v1"] = [player for player in leaders if player["match_queue_id"] == ones]
    _temp_lb["2v2"] = [player for player in leaders if player["match_queue_id"] == twos]
    for queue in queues:
      for player in _temp_lb[queue["name"]]:
        gods = []
        for god in god_keys:
          if player[god] != "null":
            gods.append(player[god])
        leaderboard[queue["name"]][player["ranking"]] = {
          "player_name": player['player_name'],
          "gods": gods
        }
    return leaderboard

if __name__ == "__main__":
    leaders = get_leaderboard()
    for bro in bros_of_the_sun:
      found = False
      for queue in queues:
        for rank in leaders[queue["name"]]:
          if leaders[queue["name"]][rank]["player_name"] == bro:
            found = True
            print(f"{bro} is rank {rank} in {queue['name']}")
      if not found:
        print(f"{bro} is not in the top 500 in any queue, git gud scrub")
