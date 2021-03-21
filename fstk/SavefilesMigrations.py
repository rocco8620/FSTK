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
            logging.debug("Nothing to migrate for {} savefile".format(filetype))
            return d

        tmp = copy.deepcopy(d)
        for i, j in zip(range(from_, to+1), range(from_+1, to+1)):
            # ottiene la funzione di migrazione
            f = getattr(self, '_migrate_{}_{}'.format(i, j), None)

            if f is None:
                logging.error("Missing {} savefile migrating version ({}) to lower version ({})".format(filetype, i, j))
                raise MigrationError("Missing {} savefile migrating from version {} to version {}".format(filetype, i, j))
            # applica la funzione di migrazione
            success, message = f(tmp)

            if not success:
                logging.error("Error migrating {} savefile from version {} to version {}: {}".format(filetype, i, j, message))
                raise MigrationError("Error migrating {} savefile from version {} to version {}: {}".format(filetype, i, j, message))
            else:
                logging.info("Successfully migrated {} savefile from version ({}) to version ({})".format(filetype, i, j))

        tmp['version'] = to
        return tmp


class ConfigMigrations(Migration):

    def migrate(self, from_, to, d):
        return super(ConfigMigrations, self)._migrate('config', from_, to, d)

    def _migrate_1_2(self, d):
        d['window']['w'] = 460
        d['window']['h'] = 520
        d['stats'] = {
            'total_created_tasks': 0,
        }
        return True, None


class TasksMigrations(Migration):

    def migrate(self, from_, to, d):
        return super(TasksMigrations, self)._migrate('tasks', from_, to, d)
