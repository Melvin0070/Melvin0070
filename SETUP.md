# Deploying your animated profile

This repo mirrors the structure of `Andrew6rant/Andrew6rant`:

```
Melvin0070/                 <- repo name MUST equal your username
├─ README.md                <- 8 lines; embeds the two SVGs responsively
├─ dark_mode.svg            <- generated, animated (dark theme)
├─ light_mode.svg           <- generated, animated (light theme)
├─ me.txt                   <- your ASCII portrait (source art)
├─ today.py                 <- generator: builds the SVGs + README
├─ requirements.txt
└─ .github/workflows/main.yml   <- rebuilds daily via GitHub Actions
```

## 1. Create the repo
Make a **public** repo named exactly `Melvin0070` (your username). GitHub shows
its `README.md` on your profile page.

## 2. Add these files
Commit everything in this folder to the repo's `main` branch.

## 3. Turn on Actions
Repo → **Settings → Actions → General → Workflow permissions** → choose
**Read and write permissions** → Save. Then the daily job can commit updates.

That's it. On every profile visit the SVG re-plays its "boot" animation, and
once a day the workflow refreshes your stats.

## Editing content
Everything shown lives in the `CONFIG` block at the top of `today.py`
(labels, values, hobbies, contact, titlebar text). Change a value, run
`python3 today.py`, commit. To restyle colors, edit the `DARK` / `LIGHT`
palettes in the same file.

## About the stats
- **Repos / Stars / Followers / Commits** auto-fill from the GitHub API when the
  workflow runs (via the built-in `GITHUB_TOKEN`). No personal token needed.
- **Lines of Code** (the `196,470++ / 53,940--` line) stays a value in `CONFIG`.
  Counting real additions/deletions means crawling every repo's full commit
  history with caching — that's what Andrew6rant's heavier `today.py` + `cache/`
  folder does. You can port that later; for now, edit the number by hand.

## Swapping the portrait
Replace `me.txt` with new ASCII (any width; the generator crops + measures it).
A **~40–50 column** portrait keeps the whole card narrow enough to avoid
horizontal scroll on phones.
