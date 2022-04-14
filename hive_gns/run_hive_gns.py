from threading import Thread

from hive_gns.engine.hook_processor import HookProcessorCore
from hive_gns.database.haf_sync import HafSync

class GnsModules:

    def __init__(self) -> None:
        self.modules = {}
    
    def _load(self):
        # load core
        self.modules['core'] = HookProcessorCore()
        #TODO: loop through dirs
    
    def start(self):
        for m in self.modules:
            m.start()

def run():
    # start  HAF sync
    HafSync.init()
    HafSync.toggle_sync()
    Thread(target=HafSync.main_loop).start()
    # start GNS modules
    modules = GnsModules()
    modules.start()
    # run server

