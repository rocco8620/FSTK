import json
import logging
import os
import sys

import requests
import webbrowser
from PySide2 import QtGui, QtCore
from PySide2.QtCore import Qt, Slot, QPoint, QEvent, QTimer, Signal, QThread
from PySide2.QtGui import QFont, QDrag, QPixmap, QPainter, QCursor
from PySide2.QtWidgets import (QAction, QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QWidget,
                               QListWidget, QListWidgetItem, QGridLayout,
                               QSizePolicy, QAbstractItemView, QListView, QMenu)

from .Dialogs import (AskForTextDialog, ConfirmDialog, NewTaskDialog, HelpDialog, InformationDialog, ChangelogDialog,
                      StatisticsDialog, ConfigurationDialog, ShowNotesDialog, EditNotesDialog)

from .SaveFiles import SaveFile
from . import Globals, Utils, Palette, Redmine
from . import Updater


class QLabelClickable(QLabel):
    clicked = Signal()

    def mousePressEvent(self, ev):
        real_rect = self.fontMetrics().boundingRect(self.rect(), Qt.TextWordWrap, self.text())
        if real_rect.contains(ev.pos()):
            self.clicked.emit()
        else:
            ev.ignore()

class QPushButtonHoverable(QPushButton):
    mouse_entered = Signal(QPoint)
    mouse_leaved = Signal()

    def enterEvent(self, ev):
        self.mouse_entered.emit(self.mapToGlobal(QPoint(self.size().height(), self.size().width())))

    def leaveEvent(self, ev):
        self.mouse_leaved.emit()

class QPushButtonDoubleClickable(QPushButton):
    doubleClicked = Signal()
    singleClicked = Signal()

    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.singleClicked.emit)
        super().clicked.connect(self.checkDoubleClick)

    @Slot()
    def checkDoubleClick(self):
        if self.timer.isActive():
            self.timer.stop()
            self.doubleClicked.emit()

        else:
            self.timer.start(250)

