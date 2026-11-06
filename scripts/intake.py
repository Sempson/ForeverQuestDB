"""Checks one pasted export. Only lines in the known format are kept, so nothing else
from an issue reaches the repository. The contributor is stored as a one-way hash."""
import hashlib
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_BAD_SHARE = 0.1
SPOT = r"\d+:\d+(?:\.\d+)?:\d+(?:\.\d+)?"
SPOTS = rf"(?:{SPOT}(?:;{SPOT})*)?"
KIND = r"(?:npc|object)?"
PATTERNS = [
    re.compile(r"FQSDATA3~[^~]*~[^~]*~[^~]*"),
    re.compile(rf"Q~\d+~[^~]*~{KIND}~\d*~{KIND}~\d*~[\d,]*~\d*~\d*"),
    re.compile(rf"G~\d+~\d+~[^~]*~\d*~{SPOTS}"),
    re.compile(rf"N~\d+~[^~]*~{SPOTS}~\d*~\d*~[^~]*~[^~]*~[a-z,]*~[\d,]*"),
    re.compile(rf"O~\d+~[^~]*~{SPOTS}"),
]


def known(line):
    return any(pattern.fullmatch(line) for pattern in PATTERNS)


def candidates(body):
    """Lines that look like export data, skipping the form's own text."""
    return [line.strip() for line in body.splitlines() if re.match(r"\s*(FQSDATA\d*~|[QGNO]~)", line)]


def check(body):
    """Returns (good lines, message for the player). No good lines means rejected."""
    lines = candidates(body)
    good = [line for line in lines if known(line)]
    if not lines:
        return [], "This doesn't look like a Forever Quest Sort export, so nothing was saved."
    if len(lines) - len(good) > len(lines) * MAX_BAD_SHARE:
        return [], "Part of this export looks changed or cut off, so nothing was saved. Copy it again from the Data tab."
    if not any(line.startswith(("Q~", "G~", "N~", "O~")) for line in good):
        return [], "This export has no quest data in it yet, so nothing was saved."
    return good, f"Thanks. {len(good)} lines were saved. Details join the database once enough players report the same thing."


def contributor(login):
    return hashlib.sha256(login.lower().encode("utf-8")).hexdigest()[:16]


def main():
    number = os.environ["ISSUE_NUMBER"]
    good, reply = check(os.environ.get("ISSUE_BODY") or "")
    if good:
        folder = ROOT / "pending"
        folder.mkdir(exist_ok=True)
        name = f"{contributor(os.environ['ISSUE_AUTHOR'])}-{int(number)}.txt"
        (folder / name).write_text("\n".join(good) + "\n", encoding="utf-8")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"result={'accepted' if good else 'rejected'}\n")
        output.write(f"reply={reply}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
