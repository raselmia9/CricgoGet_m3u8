from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    requests = []

    page.on("request", lambda req: requests.append(req.url))

    page.goto("https://example.com")
    page.wait_for_timeout(5000)

    with open("output.txt", "w") as f:
        for url in requests:
            f.write(url + "\n")

    browser.close()
