
class _AbstractEngine (object):
    def __init__ (self, titles, exclude_titles, configs):
        if (exclude_titles == None):
            exclude_titles = []
        self._titles = titles
        self._exclude_titles = exclude_titles

    def fetch_messages (self):
        raise NotImplementedError