class TaskElement(QWidget):
    _seconds = 0
    _color_group = 'No color'

    _saved = False
    _main_widget = None
    _list = None
    _list_item = None

    _notes = ''

    type = 'task'

    def __init__(self, options, main_widget, list_, list_item):
        super().__init__()
        self._main_widget = main_widget
        self._list = list_
        self._list_item = list_item

        # inizializzato in un metodo sotto
        self._notes_dialog = None
        self._notes = options.get('notes', '')

        fa5 = QFont('Font Awesome 5 Pro')

        self.box = QGridLayout()

        self.name = QLabelClickable(options['name'])
        self.name.setWordWrap(True)
        self.name.clicked.connect(self.edit_name)

        self.name.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.box.addWidget(self.name, 0, 0)
        self.box.setColumnStretch(0, 7)

        self.redmine_elements = QGridLayout()

        self.ticket_number = QPushButtonDoubleClickable(options['ticket_number'])
        self.ticket_number.setStyleSheet('''
            QPushButton { background-color: transparent; border: 0; padding: 0px }
            QPushButton[duplicated=true]  { border: 1px solid #fae661; padding: 2px }
        ''')

        self.ticket_number.singleClicked.connect(self.edit_ticket_number)
        self.ticket_number.doubleClicked.connect(self.open_ticket_main_webpage)
        self.redmine_elements.addWidget(self.ticket_number, 0, 0)

        title = options.get('ticket_title')
        self.ticket_title = QLabel(title if title is not None else 'Unable to find the specified ticket')
        self.ticket_title.setWordWrap(True)
        self.ticket_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.ticket_title.setFont(QFont('Mono', 9, italic=True))
        self.ticket_title.setProperty('invalid', title is None)
        self.ticket_title.setStyleSheet('''
            QLabel[counting=true] { color: #61ccfa; } 
            QLabel[counting=false] { color: #6e6e6e; }
            QLabel[invalid=true] { color: #fa7161; } 
        ''')
        self.redmine_elements.addWidget(self.ticket_title, 0, 1)
        self.redmine_elements.setColumnStretch(1, 7)

        # self.save_to_redmine = QPushButton('Save')
        # self.save_to_redmine.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        # self.redmine_elements.addWidget(self.save_to_redmine, alignment=Qt.AlignLeft)

        self.box.addLayout(self.redmine_elements, 1, 0)

        self.spent_time = QLabelClickable('00:00:00')
        self.spent_time.setFont(QFont('Mono', 16))
        self.spent_time.clicked.connect(self.open_ticket_new_time_webpage)

        self.box.addWidget(self.spent_time, 0, 1)
        self.box.setColumnStretch(1, 2)

        self.time_buttons = QHBoxLayout()

        self.add_time = QPushButton('plus')
        self.add_time.setFont(fa5)
        self.add_time.clicked.connect(self.add_time_f)
        self.add_time.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.add_time.setMaximumWidth(self.get_button_size()[0])
        self.add_time.setMinimumWidth(self.get_button_size()[0])
        self.add_time.setMinimumHeight(self.get_button_size()[1])

        self.notes = QPushButtonHoverable('sticky-note')
        self.notes.setFont(fa5)
        self.notes.mouse_entered.connect(self.show_notes)
        self.notes.mouse_leaved.connect(self.hide_notes)
        self.notes.clicked.connect(self.edit_notes)
        self.notes.setProperty('full', self._notes != '')
        self.notes.setStyleSheet('''
            QPushButton { padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4; }
            QPushButton[full=true] { border: 1px solid #fae661;  }
        ''')
        self.notes.setMaximumWidth(self.get_button_size()[0])
        self.notes.setMinimumWidth(self.get_button_size()[0])
        self.notes.setMinimumHeight(self.get_button_size()[1])

        self.sub_time = QPushButton('minus')
        self.sub_time.setFont(fa5)
        self.sub_time.clicked.connect(self.sub_time_f)
        self.sub_time.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.sub_time.setMaximumWidth(self.get_button_size()[0])
        self.sub_time.setMinimumWidth(self.get_button_size()[0])
        self.sub_time.setMinimumHeight(self.get_button_size()[1])

        self.time_buttons.addWidget(self.notes)
        self.time_buttons.addWidget(self.sub_time)
        self.time_buttons.addWidget(self.add_time)

        self.box.addLayout(self.time_buttons, 1, 1)

        self.del_record = QPushButton('trash')
        self.del_record.setFont(fa5)
        self.del_record.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.del_record.setMaximumWidth(self.get_button_size()[0])
        self.del_record.setMinimumWidth(self.get_button_size()[0])
        self.del_record.setMinimumHeight(self.get_button_size()[1])
        self.del_record.clicked.connect(self.del_task)

        self.box.addWidget(self.del_record, 0, 2)

        self.clear_record_time = QPushButton('broom')
        self.clear_record_time.setFont(fa5)
        self.clear_record_time.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.clear_record_time.setMaximumWidth(self.get_button_size()[0])
        self.clear_record_time.setMinimumWidth(self.get_button_size()[0])
        self.clear_record_time.setMinimumHeight(self.get_button_size()[1])
        self.clear_record_time.clicked.connect(self.clear_time)

        self.box.addWidget(self.clear_record_time, 1, 2)

        self.box.setColumnStretch(2, 2)

        self.setLayout(self.box)

        # aggiorna il label in modo da mostrare il tempo memorizzato
        self.set_time(options['elapsed_time'])

        # imposta flag per i visualizzare correttamente i gruppi colore
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet('TaskElement { border: solid ' + Palette.group_colors[options['color_group']] + '; border-width: 0px 0px 0px 5px; }')
        self._color_group = options['color_group']

    def contextMenuEvent(self, event):
        contex_menu = QMenu(self)

        ris = {}

        for name, color in Palette.group_colors.items():
            ris[contex_menu.addAction(name)] = (name, color)

        action = contex_menu.exec_(self.mapToGlobal(event.pos()))

        if action is not None:
            self.setStyleSheet('TaskElement { border: solid ' + ris[action][1] + '; border-width: 0px 0px 0px 5px; }')
            self._color_group = ris[action][0]
            Globals.config['stats']['task_color_set'] += 1

    def mousePressEvent(self, event):
        # ignora i click con il tasto destro per selezionare come attivo un widget
        if event.button() != Qt.RightButton:
            super().mousePressEvent(event)

            # se l'utente ha abilitato il reminder per switchare task lo resetto, poichè lui ha appena switchato tutto
            if Globals.config['options']['switch_reminder']['enabled']:
                self._main_widget._main_window.task_switch_timer.stop()
                self._main_widget._main_window.task_switch_timer.start(Globals.config['options']['switch_reminder']['interval'] * 60 * 1000)  # converto da minuti a millisecondi

        else:
            event.accept()

    # Azioni eseguite dall'interfaccia grafica

    @Slot()
    def add_time_f(self):
        self.update_time(+5 * 60)
        Globals.config['stats']['task_time_increased'] += 1

    @Slot()
    def sub_time_f(self):
        self.update_time(-5 * 60)
        Globals.config['stats']['task_time_decreased'] += 1

    @Slot()
    def open_ticket_new_time_webpage(self):
        n = self.ticket_number.text().strip('#')
        if n == '':
            return

        if not Globals.config['options']['redmine']['enabled']:
            InformationDialog('Open redmine ticket page in browser',
                              'If you want to open the redmine ticket page in the browser when double clicking on the task timer enable redmine integration '
                              'under<br><span style="font-style: italic">Options > Configuration > Enable redmine integration</span>',
                              min_width=550,
                              html=True).exec()
            return

        # se è abilitata la funzionalità di copia del tempo passato nel task
        if Globals.config['options']['redmine']['copy_time_to_clipboard']['enabled']:
            formatted_time = Redmine.seconds_to_time_entry_format(seconds=self.get_time(),
                                                                  rounding=Globals.config['options']['redmine']['copy_time_to_clipboard']['rounding'] * 60)
            QApplication.clipboard().setText(formatted_time)

        url = '{}/issues/{}/time_entries/new'.format(Globals.config['options']['redmine']['host'], n)

        try:
            webbrowser.open(url)
        except webbrowser.Error as e:
            logging.error('An error occurred trying to open the redmine web browser page for the url "{}": {}'.format(url, e))

    @Slot()
    def open_ticket_main_webpage(self):
        n = self.ticket_number.text().strip('#')
        if n == '':
            return

        if not Globals.config['options']['redmine']['enabled']:
            InformationDialog('Open redmine ticket page in browser',
                              'If you want to open the redmine ticket page in the browser when double clicking on the ticket number enable redmine integration under<br><span style="font-style: italic">Options > Configuration > Enable redmine integration</span>',
                              min_width=550,
                              html=True).exec()
            return

        url = '{}/issues/{}'.format(Globals.config['options']['redmine']['host'], n)

        try:
            webbrowser.open(url)
        except webbrowser.Error as e:
            logging.error('An error occurred trying to open the redmine web browser page for the url "{}": {}'.format(url, e))


    @Slot()
    def edit_ticket_number(self):
        dialog = AskForTextDialog(window_title='Set redmine ticket number',
                                  initial_text=self.ticket_number.text().strip('#'), length=250,
                                  validator=Utils.integer_number_validator)

        if not dialog.exec():  # se l'utente non ha cliccato su ok non procediamo
            return

        n = dialog.line.text().strip('# \t\n')

        self.ticket_number.setText('#' + n)

        if n == '':
            self.ticket_title.setText('')
        else:
            # aggiorno lo stato dei marker che indicano i task con numero ticket duplicato
            self._main_widget.update_duplicated_tickets_marker()

            if Globals.config['options']['redmine']['enabled']:
                self._main_widget.update_ticket_title(self.ticket_title, n)

        Globals.config['stats']['task_ticket_n_edited'] += 1

    @Slot()
    def edit_name(self):
        dialog = AskForTextDialog(window_title='Set task name',
                                  initial_text=self.name.text(), length=600,
                                  validator=Utils.not_empty_validator)
        if not dialog.exec():  # se l'utente non ha cliccato su ok non procediamo
            return

        t = dialog.line.text().strip()

        self.name.setText(t)
        self._list_item.setSizeHint(self.minimumSizeHint())
        Globals.config['stats']['task_name_edited'] += 1

    @Slot()
    def del_task(self):
        if self._notes == '':
            text = 'The task will be deleted, are you sure?'
        else:
            text = 'The task will be deleted, are you sure?\n--- THE TASK CONTAINS NOTES ---'

        dialog = ConfirmDialog(window_title='Confirm task deletion', text=text)

        if not dialog.exec():  # se l'utente non ha cliccato su ok non procediamo
            return

        self._list.takeItem(self._list.row(self._list_item))

        self._main_widget.update_total_time()
        # aggiorno lo stato dei marker che indicano i task con numero ticket duplicato
        self._main_widget.update_duplicated_tickets_marker()

        Globals.config['stats']['task_deleted'] += 1

    @Slot()
    def clear_time(self):
        dialog = ConfirmDialog(window_title='Confirm time deletion',
                               # text='The time has not been reported yet, are you sure?')
                               text='The time will be cleared, are you sure?')
        if not dialog.exec():  # se l'utente non ha cliccato su ok non procediamo
            return

        self.set_time(0)

        Globals.config['stats']['task_time_cleared'] += 1

    @Slot()
    def show_notes(self, pos):
        if self._notes_dialog is None and self._notes != '':
            self._notes_dialog = ShowNotesDialog(pos, self._notes)
            self._notes_dialog.show()

            Globals.config['stats']['task_notes_viewed'] += 1

    @Slot()
    def hide_notes(self):
        if self._notes_dialog is not None:
            self._notes_dialog.accept()
            self._notes_dialog = None

    @Slot()
    def edit_notes(self):
        dialog = EditNotesDialog(self._notes)

        if not dialog.exec():  # se l'utente non ha cliccato su ok non procediamo
            return

        self._notes = dialog.text.toPlainText().strip()
        # marco come piene o vuote le note per mostrare il giusto stato nella UI
        Utils.set_prop_and_refresh(self.notes, 'full', self._notes != '')

        Globals.config['stats']['task_notes_edited'] += 1

    # Metodi chiamati esternamente

    def update_time(self, seconds):
        self.set_time(self.get_time()+seconds)

    def get_time(self):
        return self._seconds

    def set_time(self, seconds):
        old_seconds = self._seconds
        self._seconds = seconds

        if self._seconds < 0:
            self._seconds = 0

        self.spent_time.setText(Utils.format_time(self._seconds))

        elements = [self.spent_time, self.add_time, self.sub_time, self.del_record, self.clear_record_time, self.ticket_number, self.name, self.ticket_title, self.notes]
        # valuta se è possibile che sia avvenuta un condizione che provocherebbe il cambio di colore degli elementi
        # se non può essere avvenuta skippa il codice di set dello style
        if (old_seconds == 0 and self._seconds != 0) or (old_seconds != 0 and self._seconds == 0) or (old_seconds == self._seconds == 0):
            for x in elements:
                Utils.set_prop_and_refresh(x, 'counting', self._seconds != 0)

        self._main_widget.update_total_time()

    def to_dict(self):
        return {
            'name': self.name.text(),
            'ticket': self.ticket_number.text().strip('#'),
            'elapsed_time': self._seconds,
            'color_group': self._color_group,
            'ticket_title': None if self.ticket_title.property('invalid') else self.ticket_title.text(),
            'notes': self._notes
        }

    # funzione per la formattazione degli elementi grafici
    def get_button_size(self):
        metric = self.name.fontMetrics().boundingRect('+5')
        width = metric.width() + 14
        height = metric.height() + 4

        return width, height


