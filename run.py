import os
import pandas as pd
from pathlib import Path
from scrape import TripAdvisorScrape
from bing_image_downloader import downloader
from enhance_image import Enhance
from gen_video import Video


# set directories and image size
attractions_dir = 'attractions'
image_dir = 'images'
enhanced_subdir = 'enhance'
video_dir = 'videos'
audio_dir = 'audio'
image_size = 'wallpaper'  # 'small', 'medium', 'large', or 'wallpaper'


def make_dir(dir):
    """
    Make a directory if it does not already exist.

    Parameters
    ----------
    dir : str
        the directory to make.
    """

    if not os.path.exists(dir):
        os.makedirs(dir)


def image_download(query, extra_query, output_dir, image_size='medium'):
    """
    Download an image from Bing for a query.

    Parameters
    ----------
    query : str
        the query to search for.
    extra_query : str
        extra query to append to the search that don't impact
        the output file name.
    output_dir : str
        the directory to save the image to.
    image_size : str
        the size of the image to download.
        'small', 'medium', 'large', or 'wallpaper'.
    """

    # check image size
    assert image_size in ['small', 'medium', 'large', 'wallpaper'], \
        "image_size is must be 'small', 'medium', 'large', or 'wallpaper'"

    # download image
    filters = f"+filterui:aspect-wide+filterui:license-L1+filterui:imagesize-{image_size}"
    downloader.download(query, extra_query=extra_query, limit=1,
                        output_dir=output_dir, adult_filter_off=False,
                        force_replace=False, timeout=60, filters=filters,
                        query_folder=False)


def sort_attractions(path, attractions):
    """
    Custom sort key to order attractions by index in df.

    Parameters
    ----------
    path : str
        the path to the attraction file, where we get theattraction name from.
    attractions : pd.DataFrame
        the dataframe of attractions.
    """

    # get file name after removing the extension
    attr = '.'.join(Path(path).name.split('.')[:-1])

    all_attractions = list(attractions['Attraction'])
    return all_attractions.index(attr)


if __name__ == '__main__':

    # Web scraping prep
    make_dir(attractions_dir)
    scraper = TripAdvisorScrape()

    # image scrape prep
    make_dir(image_dir)

    # video generation prep
    make_dir(video_dir)

    # get locations to scrape and required actions
    locations = pd.read_csv("locations.csv", encoding='cp1252')

    for i in range(len(locations)):

        loc = locations.loc[i, 'Location']

        # scrape trip advisor for attractions
        if locations.loc[i, 'To Scrape'] == 'yes' and locations.loc[i, 'Scraped'] != 'yes':
            print(f"getting attractions for {loc}")
            try:
                # get helper url to pass into scraping process if available
                helper_url = None
                if pd.notna(locations.loc[i, 'Helper URL']):
                    helper_url = locations.loc[i, 'Helper URL']
                # scrape
                df = scraper.scrape(loc, verbose=True, helper_url=helper_url)
                df.to_csv(f"{attractions_dir}\\{loc}.csv", index=False, encoding='cp1252')
                locations.loc[i, 'Scraped'] = 'yes'
            except Exception as e:
                print(e)
                locations.loc[i, 'Scrape Error'] = 'yes'

        # download an image for each attraction
        if locations.loc[i, 'To Image'] == 'yes' and locations.loc[i, 'Imaged'] != 'yes':
            print(f"getting images for {loc}")
            errors = False
            attractions = pd.read_csv(f"{attractions_dir}\\{loc}.csv", encoding='cp1252')
            for j in range(len(attractions)):
                attr = attractions.loc[j, 'Attraction']
                try:
                    # overwrite images with higher quality ones if they exist
                    image_download(attr, loc, f"{image_dir}\\{loc}", image_size='medium')
                    image_download(attr, loc, f"{image_dir}\\{loc}", image_size='large')
                    image_download(attr, loc, f"{image_dir}\\{loc}", image_size='wallpaper')
                except Exception as e:
                    print(e)
                    errors = True
            if errors:
                locations.loc[i, 'Image Error'] = 'yes'
            else:
                locations.loc[i, 'Imaged'] = 'yes'

        # enhance images
        if locations.loc[i, 'To Enhance'] == 'yes' and locations.loc[i, 'Enhanced'] != 'yes':
            print(f"enhancing images for {loc}")
            input_dir = f"{image_dir}\\{loc}"
            output_dir = f"{image_dir}\\{loc}\\{enhanced_subdir}"
            try:
                enhance = Enhance(input_dir, output_dir, max_size_to_enhance=(1920, 1080))
                enhance.enhance_images()
                locations.loc[i, 'Enhanced'] = 'yes'
            except Exception as e:
                print(e)
                locations.loc[i, 'Enhance Error'] = 'yes'

        # generate video for location
        if locations.loc[i, 'To Video'] == 'yes' and locations.loc[i, 'Videod'] != 'yes':
            print(f"generating video for {loc}")
            try:
                # get all attractions to sort image_paths by attraction rank
                attractions = pd.read_csv(f"{attractions_dir}\\{loc}.csv", encoding='cp1252')
                # find attractions that we have images for
                # (sometimes use enhanced_dir = f"{image_dir}\\{loc}")
                enhanced_dir = f"{image_dir}\\{loc}\\{enhanced_subdir}"
                image_paths = [f"{enhanced_dir}\\{file}" for file in os.listdir(enhanced_dir)
                               if os.path.isfile(f"{enhanced_dir}\\{file}")]
                # sort image_paths
                image_paths.sort(key=lambda path: sort_attractions(path, attractions))
                # take top x paths where x is rounded to the nearest 5
                image_paths = image_paths[: (len(image_paths) - len(image_paths) % 5)]
                # generate video
                video = Video(image_paths=image_paths, output_dir=f"{video_dir}\\{loc}",
                              audio_dir=audio_dir, resolution='4K', fps=60)
                video.gen_thumbnails(resolution='4K', sub_dir='4K')  # title='DENVER')
                video.gen_thumbnails(resolution='QHD', sub_dir='QHD')
                video.gen_thumbnails(resolution='FHD', sub_dir='FHD')
                video.gen_thumbnails(resolution='HD', sub_dir='HD')
                video.document()
                video.gen_video()
                locations.loc[i, 'Videod'] = 'yes'
            except Exception as e:
                print(e)
                locations.loc[i, 'Video Error'] = 'yes'

    # Update locations manager
    locations.to_csv("locations.csv", index=False, encoding='cp1252')
