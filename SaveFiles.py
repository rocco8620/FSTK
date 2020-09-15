import json


class SaveFile(object):

    __data = None
    __file = None

    def __init__(self, filename):
        self.__file = open(filename, 'a+')
        self.__file.seek(0)

        try:
            self.__data = json.loads(self.__file.read())
        except json.decoder.JSONDecodeError as e:
            print('Exception occurred loading file: {}'.format(e))
            self.__data = {
                'window': {
                    'x': 0,
                    'y': 0
                },

            }

    def save(self):
        self.__file.seek(0)
        self.__file.truncate()
        self.__file.write(json.dumps(self.__data))
        self.__file.flush()

    def __getitem__(self, index):
        return self.__data[index]

    def __setitem__(self, key, value):
        self.__data[key] = value
