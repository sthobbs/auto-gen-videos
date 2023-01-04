import os
import urllib.request
import urllib
import imghdr
import posixpath
import re
import time

"""
Python api to download image form Bing.
Original Author: Guru Prasad (g.gaurav541@gmail.com)
Modified by: Steve Hobbs (github.com/sthobbs)
"""


class Bing:
    """Bing image downloader class."""

    def __init__(self, query, limit, output_dir, adult, timeout, filters='',
                 query_folder=True, extra_query=''):
        """
        Parameters
        ----------
        query : str
            the query to search for.
        limit : int
            the number of images to download.
        output_dir : str
            the directory to save the images to.
        adult : bool
            whether to include adult images.
        timeout : int
            the timeout for the request.
        filters : str
            the filters to apply to the search.
        query_folder : bool
            whether to put the images in a folder named after the query.
        extra_query : str
            extra query to append to the search that don't impact
            the output file name.
        """

        self.query = query
        self.limit = limit
        self.output_dir = output_dir
        self.adult = adult
        self.timeout = timeout
        self.filters = filters
        self.query_folder = query_folder  # folder to put all images into
        # add in extra query words that don't impact output location
        if extra_query != '':
            self.extra_query = ' ' + extra_query
        else:
            self.extra_query = extra_query
        self.download_count = 0
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'}
        self.page_counter = 1

        assert not (not query_folder and limit != 1), \
            "if query_folder==False, then limit must be 1"
        assert type(limit) == int, "limit must be integer"
        assert type(timeout) == int, "timeout must be integer"

    def save_image(self, link, file_path):
        """
        Saves the image from the link to the file_path.

        Parameters
        ----------
        link : str
            the link to the image
        file_path : str
            the path to save the image to
        """

        request = urllib.request.Request(link, None, self.headers)
        image = urllib.request.urlopen(request, timeout=self.timeout).read()
        if not imghdr.what(None, image):
            print(f'[Error]Invalid image, not saving {link}\n')
            raise
        with open(file_path, 'wb') as f:
            f.write(image)

    def download_image(self, link):
        """
        Downloads the image from the link.

        Parameters
        ----------
        link : str
            the link to the image
        """

        self.download_count += 1

        # Get the image link
        try:
            path = urllib.parse.urlsplit(link).path
            filename = posixpath.basename(path).split('?')[0]
            file_type = filename.split(".")[-1]
            file_types = {
                "jpe", "jpeg", "jfif", "exif", "tiff",
                "gif", "bmp", "png", "webp", "jpg"
            }
            if file_type.lower() not in file_types:
                file_type = "jpg"

            # Download the image
            print(f"[%] Downloading Image #{self.download_count} from {link}")
            if self.query_folder:
                out_dir = f"{os.getcwd()}\\{self.output_dir}\\{self.query}"
                out_path = f"{out_dir}\\Image_{self.download_count}.{file_type}"
            else:
                out_path = f"{os.getcwd()}\\{self.output_dir}\\{self.query}.{file_type}"
            self.save_image(link, out_path)
            print("[%] File Downloaded !\n")
        except Exception as e:
            self.download_count -= 1
            print(f"[!] Issue getting: {link}\n[!] Error:: {e}")

    def run(self):
        """Runs the Bing image downloader."""

        while self.download_count < self.limit and self.page_counter < 2:
            time.sleep(1)  # Sleep for 1 second
            print(f'\n\n[!!]Indexing page: {self.page_counter}\n')
            # Parse the page source and download pics
            request_url = 'https://www.bing.com/images/search?q=' \
                          + urllib.parse.quote_plus(self.query + self.extra_query) \
                          + '&form=IRFLTR' \
                          + '&first=' + str(self.page_counter) \
                          + '&count=' + str(self.limit) \
                          + '&adlt=' + self.adult \
                          + '&qft=' + self.filters  # + '&tsc=ImageBasicHover'
            print(self.filters)
            print('Request URL: ' + request_url)
            request = urllib.request.Request(request_url, None, headers=self.headers)
            response = urllib.request.urlopen(request)
            html = response.read().decode('utf8')
            links = re.findall('murl&quot;:&quot;(.*?)&quot;', html)

            print(f"[%] Indexed {len(links)} Images on Page {self.page_counter}.")
            print("\n===============================================\n")

            for link in links:
                if self.download_count < self.limit:
                    self.download_image(link)
                else:
                    print(f"\n\n[%] Done. Downloaded {self.download_count} images.")
                    print("\n===============================================\n")
                    break
                time.sleep(1)  # Sleep for 1 second
            self.page_counter += 1
