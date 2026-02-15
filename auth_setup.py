#!/usr/bin/env python3
"""One-time interactive login to save Amazon Kindle session state.

Launches a visible browser so you can log into Amazon manually
(handles 2FA, CAPTCHA, etc.). After login, saves the browser
session to state/kindle_session.json for headless reuse.

Re-run this script whenever the session expires.
"""

import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_DIR = Path(__file__).resolve().parent
STATE_DIR = PROJECT_DIR / "state"
SESSION_FILE = STATE_DIR / "kindle_session.json"
NOTEBOOK_URL = "https://read.amazon.com/notebook"


def main():
    parser = argparse.ArgumentParser(description="Interactive login to save Amazon Kindle session")
    parser.add_argument(
        "--chrome", action="store_true",
        help="Use system Chrome instead of Playwright's bundled Chromium",
    )
    args = parser.parse_args()

    STATE_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        launch_opts = {"headless": False}
        if args.chrome:
            launch_opts["channel"] = "chrome"
        browser = p.chromium.launch(**launch_opts)
        context = browser.new_context()
        page = context.new_page()

        page.goto(NOTEBOOK_URL)

        print("Please log into your Amazon account in the browser window.")
        print("After you see your Kindle notebook page, press Enter here to save the session.")
        input("\nPress Enter when logged in and notebook page is visible... ")

        context.storage_state(path=str(SESSION_FILE))
        print(f"Session saved to {SESSION_FILE}")

        browser.close()


if __name__ == "__main__":
    main()
