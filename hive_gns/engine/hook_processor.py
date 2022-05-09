import json
import time
from threading import Thread

from hive_gns.database.access import alter_schema, perform
from hive_gns.engine.gns_sys import GnsOps, GnsStatus
from hive_gns.database.haf_sync import HafSync
from hive_gns.engine.verifications import ExternalVerifications
from hive_gns.server import system_status
from hive_gns.tools import INSTALL_DIR

REQ_VERIFY = {
    'splinterlands': ExternalVerifications.splinterlands
}


class HookProcessor:

    def __init__(self, module) -> None:
        self.module = module
        self.good = False
        try:
            self.wd = f'{INSTALL_DIR}/modules/{self.module}'
            self.functions = open(f'{self.wd}/functions.sql', 'r').read()
            self.hooks = json.loads(open(f'{self.wd}/hooks.json', 'r').read())
            self._get_notif_details()
            alter_schema(self.functions)
            self.good = True
        except Exception as e:
            print(e)
            print(f"ERROR: ignoring incorrectly configured module: '{self.module}'")
            # TODO: log error
            pass

    def _get_notif_details(self):
        notifs = {}
        type_ids = []
        for h in self.hooks:
            data = self.hooks[h]
            op_type_id = data[0]
            notifs[op_type_id] = {
                'name': h,
                'func': data[1],
                'code': data[2]
            }
            if op_type_id not in type_ids:
                type_ids.append(op_type_id)
        self.notifs = notifs
        self.type_ids = type_ids
    
    def _get_notif_code(self, op_type_id):
        notif_name = self.notifs[op_type_id]['code']
        return notif_name
    
    def _get_notif_func(self, op_type_id):
        notif_func = self.notifs[op_type_id]['func']
        return notif_func
    
    def _main_loop(self):
        while True:
            head_gns_op_id = GnsStatus.get_global_latest_gns_op_id()
            cur_gns_op_id = GnsStatus.get_module_latest_gns_op_id(self.module)
            if head_gns_op_id - cur_gns_op_id > 0:
                ops = GnsOps.get_ops_in_range(self.type_ids, cur_gns_op_id+1, head_gns_op_id)
                tot = head_gns_op_id - cur_gns_op_id
                if not ops:
                    time.sleep(1)
                    GnsStatus.set_module_state(self.module, head_gns_op_id)
                    continue
                for o in ops:
                    op_type_id = o['op_type_id']
                    notif_code = self._get_notif_code(op_type_id)
                    func = self._get_notif_func(op_type_id)
                    try:
                        done = perform(func, [o['gns_op_id'], o['transaction_id'], o['created'], json.dumps(o['body']), notif_code])
                        if not done:
                            # TODO: log
                            pass
                        GnsStatus.set_module_state(self.module, o['gns_op_id'])
                    except Exception as err:
                        # TODO: log
                        print(err)
                        return
                    progress = int(((tot - (head_gns_op_id - o['gns_op_id'])) / tot) * 100)
                    system_status.set_module_status(self.module, f"synchronizing {progress}  %")
                GnsStatus.set_module_state(self.module, head_gns_op_id)
                if self.module in REQ_VERIFY:
                    REQ_VERIFY[self.module]()
            system_status.set_module_status(self.module, 'synchronized')
            time.sleep(1)

    def start(self):
        if self.good:
            Thread(target=self._main_loop).start()
            system_status.set_module_status(self.module, 'started')
            print(f"'{self.module}' module started.")
