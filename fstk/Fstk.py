import json
import logging
import os
import sys

import requests
from PySide2 import QtGui
from PySide2.QtCore import Qt, Slot, QPoint, QEvent, QTimer, Signal, QThread
from PySide2.QtGui import QFont
from PySide2.QtWidgets import (QAction, QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QWidget,
                               QListWidget, QListWidgetItem, QGridLayout,
                               QSizePolicy, QSizeGrip)

from .Dialogs import AskForTextDialog, ConfirmDialog, NewTaskDialog, HelpDialog, InformationDialog, ChangelogDialog
from .SaveFiles import SaveFile
from . import Globals, Utils
from . import Updater


class QLabelClickable(QLabel):
    clicked = Signal()

    def __init__(self, parent=None):
        QLabel.__init__(self, parent)

    def mousePressEvent(self, ev):
        self.clicked.emit()


class RowElement(QWidget):
    __seconds = 0

    __saved = False
    __list = None
    __list_item = None

    def __init__(self, name, ticket_number, elapsed_time, list, list_item):
        super(RowElement, self).__init__(None)
        self.__list = list
        self.__list_item = list_item
        self.__seconds = elapsed_time

        self.box = QGridLayout()

        self.name = QLabelClickable(name)
        self.name.setWordWrap(True)
        self.name.clicked.connect(self.edit_name)

        self.name.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.box.addWidget(self.name, 0, 0)
        self.box.setColumnStretch(0, 7)

        self.redmine_elements = QHBoxLayout()

        self.ticket_number = QPushButton(ticket_number)
        self.ticket_number.setStyleSheet('border: 0; background-color: transparent')
        self.ticket_number.clicked.connect(self.edit_ticket_number)
        self.redmine_elements.addWidget(self.ticket_number)

        # self.save_to_redmine = QPushButton('Save')
        # self.save_to_redmine.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        # self.redmine_elements.addWidget(self.save_to_redmine, alignment=Qt.AlignLeft)

        self.redmine_elements.addStretch()

        self.box.addLayout(self.redmine_elements, 1, 0)

        self.spent_time = QLabel('00:00:00')
        self.spent_time.setFont(QFont('Mono', 16))

        self.box.addWidget(self.spent_time, 0, 1)
        self.box.setColumnStretch(1, 2)

        self.time_buttons = QHBoxLayout()

        self.add_time = QPushButton("+5")
        self.add_time.clicked.connect(lambda: self.update_time(+5 * 60))
        self.add_time.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')

        self.sub_time = QPushButton("-5")
        self.sub_time.clicked.connect(lambda: self.update_time(-5 * 60))
        self.sub_time.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.sub_time.setMaximumWidth(self.set_min_size_from_content(self.add_time))

        self.time_buttons.addWidget(self.sub_time)
        self.time_buttons.addWidget(self.add_time)

        self.box.addLayout(self.time_buttons, 1, 1)

        self.del_record = QPushButton("X")
        self.del_record.setStyleSheet('padding-top: 1; padding-bottom: 1; padding-left: 4; padding-right: 4;')
        self.del_record.setMaximumWidth(self.set_min_size_from_content(self.add_time))
        self.del_record.setMinimumWidth(self.set_min_size_from_content(self.add_time))
        self.del_record.clicked.connect(lambda: self.del_task())

        self.box.addWidget(self.del_record, 0, 2)

        self.box.setColumnStretch(2, 2)

        self.setLayout(self.box)

        self.show_time()

    # Azioni eseguite dall'interfaccia grafica
    @Slot()
    def edit_ticket_number(self):
        dialog = AskForTextDialog(window_title='Set redmine ticket number',
                                  initial_text=self.ticket_number.text().strip('#'), length=250)

        if not dialog.exec():  # se l'utente non ha cliccato su ok non procediamo
            return

        n = dialog.line.text().strip('# ')

        try:
            n = int(n)
            if 0 < n < 1000000:
                self.ticket_number.setText('#' + str(n))
        except ValueError:
            pass

    @Slot()
    def edit_name(self):
        dialog = AskForTextDialog(window_title='Set task name',
                                  initial_text=self.name.text(), length=600)
        if not dialog.exec():  # se l'utente non ha cliccato su ok non procediamo
            return

        t = dialog.line.text().strip()

        self.name.setText(t)
        self.__list_item.setSizeHint(self.minimumSizeHint())

    @Slot()
    def del_task(self):
        dialog = ConfirmDialog(window_title='Confirm task deletion',
                               text='The time has not been reported yet, are you sure?')
        if not dialog.exec():  # se l'utente non ha cliccato su ok non procediamo
            return

        self.__list.takeItem(self.__list.row(self.__list_item))

    # Metodi chiamati esternmente

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

    def to_dict(self):
        return {'name': self.name.text(), 'ticket': self.ticket_number.text().strip('#'),
                'elapsed_time': self.__seconds}

    # funzione per la formattazione degli elementi grafici
    @staticmethod
    def set_min_size_from_content(elem):
        width = elem.fontMetrics().boundingRect(elem.text()).width() + 14
        elem.setMaximumWidth(width)

        return width


class MainWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        # Create the list
        self.task_list = QListWidget()

        self.add_task_button = QPushButton("+")
        self.add_task_button.setFont(QFont('Mono', 17, weight=QFont.Bold))
        self.add_task_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.add_task_button.clicked.connect(self.create_task)

        self.grip = QSizeGrip(self)
        self.grip.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        # QWidget Layout
        self.layout = QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setRowStretch(0, 1)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.bottom_layout.addWidget(self.add_task_button)
        self.bottom_layout.addWidget(self.grip)

        self.layout.addWidget(self.task_list, 0, 0)
        self.layout.addLayout(self.bottom_layout, 1, 0)

        # Set the layout to the QWidget
        self.setLayout(self.layout)
        self.setContentsMargins(0, 0, 0, 0)

        # prepara il timer per contare il tempo

        self.task_timer = QTimer()
        self.task_timer.setTimerType(Qt.PreciseTimer)
        self.task_timer.timeout.connect(self.count_time)
        self.task_timer.start(1000)

    @Slot()
    def create_task(self):
        dialog = NewTaskDialog()
        if not dialog.exec():  # se l'utente non ha cliccato su ok non procediamo
            return

        name = dialog.name.toPlainText()
        ticket_number = dialog.ticket_number.text()

        self.insert_task_in_list(name, ticket_number)

    def insert_task_in_list(self, name, ticket_number='', elapsed_time=0):
        # Add to list a new item (item is simply an entry in your list)
        item = QListWidgetItem(self.task_list)

        # Instanciate a custom widget
        row = RowElement(name, ticket_number, elapsed_time, self.task_list, item)
        item.setSizeHint(row.minimumSizeHint())

        # Associate the custom widget to the list entry
        self.task_list.setItemWidget(item, row)

    def count_time(self):
        for s in self.task_list.selectedItems():
            self.task_list.itemWidget(s).update_time(+1)




class CheckUpdateWorker(QThread):
    finished = Signal(tuple) # (Success, Message, New Version)

    def run(self):
        try:
           r = requests.get(Globals.update_url)
           if r.status_code != 200:
               logging.info('Check for update failed: Expected 200 but got {} status code'.format(r.status_code))
               self.finished.emit((False, 'Check for update failed: Expected 200 but got {} status code'.format(r.status_code), None))
               return
        except Exception as e:
            raise e

        try:
            resp = json.loads(r.text)
        except json.JSONDecodeError as e:
            logging.info('Check for update failed: Invalid json response: {}'.format(e))
            self.finished.emit((False, 'Check for update failed: Invalid json response: {}'.format(e), None))
            return

        logging.info('Latest available version: {}'.format(resp['info']['version'].strip()))
        self.finished.emit((True, None, resp['info']['version'].strip()))


