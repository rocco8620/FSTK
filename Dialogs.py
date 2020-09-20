from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton, QSizePolicy, QLabel

from Globals import default_window_style


class AskForTextDialog(QDialog):

    def __init__(self, window_title, length, initial_text):
        QDialog.__init__(self)

        self.setWindowTitle(window_title)
        self.resize(length, 100)
        #self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
        ''')

        # QWidget Layout
        self.box = QGridLayout()

        self.line = QLineEdit(initial_text)
        self.line.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.box.addWidget(self.line, 0, 0)

        self.ok_button = QPushButton('Ok')

        self.ok_button.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.ok_button.clicked.connect(lambda: self.accept())

        self.box.addWidget(self.ok_button, 1, 0, alignment=Qt.AlignCenter)

        self.ok_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)

class ConfirmDialog(QDialog):

    def __init__(self, window_title, text, positive_button='Ok', negative_button='Cancel'):
        QDialog.__init__(self)

        self.setWindowTitle(window_title)
        self.resize(0, 100)
        #self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet(default_window_style + '''
            QDialog { background-color: #232931 }
            QLineEdit { background-color: #444f5d; }
        ''')

        # QWidget Layout
        self.box = QGridLayout()

        self.question = QLabel(text)
        self.question.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.box.addWidget(self.question, 0, 0, 1, 2)

        self.ok_button = QPushButton(positive_button)
        self.cancel_button = QPushButton(negative_button)

        self.ok_button.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.ok_button.clicked.connect(lambda: self.accept())

        self.cancel_button.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.cancel_button.clicked.connect(lambda: self.reject())

        self.box.addWidget(self.ok_button, 1, 0, alignment=Qt.AlignRight)
        self.box.addWidget(self.cancel_button, 1, 1, alignment=Qt.AlignLeft)

        self.ok_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.cancel_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setLayout(self.box)