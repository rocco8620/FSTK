import sys


from PySide2.QtCore import Qt, Slot, QPoint, QEvent, QTimer
from PySide2.QtGui import QPainter, QBrush, QColor, QFont, QIcon, QPixmap, QCursor
from PySide2.QtWidgets import (QAction, QApplication, QHeaderView, QHBoxLayout, QLabel, QLineEdit,
                               QMainWindow, QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget, QMenu, QListWidget, QListWidgetItem, QGridLayout,
                               QStyleOptionButton, QStyle, QSizePolicy, QDialog)

from Dialogs import AskForTextDialog, ConfirmDialog
from Globals import default_window_style
from SaveFiles import SaveFile


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

    __seconds = 0

    __saved = False
    __list = None
    __list_item = None

    def __init__(self, name, ticket_number, list, list_item):
        super(RowElement, self).__init__(None)
        self.__list = list
        self.__list_item = list_item

        self.box = QGridLayout()


        self.name = QLabel(name)
        self.name.setWordWrap(True)

        self.name.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.box.addWidget(self.name, 0, 0, 1, 2)
        self.box.setColumnStretch(0, 7)

        self.redmine_elements = QHBoxLayout()

        self.ticket_number = QPushButton(ticket_number)
        self.ticket_number.setStyleSheet('border: 0; background-color: transparent')
        self.ticket_number.clicked.connect(self.edit_ticket_number)
        self.redmine_elements.addWidget(self.ticket_number)

        self.save_to_redmine = QPushButton('Save')
        self.save_to_redmine.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.redmine_elements.addWidget(self.save_to_redmine, alignment=Qt.AlignLeft)

        self.redmine_elements.addStretch()

        self.box.addLayout(self.redmine_elements, 1, 0)

        self.spent_time = QLabel('00:00:00')
        self.spent_time.setFont(QFont('Mono', 16))

        self.box.addWidget(self.spent_time, 0, 2)
        self.box.setColumnStretch(1, 2)

        self.time_buttons = QHBoxLayout()

        self.add_time = QPushButton("+5")
        self.add_time.clicked.connect(lambda: self.update_time(+5 * 60))
        self.add_time.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')

        self.sub_time = QPushButton("-5")
        self.sub_time.clicked.connect(lambda: self.update_time(-5 * 60))
        self.sub_time.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.sub_time.setMaximumWidth(set_min_size_from_content(self.add_time))

        self.time_buttons.addWidget(self.sub_time)
        self.time_buttons.addWidget(self.add_time)

        self.box.addLayout(self.time_buttons, 1, 2)

        self.del_record = QPushButton("X")
        self.del_record.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.del_record.setMaximumWidth(set_min_size_from_content(self.add_time))
        self.del_record.setMinimumWidth(set_min_size_from_content(self.add_time))
        self.del_record.clicked.connect(lambda: self.del_task())

        self.box.addWidget(self.del_record, 0, 3)

        self.box.setColumnStretch(2, 2)

        self.setLayout(self.box)

    @Slot()
    def edit_ticket_number(self):
        dialog = AskForTextDialog(window_title='Set redmine ticket number', initial_text=self.ticket_number.text().strip('#'), length=250)
        dialog.exec()
        n = dialog.line.text().strip('# ')

        try:
            n = int(n)
            if 0 < n < 1000000:
                self.ticket_number.setText('#' + str(n))
        except ValueError:
            pass

    @Slot()
    def del_task(self):
       dialog = ConfirmDialog(window_title='Confirm task deletion', text='The time has not been reported yet, are you sure?')
       if dialog.exec():
           self.__list.takeItem(self.__list.row(self.__list_item))

      #  self.ticket_number.setText('#' + dialog.line.text().strip('# '))
       pass


    def show_time(self):
        hours = self.__seconds // 3600
        minutes = (self.__seconds % 3600) // 60
        seconds = (self.__seconds % 3600) % 60

        self.spent_time.setText('{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds))

    def update_time(self, seconds):
        self.__seconds += seconds

        if self.__seconds < 0:
            self.__seconds = 0

        self.show_time()


class MainWidget(QWidget):


    def __init__(self):
        QWidget.__init__(self)

        # Create the list
        self.task_list = QListWidget()

        self.add_task('Creazione ticket per Nicolas', '#9834')
        self.add_task('Eliminazione dei siti web su trv4', '#5032')
        self.add_task('Lettura delle favole della buona notte al virtualizzatore lisp-ve-pve-01, perchè senza non si spegne.', '#6834')

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

        self.layout.addWidget(self.task_list, 0, 0)
        self.layout.addLayout(self.bottom_layout, 1, 0)

        # Set the layout to the QWidget
        self.setLayout(self.layout)
        self.setContentsMargins(0, 0, 0, 0)

        # prepara il timer per contare il tempo

        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.count_time)
        self.timer.start(1000)


    def add_task(self, title, ticket=''):
        # Add to list a new item (item is simply an entry in your list)
        item = QListWidgetItem(self.task_list)

        # Instanciate a custom widget
        row = RowElement(title, ticket, self.task_list, item)
        item.setSizeHint(row.minimumSizeHint())

        # Associate the custom widget to the list entry
        self.task_list.setItemWidget(item, row)

    def count_time(self):
        for s in self.task_list.selectedItems():
            self.task_list.itemWidget(s).update_time(+1)



class MainWindow(QMainWindow):
    def __init__(self, widget):
        QMainWindow.__init__(self)
        self.setWindowTitle("Fast Switch Time Keeper")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.resize(460, 520)

        # Menu
        self.menu_bar = self.menuBar()
        self.options_menu = self.menu_bar.addMenu("Options")
        self.load_dump_action = self.options_menu.addAction("Always on top")

        self.load_dump_action.triggered.connect(lambda: self.setWindowFlag(Qt.WindowStaysOnTopHint, not bool(self.windowFlags() & Qt.WindowStaysOnTopHint)))

        self.menu_bar.installEventFilter(self)

        # Exit QAction
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_app)

        self.options_menu.addAction(exit_action)
        self.widget = widget
        self.setCentralWidget(self.widget)

        self.oldPos = self.pos()

        # apre i file di salvataggio delle config
        self.config = SaveFile('config.json')

        # sposta la finestra nell'ultima posizone in cui si trovava prima di chiudere
        self.move(self.config['window']['x'], self.config['window']['y'])

        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.config['window']['always_on_top'])

        self.show()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.MouseMove and event.buttons() & Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
        elif event.type() == QEvent.Type.MouseButtonPress:
            self.oldPos = event.globalPos()
            pass

        return super(MainWindow, self).eventFilter(source, event)

    def closeEvent(self, event):
        # aggiorna il dizionario delle config
        self.config['window']['x'] = self.x()
        self.config['window']['y'] = self.y()
        self.config['window']['always_on_top'] = bool(self.windowFlags() & Qt.WindowStaysOnTopHint)

        # salva su disco le config
        self.config.save()

    @Slot()
    def exit_app(self, checked):
        QApplication.quit()


if __name__ == "__main__":
    # Qt Application
    app = QApplication(sys.argv)
    app.setStyleSheet(default_window_style + '''
        QMenuBar, QMenuItem { background-color: #444f5d } 
        
        QListWidget { background-color: #232931; } 
        QListWidget::item { background-color: #353d48; } 
        QListWidget::item:selected { background-color: #5d54a4; } 
        
    ''')

    # https://colorhunt.co/palette/117601
    # QWidget
    main_widget = MainWidget()
    # QMainWindow using QWidget as central widget
    window = MainWindow(main_widget)

    # Execute application
    sys.exit(app.exec_())