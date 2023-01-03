"""
Scrapes trip advisor for the top n=30 attractions in a location and writes
output to a csv file.
"""

import re
import time
import html
import urllib
import urllib.request
import pandas as pd
from bs4 import BeautifulSoup


class TripAdvisorScrape():

    def __init__(self, n=30):
        assert type(n) == int and 1 <= n <= 30, \
            'n is not an integer in {1, 2, ...,30}'
        self.n = n  # number of attractions to scrape (1-30)

    def get_html(self, url):
        time.sleep(5)  # wait 5 seconds
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'
        }
        request = urllib.request.Request(url, None, headers=headers)
        response = urllib.request.urlopen(request)
        html_str = response.read().decode('utf8')
        return html_str

    def scrape(self, location, verbose=True, helper_url=None):
        if helper_url is not None:
            new_url = helper_url
        else:
            # Search trip advisor for location (e.g. 'Toronto, Ontario',
            # or 'Canada') to find the URL I want
            request_url = f"https://www.tripadvisor.com/Search?q={location} things to do"
            request_url = request_url.replace(' ', '%20')
            html_str = self.get_html(request_url)
            # Extract the actual URL that the search sent me to (e.g.
            # 'https://www.tripadvisor.com/Attractions-g155019-Activities-Toronto_Ontario.html')
            soup = BeautifulSoup(html_str, 'html.parser')
            m = soup.head.find_all('meta')
            url = [i.get('content') for i in m if i.get('property') == 'og:url'][0]
            # modify URL to get the full list of attractions in the location (e.g.
            # 'https://www.tripadvisor.com/Attractions-g155019-Activities-a_allAttractions.true')
            pattern = r'https://www\.tripadvisor\.com/Attractions-.*-Activities-'
            new_url = re.match(pattern, url).group(0)
            new_url = new_url + 'a_allAttractions.true'
        # pull html from the new URL
        new_html = self.get_html(new_url)
        # extract attractions from HTML
        df = []
        for i in range(1, self.n + 1):
            # find attraction in HTML code
            pattern = rf'>{i}\.</span> <!-- -->.*?</div>'
            s = re.search(pattern, new_html).group(0)
            # trim off extra text
            s = s.replace(f'>{i}.</span> <!-- -->', '')
            s = s.replace('</div>', '')
            # convert character references to unicode
            s = html.unescape(s)
            # append to df
            d = {
                'Rank': i,
                'Attraction': s
            }
            df.append(d)
            if verbose:
                print(f"{i}. {s}")
        # return scraped results
        df = pd.DataFrame(df)
        return df
