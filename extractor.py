import time
import sys
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    log("Cloudflare এবং Bot Detection বাইপাস করার জন্য Undetected-Chromedriver ব্রাউজার শুরু করা হচ্ছে...", "INFO")
    
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = None
    try:
        # undetected_chromedriver ব্যবহার করে ব্রাউজার ইনিশিয়ালাইজ করা
        driver = uc.Chrome(options=options, use_subprocess=True)
        log("Undetected ব্রাউজার ইনস্ট্যান্স সফলভাবে তৈরি হয়েছে।", "SUCCESS")
        
        log(f"লিংকে প্রবেশ করা হচ্ছে: {url}", "INFO")
        driver.get(url)
        
        # ক্লাউডফায়ার চ্যালেঞ্জ হ্যান্ডেল করার জন্য পর্যাপ্ত সময় অপেক্ষা
        log("ক্লাউডফায়ার সিকিউরিটি চেক ও চ্যালেঞ্জ পাস করার জন্য অপেক্ষা করা হচ্ছে...", "WARNING")
        time.sleep(10)
        
        page_source = driver.page_source
        if "cf-browser-verification" in page_source or "Verifying" in page_source:
            log("ক্লাউডফায়ার ভেরিফিকেশন এখনও চলমান, আরও কিছুটা সময় অপেক্ষা করা হচ্ছে...", "WARNING")
            time.sleep(10)
            log("ক্লাউডফায়ার প্রটেকশন সফলভাবে বাইপাস করা হয়েছে!", "SUCCESS")
        else:
            log("ক্লাউডফায়ার প্রটেকশন সফলভাবে অতিক্রম করা হয়েছে।", "SUCCESS")

        log("ভিডিও প্লেয়ার, স্ক্রিপ্ট এবং স্ট্রিম সোর্স লোড হওয়ার জন্য অপেক্ষা করা হচ্ছে...", "INFO")
        time.sleep(8)

        # ১. সরাসরি পেজ সোর্স বা স্ক্রিপ্ট থেকে m3u8 খোঁজা
        import re
        log("পেজ সোর্সে m3u8 লিংক খোঁজা হচ্ছে...", "INFO")
        matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', driver.page_source)
        if matches:
            m3u8_link = matches[0]
            log(f"সফলভাবে M3U8 লিংক পাওয়া গেছে: {m3u8_link}", "SUCCESS")
        
        # ২. যদি মেইন পেজে না পাওয়া যায়, তবে জাভাস্ক্রিপ্ট বা ডাইনামিক সোর্স চেক করা
        if not m3u8_link:
            log("পেজে সরাসরি লিংক না মেলায় জাভাস্ক্রিপ্ট ভেরিয়েবল বা এক্সিকিউশন চেক করা হচ্ছে...", "WARNING")
            # পেজের সমস্ত script ট্যাগ থেকে লিংক খোঁজা
            scripts = driver.find_elements(By.TAG_NAME, "script")
            for script in scripts:
                script_content = script.get_attribute("innerHTML")
                if script_content and ".m3u8" in script_content:
                    script_matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', script_content)
                    if script_matches:
                        m3u8_link = script_matches[0]
                        log(f"স্ক্রিপ্টের ভেতর থেকে M3U8 লিংক উদ্ধার করা হয়েছে: {m3u8_link}", "SUCCESS")
                        break

        # ৩. আইফ্রেম (Iframe) চেক করা যদি তখনও না মিলে
        if not m3u8_link:
            log("আইফ্রেমগুলোর ভেতর স্ক্যান করা হচ্ছে...", "INFO")
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            log(f"মোট আইফ্রেম পাওয়া গেছে: {len(iframes)}টি", "INFO")
            for index, iframe in enumerate(iframes):
                try:
                    iframe_src = iframe.get_attribute("src")
                    log(f"আইফ্রেম [{index}] সোর্স: {iframe_src}", "INFO")
                    driver.switch_to.frame(iframe)
                    time.sleep(3)
                    
                    iframe_matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', driver.page_source)
                    if iframe_matches:
                        m3u8_link = iframe_matches[0]
                        log(f"আইফ্রেম [{index}] এর ভেতর M3U8 লিংক পাওয়া গেছে: {m3u8_link}", "SUCCESS")
                        driver.switch_to.default_content()
                        break
                    driver.switch_to.default_content()
                except Exception as ex:
                    log(f"আইফ্রেম [{index}] স্ক্যান করার সময় ত্রুটি: {str(ex)}", "WARNING")
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
        log("সকল পদ্ধতি চেষ্টার পরেও টার্গেট পেজ থেকে M3U8 লিংক সংগ্রহ করা সম্ভব হয়নি।", "ERROR")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("NOT_FOUND")

if __name__ == "__main__":
    main()
