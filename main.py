from urllib.request import urlopen
import requests
from datetime import datetime, timedelta
import re

# Get the current year
current_year = datetime.now().year

# Get the past two years
past_years = [current_year - i for i in range(3)]

# Create a regex pattern
year_pattern = re.compile(r'\b(?:{}|{})\b'.format(current_year, '|'.join(map(str, past_years))))

# Pages to scrape
urls = ["https://news.mit.edu/topic/computer-graphics", 
        "https://www.sciencedaily.com/news/computers_math/computer_graphics/", 
        "https://www.cgrecord.net/", 
        "https://www.cgw.com/Press-Center.aspx"]
HEADERS = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}

# Scraping with beautiful soup
with open('links.txt', 'w') as file:
    for url in urls:
        response = requests.get(url, headers=HEADERS)
        file.write(f"URL: {url}\n")

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Access the content of the page
            content = response.text
            
            # Here you can use regular expressions, string manipulation, or a parsing library like BeautifulSoup to extract data
            # For example, let's extract all the links on the page using BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            links = soup.find_all('a')

            for link in links:
                href = link.get('href')
                if href:
                    match = year_pattern.search(href)
                    if match:
                        file.write(href + '\n')

        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
    
    file.close()