class ListWidget(QListWidget):
    _pixmap = None

    def __init__(self):
        super().__init__()

    def startDrag(self, supported_actions):
        Globals.config['stats']['task_reordered'] += 1

        drag = QDrag(self)
        drag.setMimeData(self.model().mimeData(self.selectedIndexes()))
        self._pixmap = QPixmap(self.viewport().visibleRegion().boundingRect().size())
        self._pixmap.fill(Qt.transparent)
        painter = QPainter(self._pixmap)

        for i in self.selectedIndexes():
            painter.drawPixmap(self.visualRect(i), self.viewport().grab(self.visualRect(i)))

        drag.setPixmap(self._pixmap)
        drag.setHotSpot(self.viewport().mapFromGlobal(QCursor.pos()))
        drag.exec_(supported_actions, Qt.MoveAction)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            for s in self.selectedItems():
                self.itemWidget(s).del_task()
        else:
            super().keyPressEvent(event)


class UpdateTicketTitleWorker(QThread):
    finished = Signal(dict)

    def __init__(self, ticket_numbers):
        QThread.__init__(self)
        self.ticket_numbers = ticket_numbers

    def run(self):
           result = Redmine.get_tickets_title(self.ticket_numbers)
           self.finished.emit(result)

class CheckRedmineCredsWorker(QThread):
    finished = Signal(bool)

    def run(self):
           result = Redmine.are_creds_valid()
           self.finished.emit(result)

