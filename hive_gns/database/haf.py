import json
import os
import re
from threading import Thread
from hive_gns.database.core import DbSession

from hive_gns.tools import INSTALL_DIR

SOURCE_DIR = os.path.dirname(__file__) + "/sql"

MAIN_CONTEXT = "gns"


class Sync:

    db_conn = DbSession()
    error = False
    
    @classmethod
    def _create_new_connection(cls):
        if cls.error == False:
            del cls.db_conn
            cls.db_conn = DbSession()
    
    @classmethod
    def _disable_sync(cls):
        cls.db_conn.execute(
            "UPDATE gns.global_props SET sync_enabled = false;"
        )
        cls.db_conn.commit()

    @classmethod
    def disable_module(cls, module):
        cls.db_conn.execute(
            f"UPDATE gns.module_state SET enabled = false WHERE module = '{module}';"
        )
        cls.db_conn.commit()
    
    @classmethod
    def enable_module(cls, module):
        cls.db_conn.execute(
            f"UPDATE gns.module_state SET enabled = true WHERE module = '{module}';"
        )
        cls.db_conn.commit()
    
    @classmethod
    def is_enabled(cls, module):
        enabled = bool(
            cls.db_conn.select_one(
                f"SELECT enabled FROM gns.module_state WHERE module ='{module}';"
            )
        )
        return enabled

    @classmethod
    def is_connection_open(cls):
        return cls.db_conn.is_open()
    
    @classmethod
    def is_sync_running(cls):
        running = cls.db_conn.select_exists(
            "SELECT * FROM gns.global_props WHERE check_in >= NOW() - INTERVAL '1 min'")
        return running
    
    @classmethod
    def start(cls):
        try:
            print("Running state_preload script...")
            cls.db_conn.execute("CALL gns.load_state();")
            print("HAF sync starting...")
            cls.db_conn.execute("CALL gns.run_sync();")
        except Exception as err:
            print(f"HAF sync error: {err}")
            cls.error = True
            cls._disable_sync()
            cls.db_conn.conn.close()
            cls.db_conn.conn.close()


class Haf:

    db = DbSession()
    module_list = []

    @classmethod
    def _is_valid_module(cls, module):
        return bool(re.match(r'^[a-z]+[_]*$', module))

    @classmethod
    def _check_context(cls, name, start_block=None):
        exists = cls.db.select_one(
            f"SELECT hive.app_context_exists( '{name}' );"
        )
        if exists is False:
            cls.db.select(f"SELECT hive.app_create_context( '{name}' );")
            if start_block is not None:
                cls.db.select(f"SELECT hive.app_context_detach( '{name}' );")
                cls.db.select(f"SELECT hive.app_context_attach( '{name}', {(start_block-1)} );")
            cls.db.commit()
            print(f"HAF SYNC:: created context: '{name}'")
    
    @classmethod
    def _check_schema(cls, module, tables):
        exists = cls.db.select(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name='{module}';")
        if exists is None:
            cls.db.execute(tables, None)
            cls.db.commit()
    
    @classmethod
    def _update_functions(cls, functions):
        cls.db.execute(functions, None)
        cls.db.commit()
    
    @classmethod
    def _check_hooks(cls, module, defs):
        has = cls.db.select_exists(f"SELECT module FROM gns.module_state WHERE module='{module}'")
        # generate used op type ids array
        _op_ids = []
        for op in defs['ops'].keys():
            _op_ids.append(op)
        defs['op_ids'] = _op_ids
        defs = json.dumps(defs)
        if has is False:
            cls.db.execute(
                f"""
                    INSERT INTO gns.module_state (module, hooks)
                    VALUES ('{module}', '{defs}');
                """)
        else:
            cls.db.execute(
                f"""
                    UPDATE gns.module_state SET defs='{defs}' WHERE module='{module}';
                """
            )

    @classmethod
    def _init_modules(cls):
        working_dir = f'{INSTALL_DIR}/modules'
        cls.module_list = [f.name for f in os.scandir(working_dir) if cls._is_valid_module(f.name)]
        for module in cls.module_list:
            defs = json.loads(open(f'{working_dir}/{module}/defs.json', 'r', encoding='UTF-8').read())
            functions = open(f'{working_dir}/{module}/functions.sql', 'r', encoding='UTF-8').read()
            tables = open(f'{working_dir}/{module}/tables.sql', 'r', encoding='UTF-8').read()
            cls._check_context(module, defs['props']['start_block'])
            cls._check_schema(module, tables)
            cls._check_hooks(module, defs)
            cls._update_functions(functions)

    @classmethod
    def _init_gns(cls):
        cls._check_context(MAIN_CONTEXT)
        for _file in ['tables.sql', 'functions.sql', 'sync.sql', 'state_preload.sql', 'filters.sql']:
            _sql = open(f'{SOURCE_DIR}/{_file}', 'r', encoding='UTF-8').read()
            cls.db.execute(_sql)
        cls.db.execute(
            """
                INSERT INTO gns.global_props (head_block_num)
                SELECT '0'
                WHERE NOT EXISTS (SELECT * FROM gns.global_props);
            """, None
        )
        cls.db.commit()

    @classmethod
    def init(cls):
        cls._init_gns()
        cls._init_modules()
        Thread(target=Sync.start).start()
