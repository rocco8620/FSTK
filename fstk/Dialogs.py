import json
import re

from PySide2 import QtGui
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton, QSizePolicy, QLabel, QPlainTextEdit, \
    QTextEdit, QCheckBox, QApplication, QFrame

from . import Globals, Utils
from .Globals import default_window_style


class AskForTextDialog(QDialog):

    def __init__(self, window_title, length, initial_text, validator=None):
        QDialog.__init__(self)
        self.__validator = validator

        self.setWindowTitle(window_title)
        self.resize(length, 100)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
        ''')

        self.setWindowIcon(QtGui.QIcon(Utils.get_local_file_path('icon.png')))

        # QWidget Layout
        self.box = QGridLayout()

        self.line = QLineEdit(initial_text)
        self.box.addWidget(self.line, 0, 0)

        self.error_label = QLabel()
        self.error_label.setStyleSheet('color: #fa7161')
        self.box.addWidget(self.error_label, 1, 0)

        self.ok_button = QPushButton('Ok')
        self.ok_button.clicked.connect(self.ok_handler)
        self.box.addWidget(self.ok_button, 2, 0, alignment=Qt.AlignCenter)

        self.ok_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)

    def ok_handler(self):
        if self.__validator is not None:
            success, error_msg = self.__validator(self.line.text())
            if not success:
                self.line.setStyleSheet('background-color: #fa7161')
                self.error_label.setText(error_msg)
                return

        self.accept()


class ConfirmDialog(QDialog):

    def __init__(self, window_title, text, positive_button='Ok', negative_button='Cancel', html=False):
        QDialog.__init__(self)

        self.setWindowTitle(window_title)
        self.resize(0, 100)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton, QLabel { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
            
        ''')

        self.setWindowIcon(QtGui.QIcon(Utils.get_local_file_path('icon.png')))

        # QWidget Layout
        self.box = QGridLayout()
        self.text = QLabel(text)

        if html:
            self.text.setTextFormat(Qt.RichText)

        self.box.addWidget(self.text, 0, 0, 1, 2)

        self.ok_button = QPushButton(positive_button)
        self.cancel_button = QPushButton(negative_button)

        self.ok_button.clicked.connect(lambda: self.accept())

        self.cancel_button.clicked.connect(lambda: self.reject())

        self.box.addWidget(self.ok_button, 1, 0, alignment=Qt.AlignRight)
        self.box.addWidget(self.cancel_button, 1, 1, alignment=Qt.AlignLeft)

        self.ok_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.cancel_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)


class InformationDialog(QDialog):

    def __init__(self, window_title, text, html=False, min_width=None, max_width=700):
        QDialog.__init__(self)

        self.setWindowTitle(window_title)
        self.resize(0, 100)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton, QLabel { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }

        ''')

        self.setWindowIcon(QtGui.QIcon(Utils.get_local_file_path('icon.png')))

        # QWidget Layout
        self.box = QGridLayout()

        self.text = QLabel(text)
        self.text.setMaximumWidth(max_width)
        if min_width is not None:
            self.text.setMinimumWidth(min_width)

        self.text.setWordWrap(True)
        if html:
            self.text.setTextFormat(Qt.RichText)

        self.box.addWidget(self.text, 0, 0)

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(lambda: self.accept())

        self.box.addWidget(self.ok_button, 1, 0, alignment=Qt.AlignCenter)

        self.ok_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)
        self.adjustSize()


class NewTaskDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self)

        self.setWindowTitle('Add new task')
        self.resize(500, 150)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QPlainTextEdit, QLineEdit { background-color: #444f5d; }
            QPushButton, QLabel { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
        ''')

        self.setWindowIcon(QtGui.QIcon(Utils.get_local_file_path('icon.png')))

        # QWidget Layout
        self.box = QGridLayout()

        self.box.addWidget(QLabel('Name:'), 0, 0)
        self.box.addWidget(QLabel('Ticket:'), 1, 0)

        self.name = QPlainTextEdit()
        self.name.setTabChangesFocus(True)
        self.ticket_number = QLineEdit()

        self.box.addWidget(self.name, 0, 1)
        self.box.addWidget(self.ticket_number, 1, 1)

        self.error_label = QLabel()
        self.error_label.setStyleSheet('color: #fa7161')
        self.box.addWidget(self.error_label, 2, 0, 1, 2)

        self.ok_button = QPushButton('Save')
        self.ok_button.clicked.connect(self.check_data)

        self.box.addWidget(self.ok_button, 3, 0, 1, 2, alignment=Qt.AlignCenter)

        self.ok_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)

    def check_data(self):
        if len(self.name.toPlainText().strip()) == 0:
            self.show_error('The task name cannot be empty', self.name)
            return
        else:
            self.clear_error(self.name)

        if self.ticket_number.text().strip() != '':
            success, error_msg = Utils.integer_number_validator(self.ticket_number.text())
            if not success:
                self.show_error(error_msg, self.ticket_number)
                return
            else:
                self.clear_error(self.ticket_number)

        self.name.setPlainText(self.name.toPlainText().strip().replace('\n', ' ').replace('\t', ''))
        self.ticket_number.setText(self.ticket_number.text().strip(' \n\t#'))

        self.accept()

    def show_error(self, message, widget):

        widget.setStyleSheet('background-color: #fa7161')
        self.error_label.setText(message)

    def clear_error(self, widget):
        widget.setStyleSheet('')


class HelpDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self)

        self.setWindowTitle('Help')
        self.resize(700, 600)
        self.setStyleSheet(default_window_style + '''
                    QDialog { background-color: #232931 }
                    QLineEdit { background-color: #444f5d; }
                    QPushButton { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
                    QTextEdit { background-color: #444f5d }
                ''')

        self.setWindowIcon(QtGui.QIcon(Utils.get_local_file_path('icon.png')))

        help_text = '''
            Current FSTK version: <b>{}</b><br>
            <br>
            <b>Shortcuts</b>
            <ul>
                <li><b>Ctrl + Q</b>: Exits the software.</li>
                <li><b>Ctrl + H</b>: Opens this help page.</li>
            </ul><br>
            <b>Tips</b>
            <ul>
                <li>To edit the redmine ticket number on an entry, click on it.</li>
                <li>To open the redmine webpage of a ticket, double click on the ticket number.</li>
                <li>To open the redmine webpage to add a time entry to a ticket, click on the task time counter.</li>
                <li>To reorder the tasks in the list, drag & drop them.</li>
                <li>To assign a color to a task right click on it.</li>
                <li>To obtain the redmine api key, visit the page <b>/my/account</b> on your redmine installation. Use the menu on the right to generate/see it.</li>
            </ul><br>
            <b>Info</b>
            <ul>
                <li>The tasks and times are written to disk every minute, to prevent data loss.</li>
                <li>This software features an auto update function.</li>
                <li>Logs are saved on /tmp/fstk.log</li>
                <li>This software is BigFax® approved</li>
            </ul><br>
            <b>Gotchas</b>
            <ul>
                <li>If the computer is put on standby for too much time, the time counter may stop counting.</li>
            </ul>
        '''.format(Globals.version)

        # QWidget Layout
        self.box = QGridLayout()

        self.text = QTextEdit(help_text)
        self.text.setReadOnly(True)
        self.box.addWidget(self.text, 0, 0)

        self.close_button = QPushButton('Close')

        self.close_button.clicked.connect(lambda: self.accept())

        self.box.addWidget(self.close_button, 1, 0, alignment=Qt.AlignCenter)

        self.close_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)



class ChangelogDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self)

        self.setWindowTitle('Changelog')
        self.resize(600, 400)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
            QTextEdit { background-color: #444f5d }
        ''')

        self.setWindowIcon(QtGui.QIcon(Utils.get_local_file_path('icon.png')))

        changelog_text = '''
            Current FSTK version: <b>{}</b><br>
            <br>
            <b>Release 0.7.0</b>
            <ul>
                <li>Double clicking on the ticket number now opens the relative redmine webpage</li>
                <li>Double clicking on the task time counter now opens the relative redmine webpage to add a new time entry</li>
                <li>New function to periodicaly remind the user to switch tasks</li>
            </ul><br>
            <b>Release 0.6.0</b>
            <ul>
                <li>New compatibility mode for boomers to invert the icon and color of play/pause button</li>
                <li>Usage statistics are now recorded locally, to be used to hint development direction</li>
                <li>Now fstk correctly handles SIGTERM signals</li>
                <li>Fix bug preventing the ticket number to be removed from a task</li>
            </ul><br>
            <b>Release 0.5.0</b>
            <ul>
                <li>The time tracking can now be paused</li>
                <li>Notes related to tasks can now be saved</li>
                <li>New icons for buttons</li>
                <li>Fix fstk not starting if lockfile was pointing to process with specific cmdline. Thanks M.Z.</li>
                <li>Fix redmine ticket title missing if the ticket was marked as 'closed' on redmine</li>
            </ul><br>
            <b>Release 0.4.1</b>
            <ul>
                <li>Fix bug redmine ticket title search when no ticket number was provided</li>
            </ul><br>
            <b>Release 0.4.0</b>
            <ul>
                <li>Redmine ticket title is now visible in the taskbox</li>
                <li>Invalid data for the task name or ticket number is not ignored anymore</li>
                <li>Logs are now saved also on /tmp/fstk.log</li>
                <li>Configuration page is now available</li>
                <li>Minor graphical and usage improvements</li>
            </ul><br>
            <b>Release 0.3.0</b>
            <ul>
                <li>The tasks can be assigned a color right clicking on them</li>
                <li>A task with 0 time counted is now greyed</li>
                <li>Tasks can now be beleted using 'Del' keyboard button</li>
                <li>Clicking on empty space near a task name wont open the 'change name dialog' anymore</li>
                <li>Fixed incompatibility with python 3.6.0-3.8.5. Thanks P.P.</li>
            </ul><br>
            <b>Release 0.2.1</b>
            <ul>
                <li>Fix drag & drop bug that made some tasks disappear if reordered. Thanks N.N.</li>
                <li>Fixed bug that made the tasks controls disappear while the tasks was drag & dropped</li>
            </ul><br>
            <b>Release 0.2.0</b>
            <ul>
                <li>Added a label showing the total hours counted</li>
                <li>Added a button to clear the time recorded for a task without deleting the task itself</li>
                <li>The tasks in the list can now be reordered dragging them</li>
                <li>Added stats menu bar</li>
                <li>Added button to minimize window</li>
                <li>Minor fixes</li>
            </ul><br>
            <b>Release 0.1.2</b>
            <ul>
                <li>First release, basic time counting and task management</li>
                <li>Auto update function</li>
                <li>Desktop shortcut for easy start</li>
            </ul>
        '''.format(Globals.version)

        # QWidget Layout
        self.box = QGridLayout()

        self.text = QTextEdit(changelog_text)
        self.text.setReadOnly(True)
        self.box.addWidget(self.text, 0, 0)

        self.close_button = QPushButton('Close')

        self.close_button.clicked.connect(lambda: self.accept())

        self.box.addWidget(self.close_button, 1, 0, alignment=Qt.AlignCenter)

        self.close_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)


class StatisticsDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self)

        self.setWindowTitle('Dev Statistics')
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
        ''')

        self.setWindowIcon(QtGui.QIcon(Utils.get_local_file_path('icon.png')))

        stats_text = '''
            <b>Dev Statistics</b>
            <ul>
                {}
            </ul>
        '''.format(''.join([ '<li>{}: <b>{}<b></li>'.format(k.replace('_', ' ').capitalize(), v) for k, v in Globals.config['stats'].items() ]) )

        # QWidget Layout
        self.box = QGridLayout()

        self.text = QLabel(stats_text)
        self.text.setTextFormat(Qt.RichText)
        self.box.addWidget(self.text, 0, 0)

        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(lambda: self.accept())

        self.clipboard_button = QPushButton('Copy to clipboard')
        self.clipboard_button.clicked.connect(lambda: QApplication.clipboard().setText(json.dumps(Globals.config['stats'])))

        self.box.addWidget(self.clipboard_button, 1, 0, alignment=Qt.AlignCenter)
        self.box.addWidget(self.close_button, 2, 0, alignment=Qt.AlignCenter)

        self.close_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.clipboard_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)
        self.adjustSize()