class MainWidget(QWidget):

    _main_window = None

    def __init__(self):
        QWidget.__init__(self)

        # Create the list
        self.task_list = ListWidget()
        self.task_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.task_list.setMovement(QListView.Snap)
        self.task_list.setDefaultDropAction(Qt.MoveAction)
        self.task_list.setDragEnabled(True)
        self.task_list.viewport().setAcceptDrops(True)
        self.task_list.setDropIndicatorShown(True)
        self.task_list.setDragDropMode(QAbstractItemView.InternalMove)

        # flag che indica se il timer sta scorrendo o è in pausa
        self.running = True

        # QWidget Layout
        self.layout = QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setRowStretch(0, 1)

        self.layout.addWidget(self.task_list, 0, 0)

        # Set the layout to the QWidget
        self.setLayout(self.layout)
        self.setContentsMargins(0, 0, 0, 0)

        # prepara il timer per contare il tempo
        self.tasks_timer = QTimer()
        self.tasks_timer.setTimerType(Qt.PreciseTimer)
        self.tasks_timer.timeout.connect(self.count_time)
        self.tasks_timer.start(1000)

    @Slot()
    def create_task(self):
        dialog = NewTaskDialog()
        if not dialog.exec():  # se l'utente non ha cliccato su ok non procediamo
            return

        name = dialog.name.toPlainText()
        ticket_number = dialog.ticket_number.text()

        row = self.insert_task_in_list(name, '#' + ticket_number)
        Globals.config['stats']['task_created'] += 1

        if ticket_number != '':
            # aggiorno lo stato dei marker che indicano i task con numero ticket duplicato
            self.update_duplicated_tickets_marker()

            # se abilitato redmine lancio un thread per ottenere il titolo del ticket
            if Globals.config['options']['redmine']['enabled'] :
                self.update_ticket_title(row.ticket_title, ticket_number)
        else:
            Globals.config['stats']['task_created_without_ticket_number'] += 1

    def update_ticket_title(self, title_widget, ticket_number):
        title_widget.setText('...')

        def func(result):
            if result is not None:
                text = result.get(ticket_number)
                if text is not None:
                    title_widget.setText(text)
                    Utils.set_prop_and_refresh(title_widget, 'invalid', False)
                else:
                    title_widget.setText('Unable to find the specified ticket')
                    Utils.set_prop_and_refresh(title_widget, 'invalid', True)
                    logging.debug('Redmine api call returned dict not containing ticket title')
            else:
                Utils.set_prop_and_refresh(title_widget, 'invalid', True)
                logging.warning('Redmine api call returned empty dict searching for ticket title')

        Utils.launch_thread(UpdateTicketTitleWorker, [ticket_number], [('finished', func)])


    def insert_task_in_list(self, name, ticket_number='', elapsed_time=0, color_group='No color', ticket_title='', notes=''):
        # Add to list a new item (item is simply an entry in your list)
        item = QListWidgetItem()

        # Instanciate a custom widget
        row = TaskElement({
            'name': name,
            'ticket_number': ticket_number,
            'elapsed_time': elapsed_time,
            'color_group': color_group,
            'ticket_title': ticket_title,
            'notes': notes
        }, self, self.task_list, item)
        item.setSizeHint(row.minimumSizeHint())

        # Associate the custom widget to the list entry
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, row)

        return row

    def count_time(self):
        if self.running:
            for s in self.task_list.selectedItems():
                self.task_list.itemWidget(s).update_time(+1)


    def update_total_time(self):
        total = 0
        for t in widgets_of_type(list_=self.task_list, type_='task'):
            total += t.get_time()

        self.total_time.setText('Total time: {}'.format(Utils.format_time(total)))

    def update_duplicated_tickets_marker(self):
        tickets = {}

        for widget in widgets_of_type(list_=self.task_list, type_='task'):
            ticket_number = widget.ticket_number.text().strip('#')

            if ticket_number != '':
                if ticket_number not in tickets:
                    tickets[ticket_number] = []

                tickets[ticket_number].append(widget)

        for widgets in tickets.values():
            if len(widgets) > 1:
                # setto il colore di warning
                for w in widgets:
                    Utils.set_prop_and_refresh(w.ticket_number, 'duplicated', True)
            else:
                # rimuovo il colore di warning
                Utils.set_prop_and_refresh(widgets[0].ticket_number, 'duplicated', False)




