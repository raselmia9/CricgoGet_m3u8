from playwright.sync_api import sync_playwright
from datetime import datetime

URL = "https://cricgo.cc/player.php?id=willow"

# Log function
def log(message):
    now = datetime.now().strftime("%H:%M:%S")
    line = f"[{now}] {message}"
    print(line)
    with open("status.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")

# Clear old files
open("status.txt", "w").close()
open("output.txt", "w").close()

with sync_playwright() as p:
    log("🟢 Script Started")

    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
    )

    page = browser.new_page(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36"
    )

    requests = []

    # Capture every request
    def capture(req):
        requests.append(req.url)

    page.on("request", capture)

    try:
        log("🔵 Opening page...")
        response = page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        if response:
            log(f"🟢 HTTP Status : {response.status}")

        page.wait_for_timeout(15000)

        title = page.title()
        log(f"📄 Title : {title}")

        with open("title.txt", "w", encoding="utf-8") as f:
            f.write(title)

        html = page.content()
        with open("page.html", "w", encoding="utf-8") as f:
            f.write(html)

        page.screenshot(path="cloudflare.png", full_page=True)
        log("📸 Screenshot Saved")

        with open("output.txt", "w", encoding="utf-8") as f:
            for url in requests:
                f.write(url + "\n")

        log(f"🟡 Total Requests : {len(requests)}")
        log("🟢 output.txt Created")
        log("🟢 page.html Created")
        log("🟢 title.txt Created")
        log("🟢 cloudflare.png Created")

    except Exception as e:
        log(f"🔴 ERROR : {e}")

    finally:
        browser.close()
        log("🟢 Browser Closed")
        log("✅ Finished")
