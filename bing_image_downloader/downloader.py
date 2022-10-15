import os
import shutil

try:
    from bing import Bing
except ImportError:  # Python 3
    from .bing import Bing


def download(query, limit=100, output_dir='dataset', adult_filter_off=True, force_replace=False, timeout=60, filters='', query_folder=True, extra_query=''):

    # engine = 'bing'
    if adult_filter_off:
        adult = 'off'
    else:
        adult = 'on'

    cwd = os.getcwd()
    image_dir = os.path.join(cwd, output_dir, query)

    if force_replace:
        if os.path.isdir(image_dir):
            shutil.rmtree(image_dir)

    # check directory and create if necessary
    try:
        if not os.path.isdir("{}\\{}\\".format(cwd, output_dir)):
            os.makedirs("{}\\{}\\".format(cwd, output_dir))
    except:
        pass
    
    assert not (not query_folder and limit != 1), "if query_folder==False, then limit must be 1"
    
    if query_folder and not os.path.isdir("{}\\{}\\{}".format(cwd, output_dir, query)):
        os.makedirs("{}\\{}\\{}".format(cwd, output_dir, query))

    bing = Bing(query, limit, output_dir, adult, timeout, filters, query_folder, extra_query)
    bing.run()


if __name__ == '__main__':
    download('abitabh', limit=10, timeout='1')
