import json
from sys import modules
from threading import Thread
import time
from typing import Dict

from hive_gns.database.core import DbSession


class Module:

    def __init__(self, name, defs) -> None:
        self.name = name
        self.defs = defs
        self.db_conn = DbSession()
        self.error = False
    
    def create_new_connection(self):
        if self.error == False:
            del self.db_conn
            self.db_conn = DbSession()

    def get_defs(self):
        return self.defs
    
    def disable(self):
        self.defs['props']['enabled'] = False
        _defs = json.dumps(self.defs)
        self.db_conn.execute(
            f"UPDATE gns.module_state SET defs = '{_defs}' WHERE module = '{self.name}';"
        )
        self.db_conn.commit()
    
    def enable(self):
        self.defs['props']['enabled'] = True
        _defs = json.dumps(self.defs)
        self.db_conn.execute(
            f"UPDATE gns.module_state SET defs = '{_defs}' WHERE module = '{self.name}';"
        )
        self.db_conn.commit()
    
    def is_enabled(self):
        enabled = bool(
            self.db_conn.select_one(
                f"SELECT defs->'props'->'enabled' FROM gns.module_state WHERE module ='{self.name}';"
            )
        )
        return enabled

    def is_connection_open(self):
        return self.db_conn.is_open()
    
    def running(self):
        running = self.db_conn.select_exists(
            f"SELECT * FROM gns.module_state WHERE module = '{self.name}' AND check_in >= NOW() - INTERVAL '1 min'")
        return running
    
    def start(self):
        try:
            print(f"{self.name}:: starting")
            self.db_conn.execute(f"CALL gns.sync_module( '{self.name}' );")
        except Exception as err:
            print(f"Module error: '{self.name}'")
            print(err)
            self.error = True
            self.disable()
            self.db_conn.conn.close()
            self.db_conn.conn.close()

class AvailableModules:

    modules = dict[str, Module]()

    @classmethod
    def add_module(cls, module_name, module:Module):
        cls.modules[module_name] = module

    @classmethod
    def module_watch(cls):
        while True:
            for _module in cls.modules.items():
                module = cls.modules[_module[0]]
                if not modules.error:
                    good = module.is_connection_open()
                    if good is False:
                        print(f"{_module[0]}:: creating new DB connection.")
                        module.create_new_connection()
                    if module.running() is False:
                        Thread(target=module.start).start()
            time.sleep(60)
