# Kindle Notes Exporter

Export all Kindle highlights and notes from [read.amazon.com/notebook](https://read.amazon.com/notebook) into per-book markdown files using Playwright.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then install a browser. Either use Playwright's bundled Chromium:

```bash
playwright install chromium
sudo playwright install-deps chromium   # Linux only
```

Or use your system Chrome by passing `--chrome` to the scripts (no extra install needed).

## Usage

### 1. Authenticate (one-time)

```bash
python auth_setup.py             # uses Playwright Chromium
python auth_setup.py --chrome    # uses system Chrome
```

Opens a browser window — log into your Amazon account, then press Enter in the terminal to save the session. Re-run whenever the session expires.

### 2. Export highlights

```bash
python kindle_exporter.py                    # incremental, Playwright Chromium
python kindle_exporter.py --chrome           # incremental, system Chrome
python kindle_exporter.py --force            # re-export all books
python kindle_exporter.py --force --chrome   # re-export all, system Chrome
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

A weekly cron job runs the exporter every Monday at 5am:

```
0 5 * * 1 cd /path/to/kindle-notes && .venv/bin/python kindle_exporter.py >> cron.log 2>&1
```