class MainWindow(QMainWindow):
    # dizionario che contiene le informaizoni riguardo ai tempi tracciati
    times = None
    # dizionario che contiene le configurazioni attuali
    config = None
    # timer che gestisce l'autosave
    tasks_autosave_timer = None
    # thread che cerca aggiornamenti per il software in background
    update_thread = None

    def __init__(self, widget):
        QMainWindow.__init__(self)

        self.widget = widget
        self.load_ui()

        self.oldPos = self.pos()

        # carica il file di configurazione e applica alla finestra/applicazione le config salvate
        self.load_config()
        # carica il file dei task esistenti e li visualizza nell'interfaccia grafica
        self.load_tasks()

        # mostro la finestra principale
        self.show()

        # installo lo shortcut per il desktop
        self.install_desktop_shortcut()

        # Se è la prima esecuzione, mostro la finestra dei changelog
        self.show_changelog()

        # verifico se ci sono aggiornamenti
        self.search_for_updates(show_errors=False)

        # questa deve essere l'ultima operazione
        # imposto la prima esecuzione a falso
        self.config['first_run'] = False

    def load_ui(self):
        self.setWindowTitle("Fast Switch Time Keeper")
        self.setWindowIcon(QtGui.QIcon(Utils.get_local_file_path('icon.png')))
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.resize(460, 520)

        # Menu
        menu_bar = self.menuBar()
        options_menu = menu_bar.addMenu("Options")
        # always_on_top_action = options_menu.addAction("Always on top")
        # always_on_top_action.triggered.connect(self.toggle_window_stay_on_top)

        remove_deskto_shortcut_action = options_menu.addAction("Remove finder shortcut")
        remove_deskto_shortcut_action.triggered.connect(self.remove_deskto_shortcut)

        other_menu = menu_bar.addMenu("Other")
        help_action = other_menu.addAction("Help")
        help_action.triggered.connect(lambda: HelpDialog().exec())

        help_action = other_menu.addAction("Show changelog")
        help_action.triggered.connect(lambda: ChangelogDialog().exec())

        search_for_updates_action = other_menu.addAction("Search for updates")
        search_for_updates_action.triggered.connect(lambda: self.search_for_updates(show_errors=True))


        # Exit QAction
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_app)

        options_menu.addAction(exit_action)
        menu_bar.installEventFilter(self)

        self.setCentralWidget(self.widget)

    def load_config(self):
        # apre i file di salvataggio delle config
        self.config = SaveFile(os.path.join(Globals.config_folder, Globals.config_file_name), default=Globals.default_config)
        # sposta la finestra nell'ultima posizone in cui si trovava prima di chiudere
        self.move(self.config['window']['x'], self.config['window']['y'])
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.config['window']['always_on_top'])

    def load_tasks(self):
        self.times = SaveFile(os.path.join(Globals.config_folder, Globals.times_file_name), default=Globals.default_times)

        # carico i task dal file di salvataggio all'interfaccia utente
        for t in self.times['current_tasks'].values():
            self.widget.insert_task_in_list(t['name'], '#' + t['ticket'], t['elapsed_time'])

        # lancio il timer per l'autosalvataggio dei tempi/task ogni minuto
        self.tasks_autosave_timer = QTimer()
        self.tasks_autosave_timer.timeout.connect(self.flush_tasks_to_savefile)
        self.tasks_autosave_timer.start(60 * 1000)

    def flush_tasks_to_savefile(self):
        logging.info("Autoflushing times to file...")
        self.times['current_tasks'].clear()

        for i in range(self.widget.task_list.count()):
            t = self.widget.task_list.itemWidget(self.widget.task_list.item(i))
            self.times['current_tasks'][str(i)] = t.to_dict()

        self.times.save()

    def search_for_updates(self, show_errors):
        def func(result):
            success_check, message_check, new_version = result

            if success_check:
                if new_version != Globals.version.strip():
                    dialog = ConfirmDialog(window_title='New update available',
                                           text='New version <b>v{}</b> is available, you are currently running version <b>v{}</b>.<br>'
                                                'The update is completely automatic and takes 1 minute.<br>'
                                                'Do you wan to update now?'.format(new_version, Globals.version),
                                           positive_button='Yes',
                                           negative_button='No',
                                           html=True)

                    if dialog.exec():  # se l'utente ha cliccato su aggiorna lanciamo l'aggiornamento
                        success_install, message_install = Updater.install_package(Globals.package_name)

                        if success_install:
                            InformationDialog('Software update', 'Update completed! FSTK will now restart').exec()
                            # imposto la flag first run per mostrare il changelog al riavvio
                            self.config['first_run'] = True
                            # salvo lo stato dei contatori e delle configurazioni
                            self.closeEvent(None)
                            # riavvio il processo
                            Updater.restart()
                        else:
                            InformationDialog('Software update', 'Update failed: {}'.format(message_install)).exec()
                else:
                    if show_errors:
                        InformationDialog('Software update', 'You are running the lastest version (<b>v{}</b>)'.format(Globals.version.strip())).exec()

            else:
                if show_errors:
                    InformationDialog('Software update', message_check).exec()

        # ----------------------------

        self.update_thread = CheckUpdateWorker()
        #QCoreApplication.processEvents()
        self.update_thread.finished.connect(func)
        self.update_thread.finished.connect(self.update_thread.deleteLater)
        self.update_thread.start()

    def install_desktop_shortcut(self):
        desktop_file_path = os.path.join(Globals.desktop_folder, Globals.desktop_file_name)

        if not os.path.isfile(desktop_file_path):
            logging.debug('The desktop file does not exists, creating it now')
            with open(Utils.get_local_file_path(Globals.desktop_file_name), 'r') as o:
                desktop_file_content = o.read()

            desktop_file_content = desktop_file_content.format(
                                    Utils.get_local_file_path('icon.png'), # icona del software
                                    '"{}" -m fstk'.format(sys.executable)
                                   )

            with open(desktop_file_path, 'w') as o:
                o.write(desktop_file_content)

            logging.debug('Desktop file installed in {}'.format(desktop_file_path))

        else:
            logging.debug('The desktop file is already existing')

    def remove_deskto_shortcut(self):
        desktop_file_path = os.path.join(Globals.desktop_folder, Globals.desktop_file_name)
        logging.debug('Removing desktop shortcut')

        try:
            os.remove(desktop_file_path)
            InformationDialog('Desktop Shortcut', 'Desktop shortcut removed successfully').exec()
            logging.debug('Desktop shortcut remove successfully')
        except FileNotFoundError:
            logging.debug('Desktop desktop file not found while trying to remove it')
            InformationDialog('Desktop Shortcut', 'Desktop shortcut not present.').exec()

    def show_changelog(self):
        if self.config['first_run']:
            ChangelogDialog().exec()

    # @Slot()
    # def toggle_window_stay_on_top(self):
    #     print(int(self.windowFlags()))
    #     self.setWindowFlag(Qt.WindowStaysOnTopHint, not bool(self.windowFlags() & Qt.WindowStaysOnTopHint))
    #     self.show()
    #     self.activateWindow()
    #     print('Toggled: ', not bool(self.windowFlags() & Qt.WindowStaysOnTopHint))

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.MouseMove and event.buttons() & Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
        elif event.type() == QEvent.Type.MouseButtonPress:
            self.oldPos = event.globalPos()

        return super(MainWindow, self).eventFilter(source, event)

    def closeEvent(self, _):
        # aggiorna il dizionario delle config
        self.config['window']['x'] = self.x()
        self.config['window']['y'] = self.y()
        # self.config['window']['always_on_top'] = bool(self.windowFlags() & Qt.WindowStaysOnTopHint)
        self.config['window']['always_on_top'] = True

        # salva su disco le config e tempi/task
        self.config.save()

        self.flush_tasks_to_savefile()

        logging.debug('Cleaning lock file for the current execution')
        # rilascio il file di lock per questa esecuzione
        lock_file_path = os.path.join(Globals.config_folder, Globals.lock_file_name)
        os.remove(lock_file_path)

    @Slot()
    def exit_app(self, checked):
        self.closeEvent(None)
        QApplication.quit()


