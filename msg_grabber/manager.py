import engines

class enginesManager (object):
    def __init__ (self, engine_names, titles, configs_per_engine = {}):
        self._engines = []
        for eng in engine_names:
            configs_for_cur_engine = configs_per_engine.get(eng) or {}
            configs_for_cur_engine['titles'] = (configs_for_cur_engine.get('titles') or set()) | titles
            self._engines.append(vars(engines)[unicode(eng)+'Engine'](configs_for_cur_engine))
        
    def fetch_messages (self):
        msgs = []
        for eng in self._engines:
            msgs = eng.fetch_messages()
        return msgs;
