import undetected_chromedriver as uc
import time
import re
from flask import Flask
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

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

        # === Set up Headless Chrome ===
        options = uc.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        driver = uc.Chrome(options=options)

        # === Loop Through URLs ===
        for index, url in enumerate(urls, start=2):
            print(f"🌐 Row {index}: {url}")
            driver.get(url)
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            rating = "N/A"
            try:
                # Option 1: Look for "out of 5" text
                rating_elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'out of 5')]"))
                )
                raw_text = rating_elem.text.strip()
                match = re.search(r'(\d\.\d{1,2})\s+out of 5', raw_text)
                if match:
                    rating = match.group(1)
            except:
                pass

            if rating == "N/A":
                try:
                    # Option 2: Fallback regex from full HTML
                    html = driver.page_source
                    match = re.search(r'★?\s*(\d\.\d{1,2})\s*[·•]\s*\d+\s+reviews', html)
                    if match:
                        rating = match.group(1)
                except:
                    pass

            print(f"✅ Final Rating: {rating}")
            sheet.update_cell(index, 2, rating)

        driver.quit()
        print("🎉 All ratings updated.")
        return "✅ Scraping complete."

    except Exception as err:
        print(f"[ERROR] {err}")
        return f"❌ Error: {err}", 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
