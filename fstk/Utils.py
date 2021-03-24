try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

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


def redmine_ticket_number_validator(text):
    """

    :param text:
    :return: Success, Error message
    """
    n = text.strip('# ')

    try:
        n = int(n)
        if 0 < n < 1000000:
            return True, None
        else:
            return False, 'The number must be between 0 and 1000000'
    except ValueError:
        return False, 'The number is invalid. It must be an integer'

def not_empty_validator(text):
    """

    :param text:
    :return: Success, Error message
    """
    if text.strip() == '':
        return False, 'The text cannot be empty'
    else:
        return True, None