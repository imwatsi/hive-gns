import json
import os
import re
from threading import Thread
from hive_gns.database.core import DbSession
from hive_gns.database.module import AvailableModules, Module

from hive_gns.tools import INSTALL_DIR

SOURCE_DIR = os.path.dirname(__file__) + "/sql"

MAIN_CONTEXT = "gns"


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
    def _check_defs(cls, module, defs):
        _block = defs['props']['start_block'] - 1
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
                    INSERT INTO gns.module_state (module, defs, latest_block_num)
                    VALUES ('{module}', '{defs}', {_block});
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
            cls._check_defs(module, defs)
            cls._update_functions(functions)
            AvailableModules.add_module(module, Module(module, defs))

    @classmethod
    def _init_gns(cls):
        cls._check_context(MAIN_CONTEXT)
        tables = open(f'{SOURCE_DIR}/tables.sql', 'r', encoding='UTF-8').read()
        functions = open(f'{SOURCE_DIR}/functions.sql', 'r', encoding='UTF-8').read()
        sync = open(f'{SOURCE_DIR}/sync.sql', 'r', encoding='UTF-8').read()
        cls.db.execute(tables)
        cls.db.execute(functions)
        cls.db.execute(sync)
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
        Thread(target=AvailableModules.module_watch).start()