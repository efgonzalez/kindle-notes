# Kindle Notes Exporter

Export all Kindle highlights and notes from [read.amazon.com/notebook](https://read.amazon.com/notebook) into per-book markdown files using Playwright.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
sudo playwright install-deps chromium
```

## Usage

### 1. Authenticate (one-time)

```bash
python auth_setup.py
```

Opens a browser window — log into your Amazon account, then press Enter in the terminal to save the session. Re-run whenever the session expires.

### 2. Export highlights

```bash
python kindle_exporter.py          # incremental (skips books already exported)
python kindle_exporter.py --force  # re-export all books
```

Markdown files are written to `notes/`, one per book.

### Output format

```markdown
# Book Title
**Author:** Author Name

---

> Highlight text here

**Note:** User's note if any
**Location:** 1234 | **Page:** 56

---
```

## Automation

A weekly cron job runs the exporter every Monday at 9am:

```
0 9 * * 1 /home/edu/kindle-notes/.venv/bin/python kindle_exporter.py >> cron.log 2>&1
```
