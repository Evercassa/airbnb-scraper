import os
import time
import re
import traceback
from flask import Flask
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

@app.route('/')
def home():
    return '✅ Service is up. Visit /run to start scraping.'

@app.route('/run', methods=['GET'])
def run_scraper():
    try:
        # === Google Sheets Auth ===
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Supervisor Noel").worksheet("Reviews")
        print("✅ Connected to Google Sheet.")

        # === Get URLs from Column C ===
        urls = sheet.col_values(3)[1:]
        urls = [url.strip() for url in urls if url.strip()]
        print(f"🔎 Found {len(urls)} URLs.")

        # === Install compatible ChromeDriver and set binary ===
        chromedriver_autoinstaller.install()
        chrome_path = '/usr/bin/google-chrome'  # Or '/usr/bin/chromium-browser' depending on Render
        print(f"🧭 Using Chrome binary at: {chrome_path}")

        options = webdriver.ChromeOptions()
        options.binary_location = chrome_path
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')

        driver = webdriver.Chrome(options=options)

        # === Loop Through URLs ===
        for index, url in enumerate(urls, start=2):
            print(f"🌐 Row {index}: {url}")
            driver.get(url)
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            rating = "N/A"
            try:
                rating_elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'out of 5')]"))
                )
                raw_text = rating_elem.text.strip()
                match = re.search(r'(\d\.\d{1,2})\s+out of 5', raw_text)
                if match:
                    rating = match.group(1)
            except Exception as e:
                print(f"⚠️ First method failed: {e}")

            if rating == "N/A":
                try:
                    html = driver.page_source
                    match = re.search(r'★?\s*(\d\.\d{1,2})\s*[·•]\s*\d+\s+reviews', html)
                    if match:
                        rating = match.group(1)
                except Exception as e:
                    print(f"⚠️ Fallback method failed: {e}")

            print(f"✅ Final Rating: {rating}")
            sheet.update_cell(index, 2, rating)

        driver.quit()
        print("🎉 All ratings updated.")
        return "✅ Scraping complete."

    except Exception as err:
        print("❌ ERROR OCCURRED:")
        traceback.print_exc()  # This shows the full traceback in Render logs
        return f"❌ Error: {err}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
