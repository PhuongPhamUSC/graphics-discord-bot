import discord
from discord.ext import commands
from discord.ext import tasks
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

token = os.environ.get("DISCORD_TOKEN")
channel_id = os.environ.get("DISCORD_CHANNEL_ID")
wait_time = os.environ.get("WAIT_TIME")
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_news():
    response = supabase.table('NEWS_SOURCES').select("*").execute()
    
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

        # For example, let's extract all the links on the page using BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a')
        
        # Take top x valid links in this site
        link_count = 0
        for link in links:
            href = link.get('href')
            if href and (href not in total_links) and (page["base_url"] + href not in total_links):
                match = (year_pattern.search(href) or publication_pattern.search(href))
                if match:
                    link_count += 1
                    if page["base_url"] in href: # Check if the link contains base url
                        total_links.append(href)
                    else:
                        total_links.append(page["base_url"] + href)
            if link_count == 2:    
                break
    driver.quit()
    print("Done scraping with BeautifulSoup " + str(len(total_links)) + " links found")
    return total_links


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # an attribute we can access from our task
        self.news_links = []

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    @tasks.loop(seconds=600000)  # task runs every x seconds
    async def my_background_task(self):
        channel = self.get_channel(1192747299974156350) # test channel ID
        links_list = get_news()
        if links_list.count > 0:
            # Concatenate all links into a single string
            links_string = '\n'.join(links_list)
            # Send the concatenated string as a message
            await channel.send(links_string)

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in

client = MyClient(intents=discord.Intents.default())
client.run(token)