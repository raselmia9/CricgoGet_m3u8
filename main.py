from playwright.sync_api import sync_playwright

URL = "https://cricgo.cc/player.php?id=willow"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    requests = []

    def capture(req):
        requests.append(req.url)

    page.on("request", capture)

    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(15000)

    with open("output.txt", "w", encoding="utf-8") as f:
        if requests:
            for url in requests:
                f.write(url + "\n")
        else:
            f.write("No network requests captured.")

    browser.close()
