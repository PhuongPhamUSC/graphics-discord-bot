import os
import re
import codecs
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from fake_useragent import UserAgent
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client

def get_news():
    # Set up Supabase
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    response = supabase.table('NEWS_SOURCES').select("*").execute()

    # Set up the user agent
    ua = UserAgent()
    user_agent = ua.random
    
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

    # Get the past 2 years
    current_year = datetime.now().year
    past_years = [current_year - i for i in range(3)]

    # Create a regex pattern
    year_pattern = re.compile(r'\b(?:{}|{})\b'.format(current_year, '|'.join(map(str, past_years))))
    publication_pattern = re.compile(r'\d{4}/\d{2}/\d{2}')

    # Scraping with beautiful soup
    total_links = []
    
    for page in response.data:
        url = page["base_url"] + page["directory"]
        
        # Load the page
        driver.get(url)

        # Wait for dynamically loaded content to appear (adjust the timeout as needed)
        timeout = 20
        try:
            links_present = EC.presence_of_element_located((By.CSS_SELECTOR, '[href]'))
            WebDriverWait(driver, timeout).until(links_present)
        except Exception:
            print("Timed out waiting for page to load")

        # Get the page source after dynamic content has loaded
        content = driver.page_source
        # file.write(f"{page["name"]}: {url}\n")

        # For example, let's extract all the links on the page using BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        # cap links at top 10
        links = soup.find_all('a')
        
        # Take top 10 links in this site
        link_count = 0
        for link in links:
            href = link.get('href')
            if href:
                match = year_pattern.search(href) or publication_pattern.search(href)
                if match:
                    link_count += 1
                    if page["base_url"] in href: # Check if the link contains base url
                        total_links.append(href)
                    else:
                        total_links.append(page["base_url"] + href)
            if link_count == 5:    
                break
    driver.quit()
    print("Done scraping with BeautifulSoup " + str(len(total_links)) + " links found")
    return total_links

# Run the function
get_news()