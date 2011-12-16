
class _AbstractEngine (object):
    def __init__ (self, titles, configs):
        self._titles = titles

    def fetch_messages (self):
        raise NotImplementedError
