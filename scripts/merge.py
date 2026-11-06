"""Builds data/ from pending/. A fact only counts once MIN_PLAYERS different players have
reported it, so one player's mistake never reaches the database."""
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MIN_PLAYERS = 2
CELL = 0.02
NAME_LOCALE = "enUS"


def spots(text):
    result = []
    for spot in filter(None, text.split(";")):
        map_id, x, y = spot.split(":")
        result.append((int(map_id), float(x), float(y)))
    return result


class Votes:
    def __init__(self):
        self.who = collections.defaultdict(set)

    def add(self, value, player):
        if value not in (None, ""):
            self.who[value].add(player)

    def best(self):
        agreed = [(len(p), str(v), v) for v, p in self.who.items() if len(p) >= MIN_PLAYERS]
        return max(agreed)[2] if agreed else None


class Places:
    def __init__(self):
        self.cells = collections.defaultdict(lambda: {"players": set(), "points": []})

    def add(self, points, player):
        for map_id, x, y in points:
            cell = self.cells[(map_id, round(x / CELL), round(y / CELL))]
            cell["players"].add(player)
            cell["points"].append((x, y))

    def agreed(self):
        result = []
        for (map_id, _, _), cell in sorted(self.cells.items()):
            if len(cell["players"]) >= MIN_PLAYERS:
                xs, ys = zip(*cell["points"])
                result.append([map_id, round(sum(xs) / len(xs), 3), round(sum(ys) / len(ys), 3)])
        return result


def blank_quest():
    return {"title": Votes(), "giver": Votes(), "ender": Votes(), "after": {}, "goals": {}}


def blank_goal():
    return {"text": Votes(), "npc": Votes(), "spots": Places()}


def blank_entity():
    return {"name": Votes(), "spots": Places()}


def read(root):
    quests = collections.defaultdict(blank_quest)
    groups = {"N": collections.defaultdict(blank_entity), "O": collections.defaultdict(blank_entity)}
    pending = sorted((root / "pending").glob("*.txt")) if (root / "pending").exists() else []
    players = set()
    for path in pending:
        player = path.stem.split("-")[0]
        players.add(player)
        locale = None
        for line in path.read_text(encoding="utf-8").splitlines():
            parts = line.split("~")
            kind = parts[0]
            if kind == "FQSDATA2":
                locale = parts[3]
            names = locale == NAME_LOCALE
            if kind == "Q":
                quest = quests[int(parts[1])]
                if names:
                    quest["title"].add(parts[2], player)
                if parts[3] and parts[4]:
                    quest["giver"].add((parts[3], int(parts[4])), player)
                if parts[5] and parts[6]:
                    quest["ender"].add((parts[5], int(parts[6])), player)
                if parts[7]:
                    before = {int(q) for q in parts[7].split(",")}
                    known = quest["after"].get(player)
                    quest["after"][player] = before if known is None else known & before
            elif kind == "G":
                goal = quests[int(parts[1])]["goals"].setdefault(int(parts[2]), blank_goal())
                if names:
                    goal["text"].add(parts[3], player)
                if parts[4]:
                    goal["npc"].add(int(parts[4]), player)
                goal["spots"].add(spots(parts[5]), player)
            elif kind in groups:
                entity = groups[kind][int(parts[1])]
                if names:
                    entity["name"].add(parts[2], player)
                entity["spots"].add(spots(parts[3]), player)
    return quests, groups, players


def prerequisites(after):
    """Quests every reporting player had finished just before. Needs at least two players."""
    if len(after) < MIN_PLAYERS:
        return []
    return sorted(set.intersection(*after.values()))


def build(root):
    quests, groups, players = read(root)
    out_quests = {}
    for quest_id, q in sorted(quests.items()):
        goals = {}
        for index, g in sorted(q["goals"].items()):
            row = {"text": g["text"].best(), "npc": g["npc"].best(), "spots": g["spots"].agreed()}
            if row["npc"] or row["spots"]:
                goals[str(index)] = row
        giver, ender = q["giver"].best(), q["ender"].best()
        after = prerequisites(q["after"])
        row = {"title": q["title"].best(), "giver": list(giver) if giver else None,
               "ender": list(ender) if ender else None, "after": after, "goals": goals}
        if giver or ender or goals or after:
            out_quests[str(quest_id)] = row
    out = {"quests": out_quests}
    for key, label in (("N", "npcs"), ("O", "objects")):
        out[label] = {}
        for entity_id, e in sorted(groups[key].items()):
            places = e["spots"].agreed()
            if places:
                out[label][str(entity_id)] = {"name": e["name"].best(), "spots": places}
    folder = root / "data"
    folder.mkdir(exist_ok=True)
    for name, table in out.items():
        (folder / f"{name}.json").write_text(json.dumps(table, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    stats = {"players": len(players), "quests": len(out["quests"]), "npcs": len(out["npcs"]), "objects": len(out["objects"])}
    (folder / "stats.json").write_text(json.dumps(stats, indent=1) + "\n", encoding="utf-8")
    return stats


if __name__ == "__main__":
    print(build(ROOT))
    sys.exit(0)
