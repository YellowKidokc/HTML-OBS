# Consilience Atlas Engine — READ ME FIRST

A **local-first epistemic analysis engine** that runs entirely on your own
Windows computer. It reads a paper, breaks it into addressable "atoms," lets an
AI classify each one (while keeping AI guesses clearly labelled), and renders a
clickable **Local Atlas / Periodic Table** with dependency and topology maps.

Nothing is sent to the cloud except the AI calls you choose to make. Your data
lives on your machine. There is a **Mock AI** mode that works with no key and no
internet, so you can try everything for free.

---

## What this program does
1. You upload a Markdown, TXT, or HTML paper (or use the built-in demo).
2. It analyzes the paper into **atoms** and a **relation graph**.
3. You **review, approve, and freeze** atom boundaries.
4. Everything is stored locally in a small SQLite database.
5. It renders the paper's **Periodic Table**, an **atom dossier**, and
   **dependency / emergent / Ψ-topology** maps.
6. You can **export** canonical JSON + HTML and **back up** the whole atlas.

**Core rule it never breaks:** *internal coherence is not external truth.*
Scores are rubric scores, **not** "% true." AI guesses are always marked as AI
guesses, and uncertain ones are flagged for your review.

---

## How to install (once)
1. Install **Python 3.11 or 3.12** from https://python.org (tick "Add to PATH").
2. Double-click **`setup.bat`**. It creates a private environment, installs
   everything, creates the database, and makes a `.env` file for you.

## How to start it
Double-click **`run.bat`**. Your browser opens at **http://127.0.0.1:8501**.

## How to stop the server
Close the black `run.bat` window, or press **Ctrl+C** in it.

---

## Where my data lives
Everything is under the **`data\`** folder:
- `data\atlas.db` — the database
- `data\sources\` — normalized copies of your papers
- `data\canonical\` — canonical JSON exports
- `data\rendered\` — rendered HTML
- `data\backups\` — timestamped backups
- `data\logs\` — error logs if something breaks

## How to add the DeepSeek key (optional)
1. Open the **`.env`** file in the project folder with Notepad.
2. Set `DEEPSEEK_API_KEY=your_key_here` and save.
3. Restart the app.
Without a key, the app still runs in **Mock AI** mode.

## How to ingest a paper
Sidebar → **Ingest Paper** → upload a file (or keep the demo) → give it a title →
click **ANALYZE PAPER**. Watch the 7-step progress. When done, open **Papers**.

## How to review atoms
**Papers → Atom Review**: expand each atom to **Approve**, **Freeze**, or
**Reject** it. Frozen boundaries survive re-ingestion.

## How to back up
Click **💾 Back up Atlas** in the sidebar. A timestamped copy of the database,
canonical JSON, and prompts is written to `data\backups\`.

## How to restore
Sidebar → **Database** → pick a backup → tick the confirmation → **RESTORE DATABASE**.

## How to export
Sidebar → **Export** → pick a paper → export canonical JSON + HTML + graph JSON.

## What to do if something breaks
- The app shows the error on screen and writes details to `data\logs\`.
- A failed ingestion never corrupts data you already approved.
- Worst case: restore from a backup, or delete `data\atlas.db` and re-run
  `setup.bat` to start a fresh database (your source papers stay in `data\sources\`).

---

## For the curious: how it's built
- **Engine** is plain Python in `atlas/` — independent of the GUI.
- **GUI** is `app.py` (Streamlit), a thin layer on top.
- **Tests**: from a terminal in this folder run `.venv\Scripts\python -m pytest`.
