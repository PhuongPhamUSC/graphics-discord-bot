import functools
import typing
import os
import re
import asyncio
from datetime import datetime
import discord
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client

token = os.environ.get("DISCORD_TOKEN")
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)
news_source_list = []

# Set up the browser
woptions = webdriver.ChromeOptions()
woptions.add_argument("--headless")
woptions.add_argument("--no-sandbox")
woptions.add_argument("--disable-dev-shm-usage")
woptions.add_argument("--disable-notifications")
woptions.add_argument('--disable-web-security')
woptions.add_argument("--ignore-certificate-errors-spki-list")
woptions.add_argument("--ignore-certificate-errors")
woptions.add_argument("--ignore-ssl-errors")
woptions.add_argument("--allow-insecure-localhost")
woptions.add_argument("--ignore-urlfetcher-cert-requests")
# Driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=woptions)

def to_thread(func: typing.Callable) -> typing.Coroutine:

  @functools.wraps(func)
  async def wrapper(*args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)

  return wrapper


@to_thread
def get_news():
  # empty news source list
  news_source_list.clear()

  # Get the past 2 years
  current_year = datetime.now().year
  past_years = [current_year - i for i in range(3)]

  # Create a regex pattern
  year_pattern = re.compile(r'\b(?:{}|{})\b'.format(
      current_year, '|'.join(map(str, past_years))))
  file_ext_pattern = re.compile(r'\.(htm|html|aspx)$')
  publication_pattern = re.compile(r'\d{4}/\d{2}/\d{2}')

  # Scraping with beautiful soup
  total_links = []
  response = supabase.table('NEWS_SOURCES').select("*").execute()
  for page in response.data:
    url = page["base_url"] + page["directory"]

    # Load the page
    driver.get(url)

    # Wait for dynamically loaded content to appear (adjust the timeout as needed)
    timeout = 20
    try:
      links_present = EC.presence_of_element_located(
          (By.CSS_SELECTOR, '[href]'))
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
    link_set = set()
    for link in links:
      href = link.get('href')
      if href and (href not in total_links) and (page["base_url"] + href
                                                 not in total_links):
        match = "topic" not in href and (year_pattern.search(href)
                                         or publication_pattern.search(href))
        if match:
          link_count += 1
          if page["base_url"] in href:  # Check if the link contains base url
            link_set.add(href)
          else:
            link_set.add(page["base_url"] + href)
      if len(link_set) == 5:
        news_source_list.append(page["name"])
        total_links.append(link_set)
        break
  driver.quit()
  return total_links


class MyClient(discord.Client):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  async def on_ready(self):
    print(f'Logged in as {self.user} (ID: {self.user.id})')
    print('------')
    # start the background task
    await self.my_background_task()

  async def on_guild_join(self, guild):
    print("Joining guild: " + guild.name)

  async def on_message(self, message):
    # we do not want the bot to reply to itself
    if message.author.id == self.user.id:
      return

    if message.content.startswith('!hello'):
      await message.reply('Hello!', mention_author=True)

    if message.content.startswith('!start news'):
      # if task has not started
      if not self.my_background_task.is_running():
        self.my_background_task.start()
        await message.reply('News started!', mention_author=True)
      else:
        await message.reply('News already started!', mention_author=True)

    if message.content.startswith('!add channel'):
      channel = message.channel
      supabase.table('JOINED_CHANNELS').insert({"id": channel.id}).execute()
      await channel.send("Channel subscribed")

    if message.content.startswith('!remove channel'):
      channel = message.channel
      supabase.table('JOINED_CHANNELS').delete().eq('id', channel.id).execute()
      await channel.send("Channel unsubscribed")

  # @tasks.loop(seconds=300000)  # task runs every x seconds
  async def my_background_task(self):
    response = supabase.table('JOINED_CHANNELS').select("*").execute()
    for chan in response.data:
      channel = self.get_channel(chan["id"])  # test channel ID
      links_list = await get_news()
      if len(links_list) > 0:
        # for every 5 links, send in one message
        for i in range(0, len(links_list)):
          links_string = news_source_list[i] + '\n' + '\n'.join(links_list[i])
          await channel.send(links_string)

  # @my_background_task.before_loop
  # async def before_my_task(self):
  #   await self.wait_until_ready()


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(token)
