import os
import re
import time
from threading import Thread

from hive_gns.database.access import write
from hive_gns.database.haf_sync import HafSync
from hive_gns.engine.hook_processor import HookProcessor

from hive_gns.tools import INSTALL_DIR

class GnsModules:

    def __init__(self) -> None:
        self.modules = {}
    
    def _is_valid_module(self, module):
        return bool(re.match(r'^[a-z]+[_]*$', module))

    def _init_modules_db(self):
        for m in self.modules:
            sql = f"""
                INSERT INTO gns.module_state (module)
                SELECT ('{m}')
                WHERE NOT EXISTS (SELECT * FROM gns.module_state WHERE module = '{m}');
            """
            write(sql)
    
    def _load(self):
        dir = f'{INSTALL_DIR}/modules'
        module_list = [f.name for f in os.scandir(dir) if self._is_valid_module(f.name)]
        for m in module_list:
            if m not in self.modules:
                self.modules[m] = HookProcessor(m)
        self._init_modules_db()
    
    def _refresh_modules(self):
        # TODO: periodically run _load()
        while True:
            self._load()
            time.sleep(120)

    def start(self):
        self._load()
        for m in self.modules:
            self.modules[m].start()

def run():
    # start  HAF sync
    HafSync.init()
    HafSync.toggle_sync()
    Thread(target=HafSync.main_loop).start()
    # start GNS modules
    while not HafSync.safe_to_process:
        time.sleep(1)
    modules = GnsModules()
    modules.start()
    # run server

if __name__ == '__main__':
    run()