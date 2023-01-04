import os
import shutil

try:
    from bing import Bing
except ImportError:  # Python 3
    from .bing import Bing


def download(query, limit=100, output_dir='dataset', adult_filter_off=True,
             force_replace=False, timeout=60, filters='', query_folder=True,
             extra_query=''):
    """
    Download images from Bing.

    Parameters
    ----------
    query : str
        the query to search for.
    limit : int
        the number of images to download.
    output_dir : str
        the directory to save the images to.
    adult_filter_off : bool
        whether to turn off the adult filter.
    force_replace : bool
        whether to force replace the images.
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

    adult = 'off' if adult_filter_off else 'on'

    cwd = os.getcwd()
    image_dir = os.path.join(cwd, output_dir, query)

    # remove directory if force_replace
    if force_replace:
        if os.path.isdir(image_dir):
            shutil.rmtree(image_dir)

    assert not (not query_folder and limit != 1), \
        "if query_folder==False, then limit must be 1"

    # check directory and create if necessary
    try:
        path = f"{cwd}\\{output_dir}\\"
        if not os.path.isdir(path):
            os.makedirs(path)
    except:
        pass

    path = f"{cwd}\\{output_dir}\\{query}"
    if query_folder and not os.path.isdir(path):
        os.makedirs(path)

    bing = Bing(query, limit, output_dir, adult, timeout, filters,
                query_folder, extra_query)
    bing.run()


if __name__ == '__main__':
    download('cars', limit=10, timeout='1')
