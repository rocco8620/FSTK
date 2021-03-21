from . import __version__

default_window_style = '''
        * { color: #4ecca3; }
        QPushButton { background-color: #444f5d; border: 1px solid #232931 } 
        QPushButton:hover { background-color: #585c65 }

'''

config_file_version = 2
tasks_file_version = 1

default_config = {
    'window': {
        'x': 0,
        'y': 0,
        'w': 460,
        'h': 520,
        'always_on_top': True,
    },
    'task_templates': {

    },
    'first_run': True,
    'stats': {
        'total_created_tasks': 0,
    },
    'version': config_file_version
}

default_tasks = {
    'current_tasks': { '0': {'name': 'Task di esempio', 'ticket': '1234', 'elapsed_time': 4632} },
    'version': tasks_file_version
}

config_folder = '~/.config/fstk'
config_file_name = 'config.json'
tasks_file_name = 'tasks.json'
lock_file_name = 'lock.pid'

desktop_folder = '~/.local/share/applications'
desktop_file_name = 'fast-switch-time-keeper.desktop'

package_name = 'fstk'
update_url = 'https://pypi.org/pypi/{}/json'.format(package_name)

version = __version__