class ConfigurationDialog(QDialog):

    def __init__(self, current_config):
        QDialog.__init__(self)

        self.setWindowTitle('Configuration')
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton, QLabel { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
            QPushButton:disabled, QLabel:disabled, QCheckBox:disabled { color: grey; }
            QLineEdit:disabled { background-color: #323942; color: grey; }
        ''')

        self.setWindowIcon(QtGui.QIcon(Utils.get_local_file_path('icon.png')))

        # QWidget Layout
        self.box = QGridLayout()

        ############################
        ### Integrazioni redmine ###
        ############################

        self.enable_redmine_integration = QCheckBox("Enable redmine integration")
        self.enable_redmine_integration.setChecked(current_config['redmine']['enabled'])
        self.enable_redmine_integration.stateChanged.connect(self.update_redmine_ctrls_status)
        self.box.addWidget(self.enable_redmine_integration, 0, 0, 1, 2)

        self.label_redmine_hosts = QLabel('Redmine host:')
        self.box.addWidget(self.label_redmine_hosts, 1, 0)
        self.label_redmine_apikey = QLabel('Redmine api key:')
        self.box.addWidget(self.label_redmine_apikey, 2, 0)
        self.label_redmine_toobtainkey = QLabel('To obtain the api key visit <b>/my/account</b> of your installation. More on help page.')
        self.label_redmine_toobtainkey.setTextFormat(Qt.RichText)
        self.box.addWidget(self.label_redmine_toobtainkey, 3, 0, 1, 2)

        self.redmine_host = QLineEdit(current_config['redmine']['host'])
        self.redmine_host.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.redmine_host.setMinimumWidth(400)
        self.box.addWidget(self.redmine_host, 1, 1)

        self.redmine_api_key = QLineEdit(current_config['redmine']['apikey'])
        self.box.addWidget(self.redmine_api_key, 2, 1)

        #self.use_ticket_as_task_name = QCheckBox("Use redmine ticket name as task name")
        #self.use_ticket_as_task_name.setChecked(current_config['redmine']['task_name_from_ticket'])
        #self.box.addWidget(self.use_ticket_as_task_name, 4, 0, 1, 2)

        self.update_redmine_ctrls_status(self.enable_redmine_integration.checkState())

        ############################
        ### Boomer compatibility ###
        ############################

        self.box.addWidget(self.get_separator(), 5, 0, 1, 2)

        self.box.addWidget(QLabel('<b>Boomer compatibility mode</b>'), 6, 0, 1, 2)

        self.boomer_play_pause_toggle = QCheckBox("Invert play/pause button color and icon to conform to old stile")
        self.boomer_play_pause_toggle.setChecked(current_config['boomer_compatibility']['invert_run_pause_button'])
        self.box.addWidget(self.boomer_play_pause_toggle, 7, 0, 1, 2)

        ############################
        ##### Switch reminder ######
        ############################

        self.box.addWidget(self.get_separator(), 8, 0, 1, 2)

        self.box.addWidget(QLabel('<b>Switch reminder</b>'), 9, 0, 1, 2)

        self.switch_reminder = QCheckBox("Enable periodic reminder to switch fstk task")
        self.switch_reminder.setChecked(current_config['switch_reminder']['enabled'])
        self.switch_reminder.stateChanged.connect(self.update_switch_reminder_ctrls_status)
        self.box.addWidget(self.switch_reminder, 10, 0, 1, 2)

        self.label_remind_every = QLabel('Remind every (minutes):')
        self.box.addWidget(self.label_remind_every, 11, 0)

        self.redmind_every_min = QLineEdit(str(current_config['switch_reminder']['interval']))

        self.redmind_every_min.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.redmind_every_min.setMaximumWidth(60)
        self.box.addWidget(self.redmind_every_min, 11, 1)

        self.update_switch_reminder_ctrls_status(self.switch_reminder.checkState())

        ############################
        ######### Generico #########
        ############################

        self.error_label = QLabel()
        self.error_label.setStyleSheet('color: #fa7161')
        self.box.addWidget(self.error_label, 12, 0, 1, 2)

        self.ok_button = QPushButton('Save')
        self.ok_button.clicked.connect(self.check_data)

        self.box.addWidget(self.ok_button, 13, 0, 1, 2, alignment=Qt.AlignCenter)

        self.ok_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)
        self.adjustSize()

    def get_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet('background-color: #444f5d')
        return separator


    def check_data(self):

        # se è abilitata questa funzione dobbiamo effettuare la validazione dei suoi dati
        if self.enable_redmine_integration.isChecked():

            if not re.match(r'https?://[-a-zA-Z0-9:._]+', self.redmine_host.text().strip()):
                self.show_error('The redmine host address is not valid. Example: https://red.host.com:4000', self.redmine_host)
                return
            else:
                self.clear_error(self.redmine_host)

            if not re.match(r'[a-z0-9]{40}', self.redmine_api_key.text().strip()):
                self.show_error('The redmine apikey is not valid. Example: 3131c6e3923adf52e25fa5b721254d02e6483954', self.redmine_api_key)
                return
            else:
                self.clear_error(self.redmine_api_key)

        # se è abilitata questa funzione dobbiamo effettuare la validazione dei suoi dati
        if self.switch_reminder.isChecked():
            success, message = Utils.integer_number_validator(self.redmind_every_min.text())
            if not success:
                self.show_error(message, self.redmind_every_min)
                return
            else:
                self.clear_error(self.redmind_every_min)

        self.result = {
           'redmine' : {
               'enabled': self.enable_redmine_integration.isChecked(),
               'host': self.redmine_host.text().strip(' \r\n\t/'),
               'apikey': self.redmine_api_key.text().strip(),
               'task_name_from_ticket': False, #self.use_ticket_as_task_name.isChecked()
           },
           'boomer_compatibility' : {
               'invert_run_pause_button': self.boomer_play_pause_toggle.isChecked()
           },
           'switch_reminder': {
                'enabled': self.switch_reminder.isChecked(),
                'interval': int(self.redmind_every_min.text().strip()) if self.switch_reminder.isChecked() else 60
           }
        }

        self.accept()

    def show_error(self, message, widget):
        widget.setStyleSheet('background-color: #fa7161')
        self.error_label.setText(message)

    def clear_error(self, widget):
        widget.setStyleSheet('')

    def update_redmine_ctrls_status(self, state):
        widgets = [self.label_redmine_hosts, self.label_redmine_apikey, self.label_redmine_toobtainkey, self.redmine_host, self.redmine_api_key] #, self.use_ticket_as_task_name]
        for w in widgets:
            w.setEnabled(state == Qt.Checked)

    def update_switch_reminder_ctrls_status(self, state):
        widgets = [self.label_remind_every, self.redmind_every_min]
        for w in widgets:
            w.setEnabled(state == Qt.Checked)




class ShowNotesDialog(QDialog):

    def __init__(self, pos, text, max_width=700):
        QDialog.__init__(self)

        self.resize(0, 100)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton, QLabel { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }

        ''')

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)

        self.box = QGridLayout()

        self.text = QLabel(text)
        self.text.setMaximumWidth(max_width)
        self.text.setWordWrap(True)

        self.box.addWidget(self.text, 0, 0)

        self.setLayout(self.box)
        self.adjustSize()

        self.move(pos)


class EditNotesDialog(QDialog):

    def __init__(self, initial_text):
        QDialog.__init__(self)

        self.setWindowTitle('Edit notes')
        self.resize(600, 400)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
            QTextEdit { background-color: #444f5d }
        ''')

        self.setWindowIcon(QtGui.QIcon(Utils.get_local_file_path('icon.png')))

        # QWidget Layout
        self.box = QGridLayout()

        self.text = QTextEdit()
        self.text.setPlainText(initial_text)
        self.box.addWidget(self.text, 0, 0)

        self.close_button = QPushButton('Save')

        self.close_button.clicked.connect(self.accept)

        self.box.addWidget(self.close_button, 1, 0, alignment=Qt.AlignCenter)

        self.close_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)