import json
import time
from threading import Thread

from hive_gns.database.access import alter_schema, perform, select, write
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
        notifs['ids'] = type_ids
        self.notifs = notifs
        self.type_ids = type_ids
        has = select(f"SELECT module FROM gns.module_state WHERE module='{self.module}'", ['module'], True)
        hooks = json.dumps(self.notifs)
        if has is not None:
            # update
            sql = f"""
                UPDATE gns.module_state SET hooks='{hooks}' WHERE module='{self.module}';
            """
        else:
            # insert
            sql = f"""
                    INSERT INTO gns.module_state (module, hooks)
                    VALUES ('{self.module}', '{hooks}');
                """
        done = write(sql)
        if done is not True:
            raise Exception(f"Failed to save hooks to DB for module: '{self.module}")

    
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
                try:
                    done = perform('gns.update_module', [self.module, cur_gns_op_id+1, head_gns_op_id])
                    if not done:
                        # TODO: log
                        pass
                except Exception as err:
                    # TODO: log
                    print(err)
                    return
                if self.module in REQ_VERIFY:
                    REQ_VERIFY[self.module]()
            system_status.set_module_status(self.module, 'synchronized')
            time.sleep(1)

    def start(self):
        if self.good:
            Thread(target=self._main_loop).start()
            system_status.set_module_status(self.module, 'started')
            print(f"'{self.module}' module started.")
