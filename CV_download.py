import os
import time
import urllib.request
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIG ===
LOGIN_URL = "https://app.acadoinformatics.com/syllabus/department/login/"
from config import USERNAME, PASSWORD
DOWNLOAD_DIR = os.path.expanduser("~/Downloads")

# === SETUP DRIVER ===
options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "plugins.always_open_pdf_externally": True
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(LOGIN_URL)
time.sleep(2)

# === LOGIN STEP ===
driver.find_element(By.NAME, "username").send_keys(USERNAME)
driver.find_element(By.NAME, "password").send_keys(PASSWORD)
driver.find_element(By.XPATH, "//button[contains(text(), 'Log In')]").click()
time.sleep(3)

# === CLICK 'View CV/Bio/Resume Files' LINK ===
driver.find_element(By.LINK_TEXT, "View CV/Bio/Resume Files").click()
time.sleep(3)

# (wait_for_download removed in favor of direct urllib download)


# === SORT BY FIRST NAME ===
try:
    first_name_header = driver.find_element(By.XPATH, "//th[contains(text(), 'First Name')]")
    first_name_header.click()
    time.sleep(2)
except Exception as e:
    print(f"❌ Could not click First Name header: {e}")

# === BUILD LATEST RECORD DICT ===
rows = driver.find_elements(By.XPATH, "//table/tbody/tr")
latest_entries = {}

for row in rows:
    try:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) < 5:
            continue

        last_name = cells[0].text.strip()
        first_name = cells[1].text.strip()
        date_uploaded = cells[3].text.strip()
        view_link = cells[4].find_element(By.TAG_NAME, "a")

        key = (first_name.lower(), last_name.lower())

        # Replace if newer
        if key not in latest_entries or date_uploaded > latest_entries[key][1]:
            latest_entries[key] = (row, date_uploaded)

    except Exception as e:
        print(f"⚠️ Error parsing row: {e}")

# === PRINT LATEST ENTRIES BEFORE DOWNLOAD ===
print("\n🗂️ Latest Entries (to be downloaded):")
for (first_name, last_name), (_, date_uploaded) in latest_entries.items():
    print(f"- {first_name.title()} {last_name.title()} | Date: {date_uploaded}")
print(f"\nTotal unique entries to download: {len(latest_entries)}\n")

xyx=input("Hit enter to start downloading")

# === DOWNLOAD ONLY LATEST PER PERSON ===
for (first_name, last_name), (row, date_uploaded) in latest_entries.items():
    try:
        cells = row.find_elements(By.TAG_NAME, "td")
        view_link = cells[4].find_element(By.TAG_NAME, "a")

        file_url = view_link.get_attribute("href")
        
        # Determine extension from URL
        filename = os.path.basename(urlparse(file_url).path)
        _, ext = os.path.splitext(filename)
        if not ext:
            ext = ".pdf"
            
        new_name = f"{first_name}_{last_name}_{date_uploaded}_cv{ext}"
        new_path = os.path.join(DOWNLOAD_DIR, new_name)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                urllib.request.urlretrieve(file_url, new_path)
                print(f"✅ Downloaded latest for {first_name} {last_name}: {new_name}")
                break
            except Exception as download_err:
                if attempt < max_retries - 1:
                    print(f"   ⚠️ Download failed ({download_err}). Retrying {attempt + 1}/{max_retries}...")
                    time.sleep(2)
                else:
                    raise download_err

    except Exception as e:
        print(f"❌ Failed for {first_name} {last_name} ({date_uploaded}): {e}")
