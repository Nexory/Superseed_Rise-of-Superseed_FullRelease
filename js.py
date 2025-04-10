# js.py
import json

class Console:
    def log(self, *args):
        print(*args)

console = Console()

def loadPlayerData():
    try:
        with open('player_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"achievements": []}

def savePlayerData(data):
    with open('player_data.json', 'w') as f:
        json.dump(data, f)