class CheckUpdateWorker(QThread):
    finished = Signal(tuple) # (Success, Message, New Version)

    def run(self):
        try:
           r = requests.get(Globals.update_url)
           if r.status_code != 200:
               logging.info('Check for update failed: Expected 200 but got {} status code'.format(r.status_code))
               self.finished.emit((False, 'Check for update failed: Expected 200 but got {} status code'.format(r.status_code), None))
               return
        except requests.exceptions.ConnectionError as e:
            logging.info('Check for update failed: Connection failed connection to pypi.org api: {}'.format(e))
            self.finished.emit((False, 'Check for update failed: Connection failed connection to pypi.org api: {}'.format(e), None))
            return
        except Exception as e:
            logging.info('Check for update failed: Unknow error occurred: {}'.format(e))
            self.finished.emit((False, 'Check for update failed: Unknow error occurred: {}'.format(e), None))
            return

        try:
            resp = json.loads(r.text)
        except json.JSONDecodeError as e:
            logging.info('Check for update failed: Invalid json response: {}'.format(e))
            self.finished.emit((False, 'Check for update failed: Invalid json response: {}'.format(e), None))
            return

        logging.info('Latest available version: {}'.format(resp['info']['version'].strip()))
        self.finished.emit((True, None, resp['info']['version'].strip()))

def widgets_of_type(list_, type_):
    for i in range(list_.count()):
        w = list_.itemWidget(list_.item(i))
        if w.type == type_:
            yield w

