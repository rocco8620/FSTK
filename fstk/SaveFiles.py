import json
import logging

from fstk import SavefilesMigrations, Globals


class FlushFlagDict(dict):

    _flushed = None

    def __init__(self, flush_flag):
        super(FlushFlagDict, self).__init__(self)

        self._flushed = flush_flag

    def update(self, *args, **kwargs):
        self._flushed[0] = False
        return super(FlushFlagDict, self).update(*args, **kwargs)

    def __setitem__(self, key, value):
        super(FlushFlagDict, self).__setitem__(key, (self.__transparent_obj_conversion(value)))
        self._flushed[0] = False

    def __repr__(self):
        return "<FlushFlagDict ({}) {}>".format('Flushed' if self._flushed[0] else 'Not flushed', super(FlushFlagDict, self).__repr__())

    def __transparent_obj_conversion(self, e):
        if isinstance(e, dict):
            ffd = FlushFlagDict(flush_flag=self._flushed)
            ffd.update(e)
            return ffd
        # elif isinstance(e, list):
        #     ffl = FlushFlagList(flush_flag=self.__flushed)
        #     ffl += e
        #     return ffl
        else:
            return e

# class FlushFlagList(list):
#
#     __flushed = None
#
#     def __init__(self, flush_flag):
#         super(FlushFlagList, self).__init__(self)
#
#         self.__flushed = flush_flag
#
#     def append(self, e):
#         self.__flushed[0] = False
#         return super(FlushFlagList, self).append(self.__transparent_obj_conversion(e))
#
#     def pop(self, index=-1):
#         self.__flushed[0] = False
#         return super(FlushFlagList, self).pop(index)
#
#     def __setitem__(self, index, value):
#         self.__flushed[0] = False
#         return super(FlushFlagList, self).__setitem__(index, self.__transparent_obj_conversion(value))
#
#     def __iadd__(self, other):
#         self.__flushed[0] = False
#         return super(FlushFlagList, self).__iadd__(other)
#
#     def __add__(self, other):
#         self.__flushed[0] = False
#         return super(FlushFlagList, self).__add__(other)
#
#     def __repr__(self):
#         return "<FlushFlagList {}>".format(super(FlushFlagList, self).__repr__())
#
#     def __transparent_obj_conversion(self, e):
#         if isinstance(e, dict):
#             ffd = FlushFlagDict(flush_flag=self.__flushed)
#             ffd.update(e)
#             return ffd
#         elif isinstance(e, list):
#             ffl = FlushFlagList(flush_flag=self.__flushed)
#             ffl += e
#             return ffl
#         else:
#             return e

class UncopiableList(list):
    # lista che overrida __copy__ e __deepcopy__ in modo da evitare che una copy() o deepcopy() possa generarne un duplicato,
    # che provoca una perdita di referenza per chi manteneva una referenza all'oggetto orignale

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

class SaveFile(object):

    _data = None
    _file = None
    _flushed = None

    _filetypes_migrations = {
        'config': (SavefilesMigrations.ConfigMigrations, Globals.config_file_version),
        'tasks': (SavefilesMigrations.TasksMigrations, Globals.tasks_file_version)
    }

    def __init__(self, filename, filetype, default=None):
        if filetype not in self._filetypes_migrations:
            raise ValueError("The specified filetype does not exist ({})".format(filetype))

        self._file = open(filename, 'a+')
        self._file.seek(0)

        self._flushed = UncopiableList([True])

        try:
            self._data = json.loads(self._file.read(), object_hook=self._object_hook)
            # resetta la flag, che potrebbe essere stata modificata durante il caricamento in memoria dei dati
            self._flushed[0] = True
            # applica le migrazioni al file, nel caso che una versione precedente del software stesse usando un versione precedente del file di salvataggio
            mig = self._filetypes_migrations[filetype]
            self._data = mig[0]().migrate(self._data['version'], mig[1], self._data)
        except json.decoder.JSONDecodeError as e:
            logging.warning('Exception occurred loading config file ({}): {}. Using default.'.format(self._file.name, e))

            if default is None:
                self._data = {}
            else:
                self._data = self._convert_default(default)

            # setto a false la flag, poichè il file non era valido, in modo che venga scritto al prossimo salvataggio
            self._flushed[0] = False

    def save(self):
        if not self._flushed[0]:
            self._file.seek(0)
            self._file.truncate()
            self._file.write(json.dumps(self._data, indent=4))
            self._file.flush()
            self._flushed[0] = True
            logging.info("Flushing save file ({})...".format(self._file.name))
        else:
            logging.info("Save file ({}) nothing to flush.".format(self._file.name))

    def _object_hook(self, e):
        if isinstance(e, dict):
            ffd = FlushFlagDict(flush_flag=self._flushed)
            ffd.update(e)
            return ffd
        else:
            raise ValueError("L'oggetto passato ({}) non è di un tipo permesso ({}).".format(e, type(e)))

    def _convert_default(self, o):
        if isinstance(o, dict):
            ffd = FlushFlagDict(flush_flag=self._flushed)
            ffd.update({k: self._convert_default(o[k]) for k in o})
            return ffd

        # elif isinstance(o, list):
        #     ffl = FlushFlagList(flush_flag=self.__flushed)
        #     ffl += [self.__convert_default(e) for e in o]
        #     return ffl

        return o

    def __getitem__(self, index):
        return self._data[index]

    def __setitem__(self, key, value):
        self._data[key] = value
        self._flushed[0] = False

    def __repr__(self):
        return repr(self._data)
