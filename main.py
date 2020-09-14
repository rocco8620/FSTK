import sys
import json


from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QPainter, QBrush, QColor, QFont, QIcon, QPixmap, QCursor
from PySide2.QtWidgets import (QAction, QApplication, QHeaderView, QHBoxLayout, QLabel, QLineEdit,
                               QMainWindow, QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget, QMenu, QListWidget, QListWidgetItem, QGridLayout,
                               QStyleOptionButton, QStyle, QSizePolicy)
from PySide2.QtCharts import QtCharts


def set_min_size_from_content(elem):
    width = elem.fontMetrics().boundingRect(elem.text()).width() + 14
    elem.setMaximumWidth(width)

    return width

def widgets_at(pos):
    """Return ALL widgets at `pos`

    Arguments:
        pos (QPoint): Position at which to get widgets

    """

    widgets = []
    widget_at = app.widgetAt(pos)

    while widget_at:
        widgets.append(widget_at)

        # Make widget invisible to further enquiries
        widget_at.setAttribute(Qt.WA_TransparentForMouseEvents)
        widget_at = app.widgetAt(pos)

    # Restore attribute
    for widget in widgets:
        widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    return widgets

class RowElement(QWidget):

    def __init__(self, name, ticket_number, parent=None):
        super(RowElement, self).__init__(parent)

        self.box = QGridLayout()


        self.name = QLabel(name)
        self.name.setWordWrap(True)

        self.name.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.box.addWidget(self.name, 0, 0, 1, 2)
        self.box.setColumnStretch(0, 7)

        lay = QHBoxLayout()

        self.ticket_number = QLabel(ticket_number)
        lay.addWidget(self.ticket_number)

        self.save_to_redmine = QPushButton('Save')
        self.save_to_redmine.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        lay.addWidget(self.save_to_redmine, alignment=Qt.AlignLeft)

        lay.addStretch()

        self.box.addLayout(lay, 1, 0)

        self.spent_time = QLabel('00:00')
        self.spent_time.setFont(QFont('Mono', 16))

        self.box.addWidget(self.spent_time, 0, 2, 2, 1)
        self.box.setColumnStretch(1, 2)


        self.add_time = QPushButton("+5")
        self.add_time.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')

        self.sub_time = QPushButton("-5")
        self.sub_time.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.sub_time.setMaximumWidth(set_min_size_from_content(self.add_time))

        self.spent_time.setFont(QFont('Mono', 16))


        self.box.addWidget(self.add_time, 0, 3)
        self.box.addWidget(self.sub_time, 1, 3)
        self.box.setColumnStretch(2, 2)

        self.setLayout(self.box)


class MainWidget(QWidget):


    def __init__(self):
        QWidget.__init__(self)

        # Create the list
        self.mylist = QListWidget()

        # Add to list a new item (item is simply an entry in your list)
        item = QListWidgetItem(self.mylist)

        # Instanciate a custom widget
        row = RowElement('Creazione ticket per Nicolas', '#4752')
        item.setSizeHint(row.minimumSizeHint())

        # Associate the custom widget to the list entry
        self.mylist.setItemWidget(item, row)

        # Add to list a new item (item is simply an entry in your list)
        item = QListWidgetItem(self.mylist)

        # Instanciate a custom widget
        row = RowElement('Eliminazione dei siti web su trv4', '#5032')
        item.setSizeHint(row.minimumSizeHint())

        # Associate the custom widget to the list entry
        self.mylist.setItemWidget(item, row)

        # Add to list a new item (item is simply an entry in your list)
        item = QListWidgetItem(self.mylist)

        # Instanciate a custom widget
        row = RowElement('Lettura delle favole della buona notte al virtualizzatore lisp-ve-pve-01, perchè senza non si spegne.', '#6834')
        item.setSizeHint(row.minimumSizeHint())

        # Associate the custom widget to the list entry
        self.mylist.setItemWidget(item, row)

        self.start_end_day = QPushButton("Start Day")
        self.start_end_day.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.settings = QPushButton("Settings")
        self.settings.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.add_time_target = QPushButton("+")
        self.add_time_target.setFont(QFont('Mono', 17, weight = QFont.Bold))
        self.add_time_target.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # QWidget Layout
        self.layout = QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setRowStretch(0, 1)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.bottom_layout.addWidget(self.start_end_day)
        self.bottom_layout.addWidget(self.settings)
        self.bottom_layout.addWidget(self.add_time_target)

        self.layout.addWidget(self.mylist, 0, 0)
        self.layout.addLayout(self.bottom_layout, 1, 0)

        # Set the layout to the QWidget
        self.setLayout(self.layout)
        self.setContentsMargins(0, 0, 0, 0)




    @Slot()
    def quit_application(self):
        QApplication.quit()



class MainWindow(QMainWindow):
    def __init__(self, widget):
        QMainWindow.__init__(self)
        self.setWindowTitle("Fast Switch Time Keeper")

        # Menu
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("Options")
        self.load_dump_action = self.file_menu.addAction("Always on top")

        # Exit QAction
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_app)

        self.file_menu.addAction(exit_action)
        self.widget = widget
        self.setCentralWidget(self.widget)



    @Slot()
    def exit_app(self, checked):
        QApplication.quit()


if __name__ == "__main__":
    # Qt Application
    app = QApplication(sys.argv)
    #app.setStyleSheet('* { background-color: #424242 } QPushButton { color: white; background-color: #757575; border: 0 } QPushButton:hover { background-color: #9E9E9E }')
    app.setStyleSheet( '''
        * { color: #4ecca3; }
        QPushButton { background-color: #444f5d; border: 1px solid #232931 } 
        QPushButton:hover { background-color: #585c65 }
        
        QMenuBar, QMenuItem { background-color: #444f5d } 
        
        QListWidget { background-color: #232931; } 
        QListWidget::item { background-color: #353d48; } 
        QListWidget::item:selected { background-color: #5d54a4; } 
        
    ''')

    # https://colorhunt.co/palette/117601
    # QWidget
    widget = MainWidget()
    # QMainWindow using QWidget as central widget
    window = MainWindow(widget)
    window.resize(460, 420)
    window.show()

    # Execute application
    sys.exit(app.exec_())