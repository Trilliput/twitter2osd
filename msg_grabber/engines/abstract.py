
class abstractEngine (object):
    def __init__ (self, configs):
        self._titles = configs['titles']

    def fetch_messages (self):
        raise NotImplementedError
