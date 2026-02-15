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

### macOS Application Launcher

For easy access on macOS, create an application in your Applications folder:

```bash
cat > /tmp/kindle_exporter_script.applescript << 'EOF'
do shell script "cd '/path/to/kindle-notes' && /usr/bin/python3 kindle_exporter.py --chrome > /tmp/kindle_export.log 2>&1"

display notification "Kindle notes export completed. Check log for details." with title "Kindle Exporter"

do shell script "open /tmp/kindle_export.log"
EOF

osacompile -o "/Applications/0 Kindle Notes Exporter.app" /tmp/kindle_exporter_script.applescript
rm /tmp/kindle_exporter_script.applescript
```

Replace `/path/to/kindle-notes` with your actual project path. The app will appear at the top of your Applications folder (starts with "0"), and when run it will export new highlights and show the results.

### Cron Job

A weekly cron job runs the exporter every Monday at 5am:

```
0 5 * * 1 cd /path/to/kindle-notes && .venv/bin/python kindle_exporter.py >> cron.log 2>&1
```
