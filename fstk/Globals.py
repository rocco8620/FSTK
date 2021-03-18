default_window_style = '''
        * { color: #4ecca3; }
        QPushButton { background-color: #444f5d; border: 1px solid #232931 } 
        QPushButton:hover { background-color: #585c65 }

'''

default_config = {
    'window': {
        'x': 0,
        'y': 0,
        'always_on_top': True,
    },
    'task_templates': {

    },
    'version': 1
}

default_times = {
    'current_tasks': { '0': {'name': 'Task di esempio', 'ticket': '#1234', 'elapsed_time': 4632} },
    'version': 1
}

config_folder = '~/.config/fstk'
config_file_name = 'config.json'
times_file_name = 'times.json'

update_url = 'https://pypi.org/pypi/goodtraceback/json'

from . import __version__
version = __version__