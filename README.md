# ForeverQuestDB

A quest database for World of Warcraft: Forever, built from what players see in the game. The data comes from the Data tab in the Forever Quest Sort addon.

## Add your data

1. In the game, open Forever Quest Sort, go to the Data tab and press **Export Data**.
2. Copy a part with Ctrl+C.
3. Open the **Submit quest data** form under Issues, paste it and submit.
4. If your export has more than one part, submit each part separately.

You'll get a reply when your submission has been checked.

## Privacy

Exports have no character, realm or account names. Submissions are public GitHub issues, so your GitHub username is visible there. In this repository's data files, a contributor is stored only as a one-way hash of their username, which keeps two submissions from one person from counting as two players.

## How data is accepted

A submission is checked automatically, and only lines in the export format are kept. A fact joins `data/` once at least two different players have reported it, so one mistake doesn't reach the database. Names are taken from English clients only for now.

## Files

- `pending/` holds every accepted submission.
- `data/quests.json`, `data/npcs.json`, `data/objects.json` and `data/fishing.json` hold the agreed data.
- `data/stats.json` counts it.
