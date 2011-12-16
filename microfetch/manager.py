import engines

class EnginesManager (object):
    def __init__ (self, engine_names, titles, configs_per_engine = {}):
        self._engines = []
        for eng in engine_names:
            self._engines.append(vars(engines)[unicode(eng)+'Engine'](titles, configs_per_engine.get(eng)))
        
    def fetch_messages (self):
        msgs = []
        for eng in self._engines:
            msgs = eng.fetch_messages()
        return msgs;
