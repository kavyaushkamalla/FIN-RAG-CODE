
# Import Required Libraries

import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# OLD Scraper Function: Wait for specific table
def scrape_website_old(wesite):
    print("Launching chrome browser...")

    # Define ChromeDriver path
    chrome_driver_path = "./chromedriver.exe"

    # Headless option for background execution
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")

    # Launch browser with options
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    try:
        # Navigate to website
        driver.get(wesite)
        print("Waiting for subscription table to load...")

        try:
            # Wait until a table with "Investor Category" is present
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//table[contains(., 'Investor Category')]"))
            )
            print("Table detected, collecting page source...")
        except:
            print("Timeout: Could not detect expected content.")
            # Save page source for debugging
            with open("failed_page_dump.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise

        # Return page HTML
        html = driver.page_source
        return html

    finally:
        driver.quit()  # Close browser


# Newer Scraper: Scroll page and capture HTML

def scrape_website(wesite):
    print("Launcing chrome browser...")

    # Define ChromeDriver path
    chrome_driver_path = "./chromedriver.exe"

    # Set Chrome options
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless=new")  # Enable for headless mode
    #options.add_argument("--disable-gpu")   # Optional GPU disable
    options.add_argument("--window-size=1920,1080")  # Full screen size

    # Launch browser with options
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    try:
        # Load the website
        driver.get(wesite)
        print("page loaded...")

        # Scroll to bottom to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Wait for content to load

        # Get the HTML
        html = driver.page_source
        time.sleep(5)  # Give time for JS to finish

        # Save page source for debug
        with open("failed_page_dump.html", "w", encoding="utf-8") as f:
            f.write(html)

        return html

    finally:
        driver.quit()  # Close browser

# ?? Extract only <body> from full HTML content

def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""

# Old Cleaner: Strip scripts/styles and get text only

def clean_body_content_old(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    # Remove noisy tags
    for script_or_style in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        script_or_style.extract()

    # Get visible text
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(line.strip() for line in cleaned_content.splitlines() if line.strip())

    return cleaned_content

# Improved Cleaner: Keep tables + better formatted text
def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    # Remove noisy, non-content elements
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()

    text_parts = []

    # 1?? Extract readable visible text
    visible_text = soup.get_text(separator="\n", strip=True)
    visible_text = "\n".join(line.strip() for line in visible_text.splitlines() if line.strip())
    text_parts.append("== Text Content ==\n" + visible_text)

    # 2?? Extract and format all tables
    tables = soup.find_all("table")
    for idx, table in enumerate(tables, start=1):
        rows = []
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            cell_text = [cell.get_text(strip=True) for cell in cells]
            if cell_text:
                rows.append("\t".join(cell_text))
        if rows:
            text_parts.append(f"\n== Table {idx} ==\n" + "\n".join(rows))

    return "\n\n".join(text_parts)


#  Utility: Split large content into smaller chunks
def split_dom_content(dom_content, max_length=6000):
    return [
        dom_content[i:i+max_length] for i in range(0, len(dom_content), max_length)
    ]

    ]

