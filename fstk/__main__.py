import logging
import os
import sys

from PySide2.QtWidgets import QApplication

from .Fstk import MainWidget, MainWindow
from . import Globals

# configuro il logging
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s][%(levelname)s] %(message)s', filename='')

Globals.config_folder = os.path.expanduser(Globals.config_folder)

if not os.path.isdir(Globals.config_folder):
    try:
        os.mkdir(Globals.config_folder)
        logging.debug('Config folder {} created.'.format(Globals.config_folder))
    except PermissionError as e:
        logging.critical('Unable to create directory {}, error: {}'.format(Globals.config_folder, e))
        sys.exit()
else:
    logging.debug('Config folder {} already existing.'.format(Globals.config_folder))

    # Qt Application
app = QApplication(sys.argv)
app.setStyleSheet(Globals.default_window_style + '''
    QMenuBar, QMenuItem { background-color: #444f5d } 

    QListWidget { background-color: #232931; } 
    QListWidget::item, QSizeGrip { background-color: #353d48; } 
    QListWidget::item:selected { background-color: #5d54a4; } 


''')

# https://colorhunt.co/palette/117601
# QWidget
main_widget = MainWidget()
# QMainWindow using QWidget as central widget
window = MainWindow(main_widget)

# Execute application
sys.exit(app.exec_())