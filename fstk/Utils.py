import importlib.resources as pkg_resources
from . import assets

ASSETS_PATHS_CACHE = {}

def get_local_file_path(filename):
    if filename not in ASSETS_PATHS_CACHE:
        with pkg_resources.path(assets, filename) as f:
            ASSETS_PATHS_CACHE[filename] = str(f)

    return ASSETS_PATHS_CACHE[filename]

def format_time(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 3600) % 60

        return '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds)