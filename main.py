from urllib.request import urlopen
import requests

urls = ["https://news.mit.edu/topic/computer-graphics", 
        "https://www.sciencedaily.com/news/computers_math/computer_graphics/", 
        "https://www.cgrecord.net/", 
        "https://www.cgw.com/Press-Center.aspx"]
HEADERS = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}

for url in urls:
    response = requests.get(url, headers=HEADERS)
    print(response.status_code)

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
            print(link.get('href'))

    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")