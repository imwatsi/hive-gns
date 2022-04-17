import json
import time
from threading import Thread

from hive_gns.database.access import alter_schema, perform
from hive_gns.engine.gns_sys import GnsOps, GnsStatus
from hive_gns.database.haf_sync import HafSync
from hive_gns.tools import INSTALL_DIR

class HookProcessor:

    def __init__(self, module) -> None:
        self.module = module
        try:
            self.wd = f'{INSTALL_DIR}/modules/{self.module}'
            self.functions = open(f'{self.wd}/functions.sql', 'r').read()
            self.hooks = json.loads(open(f'{self.wd}/hooks.json', 'r').read())
            alter_schema(self.functions)
        except:
            # ignore incorrectly configured modules
            # TODO: log error
            pass

    def _get_op_types(self):
        res = {}
        for h in self.hooks:
            data = self.hooks[h]
            res[(data[0])] = [h, data[1]]
        return res
    
    def _get_op_type_ids(self, op_types):
        return [str(ot) for ot in op_types]
    
    def _main_loop(self):
        while True:
            if HafSync.safe_to_process:
                head_gns_op_id = GnsStatus.get_global_latest_gns_op_id()
                cur_gns_op_id = GnsStatus.get_module_latest_gns_op_id(self.module)
                if head_gns_op_id - cur_gns_op_id > 0:
                    op_types = self._get_op_types()
                    op_type_ids = self._get_op_type_ids(op_types.keys())
                    ops = GnsOps.get_ops_in_range(op_type_ids, cur_gns_op_id+1, head_gns_op_id)
                    for o in ops:
                        op_type_id = o['op_type_id']
                        notif_name = op_types[op_type_id][0]
                        func = op_types[op_type_id][1]
                        try:
                            done = perform(func, [o['gns_op_id'], o['created'], o['body'], notif_name])
                            GnsStatus.set_module_state(self.module, o['gns_op_id'])
                        except:
                            # TODO: log
                            return
                        # TODO: log errors
                    GnsStatus.set_module_state(self.module, head_gns_op_id)
            time.sleep(1)

    def start(self):
        Thread(target=self._main_loop).start()
        print(f"'{self.module}' module started.")
