#!/usr/bin/env python3
"""Export Kindle highlights/notes from read.amazon.com/notebook.

Loads a saved browser session, scrapes all books and their
highlights/notes, and writes per-book markdown files to notes/.

Usage:
    python kindle_exporter.py           # incremental (skip existing files)
    python kindle_exporter.py --force   # re-export all books
"""

import argparse
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_DIR = Path(__file__).resolve().parent
STATE_DIR = PROJECT_DIR / "state"
SESSION_FILE = STATE_DIR / "kindle_session.json"
NOTES_DIR = PROJECT_DIR / "notes"
NOTEBOOK_URL = "https://read.amazon.com/notebook"


def sanitize_filename(name: str) -> str:
    """Remove or replace characters that are unsafe for filenames."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip('. ')
    return name[:200]  # cap length


def extract_books(page) -> list[dict]:
    """Extract the list of books from the sidebar."""
    page.wait_for_selector(
        "#kp-notebook-library .kp-notebook-library-each-book",
        timeout=30000,
    )
    book_els = page.query_selector_all(
        "#kp-notebook-library .kp-notebook-library-each-book"
    )
    books = []
    for el in book_els:
        title_el = el.query_selector("h2")
        author_el = el.query_selector("p")
        title = title_el.inner_text().strip() if title_el else "Unknown Title"
        author = author_el.inner_text().strip() if author_el else "Unknown Author"
        # Clean "By: " prefix from author
        author = re.sub(r'^By:\s*', '', author, flags=re.IGNORECASE)
        books.append({"element": el, "title": title, "author": author})
    return books


def extract_highlights(page) -> list[dict]:
    """Extract all highlights/notes for the currently selected book."""
    # Wait for annotations to appear (or the empty state)
    try:
        page.wait_for_selector(
            "#kp-notebook-annotations .a-row",
            timeout=10000,
        )
    except Exception:
        return []

    # Small delay to let all annotations render
    time.sleep(1)

    annotations = page.query_selector_all(
        "#kp-notebook-annotations > .a-row.a-spacing-base"
    )

    highlights = []
    for ann in annotations:
        # Highlight text
        hl_el = ann.query_selector("#highlight")
        highlight_text = hl_el.inner_text().strip() if hl_el else ""

        # Note text
        note_el = ann.query_selector("#note")
        note_text = note_el.inner_text().strip() if note_el else ""

        # Header with color and location info
        header_el = ann.query_selector("#annotationHighlightHeader")
        if not header_el:
            header_el = ann.query_selector("#annotationNoteHeader")
        header_text = header_el.inner_text().strip() if header_el else ""

        # Parse location and page from header like "Yellow highlight | Location: 1234"
        # or "Yellow highlight | Page: 56, Location: 1234"
        location = ""
        page_num = ""
        color = ""

        loc_match = re.search(r'Location:\s*(\S+)', header_text, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).rstrip(',')

        page_match = re.search(r'Page:\s*(\S+)', header_text, re.IGNORECASE)
        if page_match:
            page_num = page_match.group(1).rstrip(',')

        color_match = re.match(r'(\w+)\s+highlight', header_text, re.IGNORECASE)
        if color_match:
            color = color_match.group(1)

        if highlight_text or note_text:
            highlights.append({
                "text": highlight_text,
                "note": note_text,
                "location": location,
                "page": page_num,
                "color": color,
            })

    return highlights


def write_markdown(book_title: str, author: str, highlights: list[dict], output_dir: Path):
    """Write a markdown file for a single book."""
    filename = sanitize_filename(f"{book_title} - {author}") + ".md"
    filepath = output_dir / filename

    lines = [
        f"# {book_title}",
        f"**Author:** {author}",
        "",
        "---",
        "",
    ]

    for hl in highlights:
        if hl["text"]:
            lines.append(f"> {hl['text']}")
            lines.append("")

        if hl["note"]:
            lines.append(f"**Note:** {hl['note']}")

        meta_parts = []
        if hl["location"]:
            meta_parts.append(f"**Location:** {hl['location']}")
        if hl["page"]:
            meta_parts.append(f"**Page:** {hl['page']}")
        if meta_parts:
            lines.append(" | ".join(meta_parts))

        lines.append("")
        lines.append("---")
        lines.append("")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


def existing_book_files(output_dir: Path) -> set[str]:
    """Return set of existing markdown filenames (without extension) in output dir."""
    return {f.stem for f in output_dir.glob("*.md")}


def main():
    parser = argparse.ArgumentParser(description="Export Kindle highlights to markdown")
    parser.add_argument(
        "--force", action="store_true",
        help="Re-export all books (default: skip books that already have a file)",
    )
    parser.add_argument(
        "--chrome", action="store_true",
        help="Use system Chrome instead of Playwright's bundled Chromium",
    )
    args = parser.parse_args()

    if not SESSION_FILE.exists():
        print(f"Session file not found: {SESSION_FILE}")
        print("Run auth_setup.py first to log in and save your session.")
        raise SystemExit(1)

    NOTES_DIR.mkdir(exist_ok=True)
    existing = existing_book_files(NOTES_DIR)

    with sync_playwright() as p:
        launch_opts = {"headless": True}
        if args.chrome:
            launch_opts["channel"] = "chrome"
        browser = p.chromium.launch(**launch_opts)
        context = browser.new_context(storage_state=str(SESSION_FILE))
        page = context.new_page()

        print("Navigating to Kindle notebook...")
        page.goto(NOTEBOOK_URL, wait_until="networkidle")

        # Check if we got redirected to login
        if "signin" in page.url or "ap/signin" in page.url:
            print("Session expired. Please re-run auth_setup.py to log in again.")
            browser.close()
            raise SystemExit(1)

        books = extract_books(page)
        print(f"Found {len(books)} books")

        exported = 0
        skipped = 0

        for i, book in enumerate(books):
            title = book["title"]
            author = book["author"]
            file_stem = sanitize_filename(f"{title} - {author}")

            if not args.force and file_stem in existing:
                skipped += 1
                continue

            print(f"  [{i+1}/{len(books)}] {title} by {author}...")

            # Click the book to load its highlights
            book["element"].click()

            # Wait for content to update
            try:
                page.wait_for_selector(
                    "#kp-notebook-annotations",
                    timeout=15000,
                )
            except Exception:
                print(f"    Timeout waiting for annotations, skipping")
                continue

            # Small pause for content to fully render
            time.sleep(1)

            highlights = extract_highlights(page)

            if not highlights:
                print(f"    No highlights found, skipping")
                continue

            filepath = write_markdown(title, author, highlights, NOTES_DIR)
            print(f"    Wrote {len(highlights)} highlights to {filepath.name}")
            exported += 1

        browser.close()

    print(f"\nDone: {exported} exported, {skipped} skipped (already exist)")


if __name__ == "__main__":
    main()
