from playwright.sync_api import sync_playwright

URL = "https://cricgo.cc/player.php?id=willow"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(10000)

    with open("page_title.txt", "w", encoding="utf-8") as f:
        f.write(page.title())

    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(page.content())

    page.screenshot(path="page.png", full_page=True)

    browser.close()
