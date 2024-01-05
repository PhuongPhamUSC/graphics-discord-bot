from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

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

url = 'https://www.animationmagazine.net'

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
page_source = driver.page_source

# Use BeautifulSoup to parse the page source
soup = BeautifulSoup(page_source, 'html.parser')

# Now you can use BeautifulSoup as usual to extract information from the page
# For example:
# title = soup.title.text
# print(title)
links = soup.find_all('a')
for link in links:
    href = link.get('href')
    if href:
        print("LINK: " + href)

# Close the browser
driver.quit()
