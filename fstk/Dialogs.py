from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton, QSizePolicy, QLabel, QPlainTextEdit, QHBoxLayout

from . import Globals
from .Globals import default_window_style


class AskForTextDialog(QDialog):

    def __init__(self, window_title, length, initial_text):
        QDialog.__init__(self)

        self.setWindowTitle(window_title)
        self.resize(length, 100)
        #self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
        ''')

        # QWidget Layout
        self.box = QGridLayout()

        self.line = QLineEdit(initial_text)
        self.box.addWidget(self.line, 0, 0)

        self.ok_button = QPushButton('Ok')

        self.ok_button.clicked.connect(lambda: self.accept())

        self.box.addWidget(self.ok_button, 1, 0, alignment=Qt.AlignCenter)

        self.ok_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)

class ConfirmDialog(QDialog):

    def __init__(self, window_title, text, positive_button='Ok', negative_button='Cancel', html=False):
        QDialog.__init__(self)

        self.setWindowTitle(window_title)
        self.resize(0, 100)
        #self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton, QLabel { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
            
        ''')

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

    def __init__(self, window_title, text, html=False):
        QDialog.__init__(self)

        self.setWindowTitle(window_title)
        self.resize(0, 100)
        # self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton, QLabel { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }

        ''')

        # QWidget Layout
        self.box = QGridLayout()

        self.text = QLabel(text)
        if html:
            self.text.setTextFormat(Qt.RichText)

        self.box.addWidget(QLabel(text), 0, 0)

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(lambda: self.accept())

        self.box.addWidget(self.ok_button, 1, 0, alignment=Qt.AlignCenter)

        self.ok_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)

class NewTaskDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self)

        self.setWindowTitle('Add new task')
        self.resize(500, 150)
        #self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QPlainTextEdit, QLineEdit { background-color: #444f5d; }
            QPushButton, QLabel { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
        ''')

        # QWidget Layout
        self.box = QGridLayout()

        self.box.addWidget(QLabel('Name:'), 0, 0)
        self.box.addWidget(QLabel('Ticket:'), 1, 0)

        self.name = QPlainTextEdit()
        self.ticket_number = QLineEdit()

        self.box.addWidget(self.name, 0, 1)
        self.box.addWidget(self.ticket_number, 1, 1)

        self.ok_button = QPushButton('Save')
        self.ok_button.clicked.connect(self.check_data)

        self.box.addWidget(self.ok_button, 2, 0, 1, 2, alignment=Qt.AlignCenter)

        self.ok_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)

    def check_data(self):
        if len(self.name.toPlainText().strip()) == 0:
            self.reject()
            return

        self.name.setPlainText(self.name.toPlainText().strip().replace('\n', ' '))
        self.ticket_number.setText('#' + self.ticket_number.text().strip(' \n\t#'))

        self.accept()

class HelpDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self)

        self.setWindowTitle('Help')
        self.resize(500, 100)
        #self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
            QPushButton { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
        ''')

        help_text = '''
            Current FSTK version: <b>{}</b><br>
            <br>
            <b>Shortcuts</b><br>
            <br>
            <b>Ctrl + Q</b>: Exits the software<br>
            <br>
            <b>Tips</b>
            <ul>
                <li>To edit the redmine ticket number on an entry, click on it</li>
            </ul><br>
            <b>Info</b>
            <ul>
                <li>The times are written to disk every minute, to prevent data loss</li>
                <li>This software features an auto update function</li>
            </ul><br>
            <b>Gotchas</b>
            <ul>
                <li>If the computer is put on standby for too much time, the time counter may stop counting</li>
            </ul>
            
        '''.format(Globals.version)

        # QWidget Layout
        self.box = QGridLayout()

        self.text = QLabel(help_text)
        self.text.setTextFormat(Qt.RichText)
        self.box.addWidget(self.text, 0, 0)

        self.close_button = QPushButton('Close')

        self.close_button.clicked.connect(lambda: self.accept())

        self.box.addWidget(self.close_button, 1, 0, alignment=Qt.AlignCenter)

        self.close_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)