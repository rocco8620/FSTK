import copy
import logging


class MigrationError(Exception):
    pass

class Migration(object):
    # applica le funzioni di migrazione in sequenza, in modo da convertire i dati da un formato a quello successivo
    def _migrate(self, filetype, from_, to, d):
        if to < from_:
            logging.error("Tryed to migrate {} savefile from higher version ({}) to lower version ({})".format(filetype, from_, to))
            raise MigrationError("Can't migrate {} savefile from higher version ({}) to lower version ({})".format(filetype, from_, to))

        # nulla da fare, siamo già alla versione corretta
        if from_ == to:
            logging.debug("Nothing to migrate for {} savefile. Current version: {}".format(filetype, to))
            return d

        tmp = copy.deepcopy(d)
        for i, j in zip(range(from_, to+1), range(from_+1, to+1)):
            # ottiene la funzione di migrazione
            f = getattr(self, '_migrate_{}_{}'.format(i, j), None)

            if f is None:
                logging.error("Missing {} savefile migrating version ({}) from version ({})".format(filetype, i, j))
                raise MigrationError("Missing {} savefile migrating from version {} to version {}".format(filetype, i, j))
            # applica la funzione di migrazione
            success, message = f(tmp)

            if not success:
                logging.error("Error migrating {} savefile from version {} to version {}: {}".format(filetype, i, j, message))
                raise MigrationError("Error migrating {} savefile from version {} to version {}: {}".format(filetype, i, j, message))
            else:
                logging.info("Successfully migrated {} savefile from version {} to version {}".format(filetype, i, j))

        tmp['version'] = to
        return tmp


class ConfigMigrations(Migration):

    def migrate(self, from_, to, d):
        return super()._migrate('config', from_, to, d)

    def _migrate_1_2(self, d):
        d['window']['w'] = 460
        d['window']['h'] = 520
        d['stats'] = {
            'total_created_tasks': 0,
        }

        return True, None

    def _migrate_2_3(self, d):
        d['options'] = {
            'redmine': {
                'enabled': False,
                'host': '',
                'apikey': '',
                'task_name_from_ticket': False
            }
        }

        return True, None

    def _migrate_3_4(self, d):
        d['time_running'] = True

        return True, None

    def _migrate_4_5(self, d):
        del d['stats']['total_created_tasks']

        d['stats']['task_created'] = 0
        d['stats']['task_color_set'] = 0
        d['stats']['task_name_edited'] = 0
        d['stats']['task_ticket_n_edited'] = 0
        d['stats']['task_time_increased'] = 0
        d['stats']['task_time_decreased'] = 0
        d['stats']['task_time_cleared'] = 0
        d['stats']['task_deleted'] = 0
        d['stats']['task_notes_edited'] = 0
        d['stats']['task_notes_viewed'] = 0
        d['stats']['task_reordered'] = 0

        d['stats']['ticket_titles_refreshed'] = 0
        d['stats']['time_run_toggled'] = 0
        d['stats']['task_created_without_ticket_number'] = 0

        d['options']['boomer_compatibility'] = {
            'invert_run_pause_button': False
        }

        return True, None

    def _migrate_5_6(self, d):
        d['options']['switch_reminder'] = {
            'enabled': False,
            'interval': 60
        }

        return True, None

    def _migrate_6_7(selfself, d):
        d['options']['redmine']['copy_time_to_clipboard'] = {
            'enabled': False,
            'rounding': 10
        }

        return True, None


class TasksMigrations(Migration):

    def migrate(self, from_, to, d):
        return super()._migrate('tasks', from_, to, d)

    def _migrate_1_2(self, d):
        for t in d['current_tasks']:
            d['current_tasks'][t]['color_group'] = 'No color'

        return True, None

    def _migrate_2_3(self, d):
        for t in d['current_tasks']:
            d['current_tasks'][t]['ticket_title'] = ''

        return True, None

    def _migrate_3_4(self, d):
        for t in d['current_tasks']:
            d['current_tasks'][t]['notes'] = ''

        return True, None

