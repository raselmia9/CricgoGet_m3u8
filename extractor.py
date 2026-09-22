import time
import sys
from playwright.sync_api import sync_playwright

STATUS_FILE = "status.txt"
OUTPUT_FILE = "m3u8_link.txt"

def log(message, level="INFO"):
    # স্ট্যাটাস থেকে তারিখ ও সময় বাদ দিয়ে শুধু ইমোজি ও মেসেজ রাখা হয়েছে
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

    log("Playwright ব্রাউজার এবং হিউম্যান প্রটেকশন বাইপাস মোড ইনিশিয়ালাইজ করা হচ্ছে...", "INFO")
    
    with sync_playwright() as p:
        # ক্লাউডফায়ার ডিটেকশন এড়াতে ব্রাউজার আর্গুমেন্টস কনফিগার করা
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu"
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            has_touch=False,
            is_mobile=False
        )
        
        page = context.new_page()

        # বোট সিগনেচার লুকাতে জাভাস্ক্রিপ্ট প্রপার্টি ওভাররাইড করা
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # নেটওয়ার্ক রিকোয়েস্ট লিসেনার (m3u8 লিংক ধরার জন্য)
        def intercept_request(request):
            nonlocal m3u8_link
            if ".m3u8" in request.url:
                if not m3u8_link:
                    m3u8_link = request.url
                    log(f"নেটওয়ার্ক ট্রাফিক থেকে M3U8 লিংক ক্যাপচার করা হয়েছে: {m3u8_link}", "SUCCESS")

        page.on("request", intercept_request)

        try:
            log(f"টার্গেট লিংকে প্রবেশ করা হচ্ছে: {url}", "INFO")
            page.goto(url, timeout=60000)
            
            # হিউম্যান ভেরিফিকেশন বা ক্লাউডফায়ার চ্যালেঞ্জ পাস করার জন্য পর্যাপ্ত সময় ও সিমুলেশন
            log("ক্লাউডফায়ার হিউম্যান প্রটেকশন ও সিকিউরিটি চ্যালেঞ্জ চেক করা হচ্ছে...", "WARNING")
            
            # পেজে রিয়েল ইউজারের মতো মাউস মুভমেন্ট বা ক্লিক সিমুলেট করা যাতে ভেরিফিকেশন পাস হয়
            time.sleep(5)
            try:
                page.mouse.move(200, 300)
                page.mouse.click(200, 300)
            except:
                pass

            # চ্যালেঞ্জ সলভ হওয়ার জন্য ১০-১৫ সেকেন্ড অপেক্ষা
            time.sleep(12)

            # পেজ টাইটেল বা সোর্স চেক করে দেখা যে ক্লাউডফায়ার ব্লক পেজ পার হয়েছে কি না
            page_content = page.content()
            if "Cloudflare" in page_content or "Verifying" in page_content or "cf-browser-verification" in page_content:
                log("ক্লাউডফায়ার হিউম্যান ভেরিফিকেশন চ্যালেঞ্জ এখনো টিকে আছে, অতিরিক্ত সময় অপেক্ষা করা হচ্ছে...", "WARNING")
                time.sleep(15)
            else:
                log("ক্লাউডফায়ার হিউম্যান প্রটেকশন সফলভাবে বাইপাস করা হয়েছে!", "SUCCESS")

            log("ভিডিও প্লেয়ার এবং স্ট্রিম রিকোয়েস্ট লোড হওয়ার জন্য অপেক্ষা করা হচ্ছে...", "INFO")
            
            # যদি সরাসরি নেটওয়ার্কে না ধরে, তবে ফ্রেম ও পেজ সোর্স স্ক্যান করা
            for _ in range(15):
                if m3u8_link:
                    break
                time.sleep(2)
                
                # ফ্রেমগুলো চেক করা
                for frame in page.frames:
                    try:
                        frame_content = frame.content()
                        if ".m3u8" in frame_content:
                            import re
                            matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', frame_content)
                            if matches:
                                m3u8_link = matches[0]
                                log(f"আইফ্রেমের ভেতর থেকে M3U8 লিংক উদ্ধার করা হয়েছে: {m3u8_link}", "SUCCESS")
                                break
                    except:
                        pass

        except Exception as e:
            err_msg = str(e)
            log(f"অটোমেশনে মারাত্মক ত্রুটি ঘটেছে: {err_msg}", "ERROR")
        finally:
            browser.close()
            log("ব্রাউজার সেশন সফলভাবে বন্ধ করা হয়েছে।", "INFO")

    if m3u8_link:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(m3u8_link)
        log(f"M3U8 লিংক সফলভাবে {OUTPUT_FILE} ফাইলে সেভ করা হয়েছে।", "SUCCESS")
    else:
        log("হিউম্যান প্রটেকশন বাইপাসের পর টার্গেট পেজ থেকে M3U8 লিংক সংগ্রহ করা সম্ভব হয়নি।", "ERROR")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("NOT_FOUND")

if __name__ == "__main__":
    main()
