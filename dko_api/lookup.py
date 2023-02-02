import requests
from pprint import pprint as pp
from sortedcontainers import SortedList
from typing import TypedDict, List


queues = [{"id": 469, "name": "2v2 brawl"}, {"id": 511, "name": "1v1 duel"}]
god_keys = ["god_1", "god_2", "god_3"]
twos = 469
ones = 511


class Player(TypedDict):
    Rank: int
    Name: str
    Gods: List[str]
    Queue: str


class Leaderboard:
    def __init__(self):
        self.leaders = self.get_leaderboard()

    def get_leaderboard(self):
        r = requests.get("https://api2.hirezstudios.com/stats/leaderboard")
        results = r.json()
        leaders = results["rows"]
        _temp_lb = {
            "1v1 duel": [
                player for player in leaders if player["match_queue_id"] == ones
            ],
            "2v2 brawl": [
                player for player in leaders if player["match_queue_id"] == twos
            ],
        }
        leaderboard = {}
        for queue in queues:
            ranks = SortedList(key=lambda x: x["rank"])
            entries = []
            for entry in _temp_lb[queue["name"]]:
                gods = []
                for god in god_keys:
                    if entry[god] != "null" and entry[god] != None:
                        gods.append(entry[god].title())
                entries.append(
                    {
                        "name": entry["player_name"],
                        "rank": entry["ranking"],
                        "gods": gods,
                    }
                )
            ranks.update(entries)
            leaderboard[queue["name"]] = ranks
        return leaderboard

    def lookup(self, player_name: str) -> List[dict]:
        matches = []
        for queue in queues:
            lb = self.leaders[queue["name"]]
            for entry in lb:
                if entry["name"] == player_name:
                    entry["queue"] = queue["name"]
                    matches.append(entry)
                    break

        return matches
