import os
import tempfile

import engines

class EnginesManager (object):
    def __init__ (self, engine_names, titles, configs_per_engine = {}):
        self._engines = []
        for eng in engine_names:
            self._engines.append(vars(engines)[unicode(eng)+'Engine'](titles, configs_per_engine.get(eng)))
            
        self.path_cache = tempfile.mkdtemp()+"/"
        self.path_cached_avatars = self.path_cache + "avatars/"
        if not os.path.isdir(self.path_cached_avatars):
            os.mkdir(self.path_cached_avatars)
        
    def fetch_messages (self):
        msgs = []
        for eng in self._engines:
            msgs = eng.fetch_messages()
        return msgs;
