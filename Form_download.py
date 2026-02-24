import os
import time
import logging
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
import requests


import shutil
import glob

def wait_and_move_downloaded_file(dest_folder, timeout=3):
    # end_time = time.time() + timeout
    # while time.time() < end_time:
    #     # Check for any .crdownload (incomplete) files
    #     part_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.crdownload"))
    #     if part_files:
    #         time.sleep(0.5)
    #         continue
    time.sleep(timeout)

        # Get latest PDF in the default download folder
    pdf_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.pdf"))
    if pdf_files:
        latest_file = max(pdf_files, key=os.path.getctime)
        filename, ext = os.path.splitext(os.path.basename(latest_file))
        new_filename = f"{filename}_form{ext}"
        shutil.move(latest_file, os.path.join(dest_folder, new_filename))
        print(f"Moved {new_filename} PDF to {dest_folder}")
        return True
    print("Timeout waiting for PDF download")
    return False

# ========================
# CONFIGURATION
# ========================
BASE_URL = "https://app.acadoinformatics.com/syllabus/department/login/"
from config import USERNAME, PASSWORD
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

# ========================
# LOGGING SETUP
# ========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ========================
# HELPER FUNCTIONS
# ========================
def sanitize_filename(name):
    """Remove or replace invalid characters for folder/file names."""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

def wait_for_downloads_complete(download_path):
    """Wait until all Chrome temporary download files are gone."""
    while True:
        time.sleep(1)
        if not any(fname.endswith(".crdownload") for fname in os.listdir(download_path)):
            break

def download_file(url, save_path):
    """Download a file via requests with error handling."""
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        logging.info(f"Downloaded: {save_path}")
    except Exception as e:
        logging.error(f"Failed to download {url} -> {e}")

# ========================
# SELENIUM SETUP
# ========================
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()

# ========================
# LOGIN
# ========================
driver.get(BASE_URL)
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(USERNAME)
driver.find_element(By.NAME, "password").send_keys(PASSWORD)
driver.find_element(By.XPATH, "//button[contains(text(),'Log In')]").click()

# ========================
# NAVIGATE TO "Consolidated Merit Review"
# ========================
WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Consolidated Merit Review"))
).click()

# ========================
# ITERATE THROUGH YEAR × SCHOOL
# ========================
year_dropdown = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "select-year")))
school_dropdown = driver.find_element(By.ID, "select-program")
# print (year_dropdown)
# print (school_dropdown)
year_options = [y.get_attribute("value") for y in year_dropdown.find_elements(By.TAG_NAME, "option") if y.get_attribute("value")]
school_options = [s.get_attribute("value") for s in school_dropdown.find_elements(By.TAG_NAME, "option") if s.get_attribute("value")]

for year in year_options:
    for school in school_options:
        logging.info(f"Processing School: {school}, Year: {year}")

        # Select dropdowns
        time.sleep(3)
        year_dropdown = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "select-year")))
        school_dropdown = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "select-program")))
        Select(year_dropdown).select_by_value(year)
        Select(school_dropdown).select_by_value(school)
        time.sleep(3)


        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            if not rows:
                logging.info(f"No data found for School/year: {school}, Year: {year}")
                continue

        except:
            continue

        for row in rows:
            try:
                faculty_name = sanitize_filename(row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip())
                file_links = row.find_elements(By.CSS_SELECTOR, "a")
                status_text = row.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
                print (faculty_name)
                print (status_text.lower()[0:9])
                # Prepare save folder
                faculty_folder = os.path.join(DOWNLOAD_DIR, sanitize_filename(school), sanitize_filename(year), faculty_name)
                os.makedirs(faculty_folder, exist_ok=True)

                for link in file_links:
                    file_url = link.get_attribute("href")
                    if not file_url:
                        continue

                    filename = os.path.basename(urlparse(file_url).path)
                    save_path = os.path.join(faculty_folder, filename)

                    # Download file
                    download_file(file_url, save_path)
                    # print ("Downloaded" , filename)

                if status_text.lower()[0:9] == "submitted":

                    try:
                        # Find the form link (adjust selector if needed)
                        form_link = row.find_element(By.CSS_SELECTOR, "td:nth-child(3) a")
                        # driver.execute_script("window.open(arguments[0], '_blank');", form_link.get_attribute("href"))
                        form_url = form_link.get_attribute("href")
                        driver.execute_script("window.open(arguments[0], '_blank');", form_url)

                        # Switch to new tab
                        driver.switch_to.window(driver.window_handles[-1])

                        # Wait for Date and Sign tab and click it
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Date and Sign')]"))
                        ).click()

                        time.sleep(1)

                        # Wait for Download Previous PDF button and click it
                        pdf_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Download Previous PDF')]"))
                        )
                        pdf_button.click()

                        wait_and_move_downloaded_file(faculty_folder, timeout=3)

                        # Give browser time to download
                        time.sleep(1)  

                    except Exception as form_err:
                        logging.error(f"Error downloading form PDF for {faculty_name}: {form_err}")

                    finally:
                        # Close the form tab and switch back
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                else:
                    continue


            except Exception as e:
                logging.error(f"Error processing row: {e}")

driver.quit()
