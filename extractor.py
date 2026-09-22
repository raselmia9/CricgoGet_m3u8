import time
import sys
import cloudscraper
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

STATUS_FILE = "status.txt"
OUTPUT_FILE = "m3u8_link.txt"

def log(message, level="INFO"):
    # লেভেল অনুযায়ী কালার ও ইমোজি চিহ্ন: INFO (🔵), SUCCESS (🟢), WARNING (🟡), ERROR (🔴)
    icons = {
        "INFO": "🔵 [INFO]",
        "SUCCESS": "🟢 [SUCCESS]",
        "WARNING": "🟡 [WARNING]",
        "ERROR": "🔴 [ERROR]"
    }
    formatted = f"{icons.get(level, '🔹')} {time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n"
    print(formatted.strip())
    with open(STATUS_FILE, "a", encoding="utf-8") as f:
        f.write(formatted)

def main():
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("=== CRICGO M3U8 EXTRACTOR STATUS LOG ===\n")
    
    url = "https://cricgo.cc/player.php?id=willow"
    log(f"টার্গেট ইউআরএল সেটআপ সফল হয়েছে: {url}", "INFO")
    
    m3u8_link = None

    log("ক্লাউডফায়ার প্রটেকশন বাইপাস করার জন্য Selenium হেডলেস ব্রাউজার শুরু করা হচ্ছে...", "INFO")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        log("ব্রাউজার ইনস্ট্যান্স সফলভাবে তৈরি হয়েছে।", "SUCCESS")
        
        log(f"লিংকে প্রবেশ করা হচ্ছে: {url}", "INFO")
        driver.get(url)
        
        # ক্লাউডফায়ার সিকিউরিটি চেক ডিটেকশন
        time.sleep(5)
        page_source = driver.page_source
        if "cf-browser-verification" in page_source or "Verifying" in page_source or "Cloudflare" in page_source:
            log("ক্লাউডফায়ার সিকিউরিটি ভেরিফিকেশন (Cloudflare Challenge) সনাক্ত হয়েছে! বাইপাস করার চেষ্টা চলছে...", "WARNING")
            try:
                WebDriverWait(driver, 20).until(
                    lambda d: "Verifying" not in d.page_source and "cf-browser-verification" not in d.page_source
                )
                log("ক্লাউডফায়ার প্রটেকশন সফলভাবে বাইপাস করা হয়েছে!", "SUCCESS")
            except Exception as e:
                log(f"ক্লাউডফায়ার চ্যালেঞ্জের সময়সীমা পার হয়ে গেছে বা ব্লক অব্যাহত আছে: {str(e)}", "ERROR")
        else:
            log("কোনো দৃশ্যমান ক্লাউডফায়ার ব্লকিং নেই অথবা দ্রুত বাইপাস হয়ে গেছে।", "SUCCESS")

        log("ভিডিও প্লেয়ার ও স্ট্রিম সোর্স লোড হওয়ার জন্য অপেক্ষা করা হচ্ছে...", "INFO")
        time.sleep(7)

        # পেজ সোর্স থেকে m3u8 খোঁজা
        if ".m3u8" in driver.page_source:
            log("পেজ সোর্সে m3u8 প্যাটার্ন পাওয়া গেছে।", "SUCCESS")
            import re
            matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', driver.page_source)
            if matches:
                m3u8_link = matches[0]
                log(f"এক্সট্রাক্টকৃত M3U8 লিংক: {m3u8_link}", "SUCCESS")
        
        # যদি মেইন পেজে না পাওয়া যায়, তবে আইফ্রেম (Iframe) চেক করা
        if not m3u8_link:
            log("আইফ্রেমগুলোর ভেতর খোঁজা হচ্ছে...", "INFO")
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            log(f"মোট আইফ্রেম পাওয়া গেছে: {len(iframes)}টি", "INFO")
            for index, iframe in enumerate(iframes):
                try:
                    iframe_src = iframe.get_attribute("src")
                    log(f"আইফ্রেম [{index}] চেক করা হচ্ছে: {iframe_src}", "INFO")
                    driver.switch_to.frame(iframe)
                    time.sleep(3)
                    if ".m3u8" in driver.page_source:
                        import re
                        matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', driver.page_source)
                        if matches:
                            m3u8_link = matches[0]
                            log(f"আইফ্রেম [{index}] এর ভেতর M3U8 লিংক পাওয়া গেছে: {m3u8_link}", "SUCCESS")
                            driver.switch_to.default_content()
                            break
                    driver.switch_to.default_content()
                except Exception as ex:
                    log(f"আইফ্রেম [{index}] চেক করার সময় ত্রুটি: {str(ex)}", "WARNING")
                    driver.switch_to.default_content()

    except Exception as e:
        err_msg = str(e)
        log(f"ব্রাউজার অটোমেশনে মারাত্মক ত্রুটি ঘটেছে: {err_msg}", "ERROR")
    finally:
        if driver:
            driver.quit()
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
