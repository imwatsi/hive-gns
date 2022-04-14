import json
import time
from threading import Thread

from hive_gns.database.access import perform
from hive_gns.engine.gns_sys import GnsOps, GnsStatus
from hive_gns.tools import INSTALL_DIR

class HookProcessorCore:

    def __init__(self) -> None:
        self.module = 'core'
        self.wd = f'{INSTALL_DIR}/modules/{self.module}'
        self.functions = open(f'{self.wd}/functions.sql', 'r').read()
        self.hooks = json.loads(open(f'{self.wd}/hooks.json', 'r').read())
    
    def _get_op_types(self):
        res = {}
        for h in self.hooks:
            data = self.hooks[h]
            res[(data[0])] = data[1]
        return res
    
    def _main_loop(self):
        while True:
            head_gns_op_id = GnsStatus.get_global_latest_gns_op_id()
            cur_gns_op_id = GnsStatus.get_module_latest_gns_op_id(self.module)
            if head_gns_op_id - cur_gns_op_id > 0:
                op_types = self._get_op_types()
                ops = GnsOps.get_ops_in_range(cur_gns_op_id+1, head_gns_op_id, op_types.keys())
                for o in ops:
                    func = op_types[o['op_type_id']]
                    done = perform(func, [o['gns_op_id', 'created', 'body']])
                    # TODO: error notifications
                    # TODO: possibly shutdown module on error
                GnsStatus.set_module_state(self.module, head_gns_op_id)
            time.sleep(1)

    def start(self):
        Thread(target=self._main_loop).start()
        print("'{self.module}' module started.")

class HookProcessorCustom:

    def __init__(self, module, refresh_time) -> None:
        pass