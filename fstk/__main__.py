import logging
import os
import sys

from PySide2.QtWidgets import QApplication

from .Fstk import MainWidget, MainWindow
from . import Globals

# configuro il logging
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s][%(levelname)s] %(message)s', filename='')

Globals.config_folder = os.path.expanduser(Globals.config_folder)
Globals.desktop_folder = os.path.expanduser(Globals.desktop_folder)

if not os.path.isdir(Globals.config_folder):
    try:
        os.mkdir(Globals.config_folder)
        logging.debug('Config folder {} created.'.format(Globals.config_folder))
    except PermissionError as e:
        logging.critical('Unable to create directory {}, error: {}'.format(Globals.config_folder, e))
        sys.exit()
else:
    logging.debug('Config folder {} already existing.'.format(Globals.config_folder))

lock_file_path = os.path.join(Globals.config_folder, Globals.lock_file_name)

# file di lock per evitare esecuzioni multiple
if os.path.isfile(lock_file_path):
    # se il file di lock esiste lo leggo
    with open(lock_file_path, 'r') as o:
        lock_pid = o.read().strip()

    # se il processo è in esecuzione
    if os.path.isfile('/proc/{}/cmdline'.format(lock_pid)):
        with open('/proc/{}/cmdline'.format(lock_pid), 'rb') as o:
            lock_pid_cmdline = o.read()
        # il valore letto è un insieme di stringhe separate da '\x00', devo parsarle
        lock_pid_cmdline = [ x.decode() for x in lock_pid_cmdline.split(b'\x00') if x != b'' ]

        # verifico se il processo identificato dal lock file è del tipo giusto
        if lock_pid_cmdline[-2] == '-m' and lock_pid_cmdline[-1] == 'fstk':
            logging.warning('There is another instance of FSTK running (pid {}). Exiting'.format(lock_pid))
            sys.exit()
        else:
            # suppongo che sia un file di lock vecchio e lo elimino
            logging.warning('Found a stale lock file (pid {}). Process found but wrong cmdline ({}). Cleaning up'.format(lock_pid, lock_pid_cmdline))
            os.remove(lock_file_path)
    else:
        # se il processo non è in esecuzione suppongo che sia un file di lock vecchio e lo elimino
        logging.warning('Found a stale lock file (pid {}). Process with that pid not found. Cleaning up'.format(lock_pid))
        os.remove(lock_file_path)

else:
    logging.debug('Lock file not present')

# arrivati qui il file di lock è stato gestito, posso creare quello per questa esecuzione

with open(lock_file_path, 'w') as o:
    o.write(str(os.getpid()))

# Qt Application
app = QApplication(sys.argv)
app.setStyleSheet(Globals.default_window_style + '''
    QMenuBar, QMenu { background-color: #444f5d } 
    QMenu::item:selected { background-color: #232931 } 

    QListWidget { background-color: #232931; } 
    QListWidget::item, QSizeGrip { background-color: #353d48; } 
    QListWidget::item:selected { background-color: #5d54a4; } 

    QStatusBar { background-color: #444f5d } 
    QScrollBar {
        background-color: #353d48;
    }
    QScrollBar::handle {
        background: #777e87;
    }

''')

# https://colorhunt.co/palette/117601
# QWidget
main_widget = MainWidget()
# QMainWindow using QWidget as central widget
window = MainWindow(main_widget)

# Execute application
sys.exit(app.exec_())