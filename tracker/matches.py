import sqlite3
from typing import List, Dict
from tabulate import tabulate


class MatchEntry(Dict):
    date: str
    opponent1: str
    opponent2: str
    opponent3: str
    game_mode: str
    result: int


class MatchHistory:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.game_modes = {
            "1v1 duel": 1,
            "2v2 brawl": 2,
            "3v3 arcade": 3,
        }
        self.game_modes_reverse = {v: k for k, v in self.game_modes.items()}
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS match_results (
                      id INTEGER PRIMARY KEY,
                      date TEXT DEFAULT CURRENT_TIMESTAMP,
                      opponent1 TEXT,
                      opponent2 TEXT,
                      opponent3 TEXT,
                      game_mode INTEGER,
                      result INTEGER
                  )"""
        )
        self.conn.commit()

    def add_result(self, game_mode, result, opponent1, opponent2=None, opponent3=None):
        values = (opponent1, opponent2, opponent3, self.game_modes[game_mode], result)
        self.cursor.execute(
            "INSERT INTO match_results (opponent1, opponent2, opponent3, game_mode, result) VALUES (?, ?, ?, ?, ?)",
            values,
        )
        self.conn.commit()

    def get_results(self, game_mode, count=10) -> List[MatchEntry]:
        self.cursor.execute(
            "SELECT * FROM match_results WHERE game_mode = ? ORDER BY id DESC LIMIT ?",
            (self.game_modes[game_mode], count),
        )
        results = []
        for record in self.cursor.fetchall():
            match = MatchEntry()
            match["date"] = record[1]
            match["opponent1"] = record[2]
            if record[5] >= 2:
                match["opponent2"] = record[3]
            if record[5] >= 3:
                match["opponent3"] = record[4]
            match["game_mode"] = self.game_modes_reverse[record[5]]
            match["result"] = "Win" if record[6] == 1 else "Loss"
            results.append(match)
        return results

    def get_win_loss(self, game_mode):
        base_query = f"""
        SELECT count(*) 
        FROM match_results 
        WHERE game_mode = ? 
            AND result = ?
        """
        self.cursor.execute(base_query, (self.game_modes[game_mode], 1))
        wins = self.cursor.fetchall()[0]
        self.cursor.execute(base_query, (self.game_modes[game_mode], 0))
        losses = self.cursor.fetchall()[0]
        return {"wins": wins[0], "losses": losses[0]}

    def history_to_table(self, entries: List[MatchEntry]):
        if len(entries) == 0:
            return "No matches found"
        return tabulate(
            entries,
            headers="keys",
            tablefmt="fancy_outline",
            colalign=("left", "left", "left", "center", "center"),
            missingval="",
        )
