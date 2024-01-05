import re
import codecs
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Set up the browser
woptions = webdriver.ChromeOptions()
woptions.add_argument("--headless")
woptions.add_argument("--disable-notifications")
woptions.add_argument('--disable-web-security')
woptions.add_argument("--ignore-certificate-errors-spki-list")
woptions.add_argument("--ignore-certificate-errors")
woptions.add_argument("--ignore-ssl-errors")
woptions.add_argument("--allow-insecure-localhost")
woptions.add_argument("--ignore-urlfetcher-cert-requests")
driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=woptions)

# Get the current year
current_year = datetime.now().year

# Get the past two years
past_years = [current_year - i for i in range(3)]

# Create a regex pattern
year_pattern = re.compile(r'\b(?:{}|{})\b'.format(current_year, '|'.join(map(str, past_years))))
publication_pattern = re.compile(r'\d{4}/\d{2}/\d{2}')

# Class for pages
class Page:
    def __init__(self, site_name, url, directory, date):
        self.site_name = site_name
        self.url = url
        self.directory = directory
        self.date = date

    def __str__(self):
        return f"URL: {self.url}\nDate: {self.date}\n"

    def __repr__(self):
        return f"URL: {self.url}\nDate: {self.date}\n"

# Pages to scrape
pages = []
pages.append(Page("MIT News", "https://news.mit.edu", "/topic/computer-graphics", datetime.now()))
pages.append(Page("Science Daily", "https://www.sciencedaily.com", "/news/computers_math/computer_graphics", datetime.now()))
pages.append(Page("Computer Graphics World", "https://www.cgw.com/", "Press-Center", datetime.now()))
pages.append(Page("Phys Org", "", "https://phys.org/tags/computer+graphics", datetime.now()))
pages.append(Page("IEEE Spectrum", "https://spectrum.ieee.org", "/magazine", datetime.now()))
pages.append(Page("Animation Magazine", "https://www.animationmagazine.net", "/category/vfx", datetime.now()))
pages.append(Page("The Journal of Computer Graphics Technique", "https://jcgt.org", "", datetime.now()))

# Scraping with beautiful soup
with open('links.txt', 'w') as file:
    for page in pages:
        url = page.url + page.directory
        
        # Load the page
        driver.get(url)

        # Wait for dynamically loaded content to appear (adjust the timeout as needed)
        timeout = 10
        try:
            links_present = EC.presence_of_element_located((By.CSS_SELECTOR, '[href]'))
            WebDriverWait(driver, timeout).until(links_present)
        except Exception:
            print("Timed out waiting for page to load")

        # Get the page source after dynamic content has loaded
        content = driver.page_source
        file.write(f"{page.site_name}: {url}\n")

        # For example, let's extract all the links on the page using BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        print(soup.prettify())
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            if href:
                match = year_pattern.search(href) or publication_pattern.search(href)
                if match:
                    if page.url in href: # Check if the link contains base url
                        file.write(href + '\n')
                    else:
                        file.write(page.url + href + '\n')
    driver.quit()
    file.close()
    print("Done scraping with BeautifulSoup")