"""Core HAF sync script."""

import os
import time
from hive_gns.config import Config

from hive_gns.database.core import DbSession
from hive_gns.engine.hive import make_request
from hive_gns.server import system_status
from hive_gns.tools import range_split

APPLICATION_CONTEXT = "gns"
BATCH_PROCESS_SIZE = 200000
SOURCE_DIR = os.path.dirname(__file__) + "/sql"


class HafSync:
    """Main HAF sync processes."""

    @classmethod
    def init(cls):
        cls.sync_enabled = False
        cls.db = DbSession()
        cls.prepare_app_data()
        cls.setup_db()

    @classmethod
    def prepare_app_data(cls):
        exists = cls.db.select(
            f"SELECT hive.app_context_exists( '{APPLICATION_CONTEXT}' );"
        )[0][0]

        if exists is False:
            cls.db.select(f"SELECT hive.app_create_context( '{APPLICATION_CONTEXT}' );")
            cls.db.commit()
            print(f"HAF SYNC:: created context: '{APPLICATION_CONTEXT}'")
            exists = cls.db.select(
            f"SELECT hive.app_context_exists( '{APPLICATION_CONTEXT}' );"
            )[0][0]
        

    @classmethod
    def setup_db(cls):
        tables = open(f'{SOURCE_DIR}/tables.sql', 'r').read()
        functions = open(f'{SOURCE_DIR}/functions.sql', 'r').read()
        cls.db.execute(tables, None)
        cls.db.execute(functions, None)
        cls.db.execute(
            """
                INSERT INTO gns.global_props (latest_block_num)
                SELECT '0'
                WHERE NOT EXISTS (SELECT * FROM gns.global_props);
            """, None
        )
        cls.db.commit()

    @classmethod
    def toggle_sync(cls, enabled=True):
        """Turns sync on and off."""
        cls.sync_enabled = enabled
    
    @classmethod
    def get_oldest_block_num(cls):
        glob_props = make_request("condenser_api.get_dynamic_global_properties")
        return glob_props['head_block_number'] - (86400 * 30) # 30 days

    @classmethod
    def main_loop(cls):
        start_block = cls.get_oldest_block_num()
        massive_sync = False
        while True:
            if cls.sync_enabled is True:
                blocks_range = cls.db.select(f"SELECT * FROM hive.app_next_block('{APPLICATION_CONTEXT}');")[0]
                (first_block, last_block) = blocks_range
                if blocks_range is None or first_block is None:
                    system_status.set_sync_status("synchronized")
                    time.sleep(0.2)
                    continue

                if blocks_range[0] < start_block:
                    print(f"HAF SYNC:: starting from global_start_block: {start_block}")
                    cls.db.select(f"SELECT hive.app_context_detach( '{APPLICATION_CONTEXT}' );")
                    print("HAF SYNC:: context detached")
                    cls.db.select(f"SELECT hive.app_context_attach( '{APPLICATION_CONTEXT}', {(start_block-1)} );")
                    print("HAF SYNC:: context attached again")
                    blocks_range = cls.db.select(f"SELECT * FROM hive.app_next_block('{APPLICATION_CONTEXT}');")[0]
                    print(f"HAF SYNC:: blocks range: {blocks_range}")
                    (first_block, last_block) = blocks_range
                    massive_sync = True
                    # step back 30 blocks
                    #last_block -= 30

                if massive_sync:
                    print("HAF SYNC:: starting massive sync")
                    steps = range_split(first_block, last_block, BATCH_PROCESS_SIZE)
                    tot = last_block - first_block
                    cls.db.select(f"SELECT hive.app_context_detach( '{APPLICATION_CONTEXT}' );")
                    for s in steps:
                        cls.db.select(f"SELECT gns.update_ops( {s[0]}, {s[1]} );")
                        cls.db.commit()
                        progress = int(((tot - (last_block - s[0])) / tot) * 100)
                        print(f"HAF SYNC:: massive sync in progress: {s[0]} to {s[1]}    {progress} %")
                        system_status.set_sync_status(f"massive sync in progress  {progress} %")
                    cls.db.select(f"SELECT hive.app_context_attach( '{APPLICATION_CONTEXT}', {s[1]} );")
                    print("HAF SYNC:: massive sync done")
                    massive_sync = False
                    continue

                cls.db.select(f"SELECT gns.update_ops( {first_block}, {last_block} );")
                cls.db.commit()
                system_status.set_sync_status(f"synchronizing... on block {last_block}")
            time.sleep(0.2)
