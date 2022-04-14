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
            res[(data[0])] = [h, data[1]]
        return res
    
    def _main_loop(self):
        while True:
            head_gns_op_id = GnsStatus.get_global_latest_gns_op_id()
            cur_gns_op_id = GnsStatus.get_module_latest_gns_op_id(self.module)
            if head_gns_op_id - cur_gns_op_id > 0:
                op_types = self._get_op_types()
                ops = GnsOps.get_ops_in_range(cur_gns_op_id+1, head_gns_op_id, op_types.keys())
                for o in ops:
                    op_type_id = o['op_type_id']
                    notif_name = op_types[op_type_id][0]
                    func = op_types[op_type_id][1]
                    done = perform(func, [o['gns_op_id'], o['created'], o['body'], notif_name])
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