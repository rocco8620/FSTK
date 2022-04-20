from . import __version__

default_window_style = '''
        * { color: #4ecca3; }
        QPushButton { background-color: #444f5d; border: 1px solid #232931 } 
        QPushButton:hover { background-color: #585c65 }
        
        QPushButton[counting=false], QLabel[counting=false] { color: #6e6e6e }
        QLabel[invalid=true] { color: #fa7161 }
'''

config = None

config_file_version = 7
tasks_file_version = 4

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
        'task_created': 0,
        'task_color_set': 0,
        'task_name_edited': 0,
        'task_ticket_n_edited': 0,
        'task_time_increased': 0,
        'task_time_decreased': 0,
        'task_time_cleared': 0,
        'task_deleted': 0,
        'task_notes_edited': 0,
        'task_notes_viewed': 0,
        'task_reordered': 0,

        'ticket_titles_refreshed': 0,
        'time_run_toggled': 0,
        'task_created_without_ticket_number': 0,

    },
    'options': {
        'redmine' : {
           'enabled': False,
           'host': '',
           'apikey': '',
           'task_name_from_ticket': False,
           'copy_time_to_clipboard': {
               'enabled': False,
               'rounding': 10
           }
       },
       'boomer_compatibility' : {
           'invert_run_pause_button': False
       },
       'switch_reminder': {
            'enabled': False,
            'interval': 60
       }
    },
    'time_running': True,
    'version': config_file_version
}

default_tasks = {
    'current_tasks': {
        '0': {
            'name': 'Task di esempio',
            'ticket': '1234',
            'elapsed_time': 4632,
            'color_group': 'Blue',
            'ticket_title': '',
            'notes': 'This is your first task. You can save notes here.'
        }
    },
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
