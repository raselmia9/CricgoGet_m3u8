from playwright.sync_api import sync_playwright
from datetime import datetime

URL = "https://cricgo.cc/player.php?id=willow"

def log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    line = f"[{t}] {msg}"
    print(line)
    with open("status.txt","a",encoding="utf-8") as f:
        f.write(line + "\n")

open("status.txt","w").close()

with sync_playwright() as p:
    log("🟢 Script Started")

    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    requests = []

    page.on("request", lambda r: requests.append(r.url))

    try:
        log("🔵 Opening page...")
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        log("🟢 Page Loaded")
        log("📄 Title: " + page.title())

        page.wait_for_timeout(15000)

        log(f"🟡 Total Requests: {len(requests)}")

        with open("output.txt","w",encoding="utf-8") as f:
            for url in requests:
                f.write(url + "\n")

        log("🟢 output.txt Created")

    except Exception as e:
        log("🔴 ERROR: " + str(e))

    finally:
        browser.close()
        log("🟢 Browser Closed")
        log("✅ Finished")
