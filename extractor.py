import time
import sys
from playwright.sync_api import sync_playwright

STATUS_FILE = "status.txt"
OUTPUT_FILE = "m3u8_link.txt"

def log(message, level="INFO"):
    icons = {
        "INFO": "🔵 [INFO]",
        "SUCCESS": "🟢 [SUCCESS]",
        "WARNING": "🟡 [WARNING]",
        "ERROR": "🔴 [ERROR]"
    }
    formatted = f"{icons.get(level, '🔹')} - {message}\n"
    print(formatted.strip())
    with open(STATUS_FILE, "a", encoding="utf-8") as f:
        f.write(formatted)

def main():
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("=== CRICGO M3U8 EXTRACTOR STATUS LOG ===\n")
    
    url = "https://cricgo.cc/player.php?id=willow"
    log(f"টার্গেট ইউআরএল সেটআপ সফল হয়েছে: {url}", "INFO")
    
    m3u8_link = None

    log("Playwright ব্রাউজার অ্যাডভান্সড হিউম্যান বাইপাস মোডে ইনিশিয়ালাইজ করা হচ্ছে...", "INFO")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--lang=en-US,en"
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        
        page = context.new_page()

        # বট ডিটেকশন জাভাস্ক্রিপ্ট ফ্লাগ রিমুভ করা
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)

        def intercept_request(request):
            nonlocal m3u8_link
            if ".m3u8" in request.url:
                if not m3u8_link:
                    m3u8_link = request.url
                    log(f"নেটওয়ার্ক ট্রাফিক থেকে M3U8 লিংক ক্যাপচার করা হয়েছে: {m3u8_link}", "SUCCESS")

        page.on("request", intercept_request)

        try:
            log(f"টার্গেট লিংকে প্রবেশ করা হচ্ছে: {url}", "INFO")
            # এখানে networkidle পরিবর্তন করে domcontentloaded দেওয়া হয়েছে
            page.goto(url, timeout=60000, wait_until="domcontentloaded") 
            
            log("ক্লাউডফায়ার হিউম্যান চ্যালেঞ্জ অতিক্রম করার জন্য ওয়েট এবং হিউম্যান সিমুলেশন চলছে...", "WARNING")
            
            # রিয়েল ইউজারের মতো পেজে মাউস মুভমেন্ট এবং স্ক্রোল সিমুলেট করা
            for _ in range(3):
                try:
                    page.mouse.move(100 + _ * 50, 100 + _ * 30)
                    page.mouse.down()
                    page.mouse.up()
                    page.evaluate("window.scrollBy(0, 300);")
                    time.sleep(3)
                except:
                    pass

            # অতিরিক্ত সময় অপেক্ষা যাতে ক্লাউডফায়ার কুকিজ পাস করে দেয়
            time.sleep(10)

            # যদি নেটওয়ার্কে সরাসরি না ধরে, তবে পেজ ও আইফ্রেমের ভেতর থেকে খোঁজা
            for _ in range(10):
                if m3u8_link:
                    break
                time.sleep(2)
                
                content = page.content()
                if ".m3u8" in content:
                    import re
                    matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', content)
                    if matches:
                        m3u8_link = matches[0]
                        log(f"পেজ সোর্স থেকে M3U8 লিংক উদ্ধার করা হয়েছে: {m3u8_link}", "SUCCESS")
                        break

                for frame in page.frames:
                    try:
                        f_content = frame.content()
                        if ".m3u8" in f_content:
                            import re
                            matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', f_content)
                            if matches:
                                m3u8_link = matches[0]
                                log(f"আইফ্রেম থেকে M3U8 লিংক উদ্ধার করা হয়েছে: {m3u8_link}", "SUCCESS")
                                break
                    except:
                        pass

        except Exception as e:
            err_msg = str(e)
            log(f"অটোমেশনে ত্রুটি ঘটেছে: {err_msg}", "ERROR")
        finally:
            browser.close()
            log("ব্রাউজার সেশন সফলভাবে বন্ধ করা হয়েছে।", "INFO")

    if m3u8_link:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(m3u8_link)
        log(f"M3U8 লিংক সফলভাবে {OUTPUT_FILE} ফাইলে সেভ করা হয়েছে।", "SUCCESS")
    else:
        log("টার্গেট পেজ থেকে M3U8 লিংক সংগ্রহ করা সম্ভব হয়নি।", "ERROR")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("NOT_FOUND")

if __name__ == "__main__":
    main()