class MainWindow(QMainWindow):
    # dizionario che contiene le informaizoni riguardo ai tempi tracciati
    tasks = None
    # timer che gestisce l'autosave
    tasks_autosave_timer = None
    # thread che cerca aggiornamenti per il software in background
    update_thread = None

    def __init__(self, widget):
        QMainWindow.__init__(self)

        self.widget = widget
        self.widget._main_window = self

        self.oldPos = self.pos()

        # carica il file di configurazione e applica alla finestra/applicazione le config salvate
        self.load_config()
        # carica gli elementi dell'interfaccia grafica
        self.load_ui()

        # sposta la finestra nell'ultima posizone in cui si trovava prima di chiudere
        self.move(Globals.config['window']['x'], Globals.config['window']['y'])
        self.resize(Globals.config['window']['w'], Globals.config['window']['h'])
        self.setWindowFlag(Qt.WindowStaysOnTopHint, Globals.config['window']['always_on_top'])

        self.set_run_pause(Globals.config['time_running'])

        # carica il file dei task esistenti e li visualizza nell'interfaccia grafica
        self.load_tasks()

        # mostro la finestra principale
        self.show()

        self.task_switch_timer = QTimer()
        self.task_switch_timer.setTimerType(Qt.VeryCoarseTimer)
        self.task_switch_timer.timeout.connect(self.remind_task_switch)

        if Globals.config['options']['switch_reminder']['enabled']:
            self.task_switch_timer.start(Globals.config['options']['switch_reminder']['interval'] * 60 * 1000) # converto da minuti a millisecondi

        # installo lo shortcut per il desktop
        self.install_desktop_shortcut()

        # Se è la prima esecuzione, mostro la finestra dei changelog
        self.show_changelog_if_needed()

        # verifico se ci sono aggiornamenti
        self.search_for_updates(show_errors=False)

        # questa deve essere l'ultima operazione
        # imposto la prima esecuzione a falso
        Globals.config['first_run'] = False

    def load_ui(self):
        self.setWindowTitle("Fast Switch Time Keeper")
        self.setWindowIcon(QtGui.QIcon(Utils.get_local_file_path('icon.png')))
        QtGui.QFontDatabase.addApplicationFont(Utils.get_local_file_path('Font Awesome 5 Pro-Light-300.otf'))
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.resize(460, 520)

        fa5 = QFont('Font Awesome 5 Pro')

        # Menu
        menu_bar = self.menuBar()
        options_menu = menu_bar.addMenu("Options")
        # always_on_top_action = options_menu.addAction("Always on top")
        # always_on_top_action.triggered.connect(self.toggle_window_stay_on_top)

        configuration_action = options_menu.addAction("Configuration")
        configuration_action.triggered.connect(self.edit_configuration)

        remove_desktop_shortcut_action = options_menu.addAction("Remove finder shortcut")
        remove_desktop_shortcut_action.triggered.connect(self.remove_desktop_shortcut)

        # Exit QAction
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_app)
        options_menu.addAction(exit_action)

        actions_menu = menu_bar.addMenu("Actions")

        self.refresh_titles_action = actions_menu.addAction("Refresh tickets titles")
        self.refresh_titles_action.triggered.connect(self.refresh_ticket_titles)

        self.refresh_titles_action.setEnabled(Globals.config['options']['redmine']['enabled'])

        self.clear_all_tasks_times_action = actions_menu.addAction("Clear all tasks times")
        self.clear_all_tasks_times_action.triggered.connect(self.clear_all_tasks_times)

        statistics_menu = menu_bar.addMenu("Statistics")
        usage_action = statistics_menu.addAction("Dev statistics")
        usage_action.triggered.connect(lambda: StatisticsDialog().exec())

        other_menu = menu_bar.addMenu("Other")
        help_action = other_menu.addAction("Help")
        help_action.setShortcut("Ctrl+H")
        help_action.triggered.connect(lambda: HelpDialog().exec())

        help_action = other_menu.addAction("Show changelog")
        help_action.triggered.connect(lambda: ChangelogDialog().exec())

        search_for_updates_action = other_menu.addAction("Search for updates")
        search_for_updates_action.triggered.connect(lambda: self.search_for_updates(show_errors=True))

        self.menubar_corner_holder = QWidget()
        menubar_corner_layout = QHBoxLayout(self.menubar_corner_holder)

        self.minimize_button = QPushButton('-')
        self.minimize_button.setFont(QFont('Mono', 10))
        self.minimize_button.setStyleSheet('padding-top: 2; padding-bottom: 2; padding-left: 8; padding-right: 8;')
        self.minimize_button.clicked.connect(self.showMinimized)

        menubar_corner_layout.addWidget(self.minimize_button)
        menubar_corner_layout.setMargin(4)

        menu_bar.setCornerWidget(self.menubar_corner_holder)
        menu_bar.installEventFilter(self)

        status_bar = self.statusBar()

        self.widget.total_time = QLabel('Total time: 00:00:00')

        self.add_task_button = QPushButton('plus')
        self.add_task_button.setFont(fa5)
        self.add_task_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.add_task_button.setMaximumWidth(100)
        self.add_task_button.setMinimumHeight(28)
        self.add_task_button.clicked.connect(self.widget.create_task)

        self.run_pause_button = QPushButton('pause' if Globals.config['options']['boomer_compatibility']['invert_run_pause_button'] else 'play')
        self.run_pause_button.setFont(fa5)
        self.run_pause_button.setStyleSheet('background-color: {}'.format('#630f31' if Globals.config['options']['boomer_compatibility']['invert_run_pause_button'] else '#42630f'))
        self.run_pause_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.run_pause_button.setMaximumWidth(100)
        self.add_task_button.setMinimumHeight(28)
        self.run_pause_button.clicked.connect(self.toggle_run_pause)


        status_bar.addPermanentWidget(self.add_task_button, 1)
        status_bar.addPermanentWidget(self.run_pause_button, 1)
        status_bar.addPermanentWidget(self.widget.total_time, 3)

        self.setCentralWidget(self.widget)

    def load_config(self):
        # apre i file di salvataggio delle config
        Globals.config = SaveFile(os.path.join(Globals.config_folder, Globals.config_file_name), filetype='config', default=Globals.default_config)

    def load_tasks(self):
        self.tasks = SaveFile(os.path.join(Globals.config_folder, Globals.tasks_file_name), filetype='tasks', default=Globals.default_tasks)

        # carico i task dal file di salvataggio all'interfaccia utente
        for t in self.tasks['current_tasks'].values():

            self.widget.insert_task_in_list(t['name'],
                                            '#' + t['ticket'],
                                            t['elapsed_time'],
                                            t['color_group'],
                                            t['ticket_title'],
                                            t['notes'])

        self.widget.update_total_time()
        # aggiorno lo stato dei marker che indicano i task con numero ticket duplicato
        self.widget.update_duplicated_tickets_marker()

        # lancio il timer per l'autosalvataggio dei tempi/task ogni minuto
        self.tasks_autosave_timer = QTimer()
        self.tasks_autosave_timer.timeout.connect(self.flush_tasks_to_savefile)
        self.tasks_autosave_timer.start(60 * 1000)

    def flush_tasks_to_savefile(self):
        logging.info("Autoflushing tasks to file...")
        self.tasks['current_tasks'].clear()
        i = 0
        for t in widgets_of_type(list_=self.widget.task_list, type_='task'):
            self.tasks['current_tasks'][str(i)] = t.to_dict()
            i += 1
        self.tasks.save()

    def search_for_updates(self, show_errors):
        def func(result):
            success_check, message_check, new_version = result

            if success_check:
                if new_version != Globals.version.strip():
                    dialog = ConfirmDialog(window_title='New update available',
                                           text='New version <b>v{}</b> is available, you are currently running version <b>v{}</b>.<br>'
                                                'The update is completely automatic and takes 1 minute.<br>'
                                                'Do you wish to update now?'.format(new_version, Globals.version),
                                           positive_button='Yes',
                                           negative_button='No',
                                           html=True)

                    if dialog.exec():  # se l'utente ha cliccato su aggiorna lanciamo l'aggiornamento
                        success_install, message_install = Updater.install_package(Globals.package_name, new_version)

                        if success_install:
                            InformationDialog('Software update', 'Update completed! FSTK will now restart').exec()
                            # imposto la flag first run per mostrare il changelog al riavvio
                            Globals.config['first_run'] = True
                            # salvo lo stato dei contatori e delle configurazioni
                            self.closeEvent(None)
                            # riavvio il processo
                            Updater.restart()
                        else:
                            message_install = message_install.replace("\n", "<br>")
                            InformationDialog('Software update', f'Update failed: {message_install}').exec()
                else:
                    if show_errors:
                        InformationDialog('Software update', f'You are running the latest version (<b>v{Globals.version.strip()}</b>)').exec()

            else:
                if show_errors:
                    InformationDialog('Software update', message_check).exec()

        # ----------------------------

        Utils.launch_thread(CheckUpdateWorker, None, [('finished', func)])

    def install_desktop_shortcut(self):
        desktop_file_path = os.path.join(Globals.desktop_folder, Globals.desktop_file_name)

        if not os.path.isfile(desktop_file_path):
            logging.debug('The desktop file does not exists, creating it now')
            with open(Utils.get_local_file_path(Globals.desktop_file_name), 'r') as o:
                desktop_file_content = o.read()

            desktop_file_content = desktop_file_content.format(
                                    Utils.get_local_file_path('icon.png'), # icona del software
                                    '"{}" -m fstk'.format(sys.executable) # path dell'eseguibile python e modulo da lanciare
                                   )

            with open(desktop_file_path, 'w') as o:
                o.write(desktop_file_content)

            logging.debug('Desktop file installed in {}'.format(desktop_file_path))

        else:
            logging.debug('The desktop file is already existing')

    def remove_desktop_shortcut(self):
        desktop_file_path = os.path.join(Globals.desktop_folder, Globals.desktop_file_name)
        logging.debug('Removing desktop shortcut')

        try:
            os.remove(desktop_file_path)
            InformationDialog('Desktop Shortcut', 'Desktop shortcut removed successfully').exec()
            logging.debug('Desktop shortcut remove successfully')
        except FileNotFoundError:
            logging.debug('Desktop desktop file not found while trying to remove it')
            InformationDialog('Desktop Shortcut', 'Desktop shortcut not present.').exec()

    def show_changelog_if_needed(self):
        if Globals.config['first_run']:
            ChangelogDialog().exec()

    def edit_configuration(self):
        dialog = ConfigurationDialog(Globals.config['options'])

        if not dialog.exec():  # se l'utente non ha cliccato su ok non procediamo
            return

        new_conf = dialog.result

        # applico modifiche/azioni varie in seguito alle possibili modifiche della conf

        # se è stato cambiato lo stato di questa opzione effettuo delle operazioni, altrimenti no
        if Utils.is_property_different(Globals.config['options'], new_conf, property=('redmine', 'enabled')):
            # attivo/disattivo delle opzioni
            self.refresh_titles_action.setEnabled(new_conf['redmine']['enabled'])

            if new_conf['redmine']['enabled']:
                # aggiorno i titoli dei ticket
                self.refresh_ticket_titles()
            else:
                # pulisco i titoli dei ticket
                self.clear_ticket_titles()

        # aggiorno le conf globali con le nuove
        Globals.config['options'] = new_conf


        if Globals.config['options']['redmine']['enabled']:

            def func(result):
                if not result:
                    InformationDialog('Warning', 'The redmine api key or host are invalid.').exec()

            Utils.launch_thread(CheckRedmineCredsWorker, None, signals_handlers=[('finished', func)])


        self.set_run_pause(Globals.config['time_running'])

        if Globals.config['options']['switch_reminder']['enabled']:
            self.task_switch_timer.start(Globals.config['options']['switch_reminder']['interval'] * 60 * 1000) # converto da minuti a millisecondi
        else:
            self.task_switch_timer.stop()


    def refresh_ticket_titles(self):
        Globals.config['stats']['ticket_titles_refreshed'] += 1

        tickets = []
        for t in widgets_of_type(list_=self.widget.task_list, type_='task'):
            # solo se il task ha un ticket number
            if t.ticket_number.text().strip('# ') != '':
                tickets.append(t.ticket_number.text().strip('# '))
                t.ticket_title.setText('...')

        def func(result):
            if result is not None:
                for t in widgets_of_type(list_=self.widget.task_list, type_='task'):
                    # solo se il task ha un ticket number
                    if t.ticket_number.text().strip('# ') != '':
                        text = result.get(t.ticket_number.text().strip('# '))
                        if text is not None:
                            t.ticket_title.setText(text)
                            Utils.set_prop_and_refresh(t.ticket_title, 'invalid', False)
                        else:
                            t.ticket_title.setText('Unable to find the specified ticket')
                            Utils.set_prop_and_refresh(t.ticket_title, 'invalid', True)
            else:
                logging.warning('Redmine api call returned empty dict searching for ticket title')


        Utils.launch_thread(UpdateTicketTitleWorker, [tickets], [('finished', func)])

    def clear_all_tasks_times(self):
        for t in widgets_of_type(list_=self.widget.task_list, type_='task'):
            t.set_time(0)


    def clear_ticket_titles(self):
        for t in widgets_of_type(list_=self.widget.task_list, type_='task'):
            t.ticket_title.setText('')
            t.ticket_title.setProperty('invalid', False)

    def set_run_pause(self, state):
        self.widget.running = state

        if self.widget.running:
            self.run_pause_button.setStyleSheet('background-color: {}'.format('#630f31' if Globals.config['options']['boomer_compatibility']['invert_run_pause_button'] else '#42630f'))
            self.run_pause_button.setText('pause' if Globals.config['options']['boomer_compatibility']['invert_run_pause_button'] else 'play')
        else:
            self.run_pause_button.setStyleSheet('background-color: {}'.format('#42630f' if Globals.config['options']['boomer_compatibility']['invert_run_pause_button'] else '#630f31'))
            self.run_pause_button.setText('play' if Globals.config['options']['boomer_compatibility']['invert_run_pause_button'] else 'pause')

    def toggle_run_pause(self):
        self.set_run_pause(not self.widget.running)

        Globals.config['stats']['time_run_toggled'] += 1

    def remind_task_switch(self):
        if len(self.widget.task_list.selectedItems()) > 0:
            selected_task = self.widget.task_list.itemWidget(self.widget.task_list.selectedItems()[0])
            name = selected_task.name.text()
            ticket_number = selected_task.ticket_number.text()
            InformationDialog('Remeber to switch active task', 'Are you still working on task "{}" {}?'.format(name, '(ticket: {})'.format(ticket_number) if ticket_number else ''), max_width=1000).show()
        else:
            InformationDialog('Remeber to switch active task', 'Have you started working on a task? (no task is currently selected)', max_width=1000).show()

    # @Slot()
    # def toggle_window_stay_on_top(self):
    #     print(int(self.windowFlags()))
    #     self.setWindowFlag(Qt.WindowStaysOnTopHint, not bool(self.windowFlags() & Qt.WindowStaysOnTopHint))
    #     self.show()
    #     self.activateWindow()
    #     print('Toggled: ', not bool(self.windowFlags() & Qt.WindowStaysOnTopHint))

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.MouseMove:
            if event.buttons() & Qt.LeftButton:
                delta = QPoint(event.globalPos() - self.oldPos)
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self.oldPos = event.globalPos()
        elif event.type() == QEvent.Type.MouseButtonPress:
            self.oldPos = event.globalPos()

        return super().eventFilter(source, event)

    def closeEvent(self, _):
        # aggiorna il dizionario delle config
        Globals.config['window']['x'] = self.x()
        Globals.config['window']['y'] = self.y()
        Globals.config['window']['h'] = self.height()
        Globals.config['window']['w'] = self.width()
        # Globals.config['window']['always_on_top'] = bool(self.windowFlags() & Qt.WindowStaysOnTopHint)
        Globals.config['window']['always_on_top'] = True
        Globals.config['time_running'] = self.widget.running

        # salva su disco le config
        Globals.config.save()

        # salva su disco i task/tempi
        self.flush_tasks_to_savefile()

        logging.debug('Cleaning lock file for the current execution')
        # rilascio il file di lock per questa esecuzione
        lock_file_path = os.path.join(Globals.config_folder, Globals.lock_file_name)
        os.remove(lock_file_path)

    @Slot()
    def exit_app(self, checked):
        self.closeEvent(None)
        QApplication.quit()



