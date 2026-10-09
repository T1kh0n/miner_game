import json
import os
from datetime import datetime

class LeaderboardManager:
    def __init__(self, filepath="assets/saves/leaderboard.json"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.entries = self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add_score(self, score, depth, skin):
        record = {
            "score": score,
            "depth": depth,
            "skin": skin,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.entries.append(record)
        self.entries.sort(key=lambda r: (r["score"], r["depth"]), reverse=True)
        self.entries = self.entries[:10]
        self.save()
