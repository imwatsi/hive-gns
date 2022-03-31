"""Core HAF sync script."""

import os
import time

from hive_gns.database.core import DbSession
from hive_gns.tools import range_split

APPLICATION_CONTEXT = "gns"
BATCH_PROCESS_SIZE = 1000000
SOURCE_DIR = os.path.dirname(__file__) + "/sql"


class HafSync:
    """Main HAF sync processes."""

    @classmethod
    def init(cls, config):
        cls.sync_enabled = False
        cls.db = DbSession(config)
        cls.prepare_context()
        cls.setup_db()

    @classmethod
    def prepare_context(cls):
        exists = cls.db.select(
            f"SELECT hive.app_context_exists( '{APPLICATION_CONTEXT}' );"
        )[0][0]
        print(exists)
        if exists is False:
            cls.db.select(f"SELECT hive.app_create_context( '{APPLICATION_CONTEXT}' );")
            cls.db.commit()
            print(f"Created context: '{APPLICATION_CONTEXT}'")
            exists = cls.db.select(
            f"SELECT hive.app_context_exists( '{APPLICATION_CONTEXT}' );"
            )[0][0]
            print(exists)

    @classmethod
    def setup_db(cls):
        tables = open(f'{SOURCE_DIR}/tables.sql', 'r').read()
        functions = open(f'{SOURCE_DIR}/functions.sql', 'r').read()
        cls.db.execute(tables, None)
        cls.db.execute(functions, None)
        cls.db.commit()

    @classmethod
    def toggle_sync(cls, enabled=True):
        """Turns sync on and off."""
        cls.sync_enabled = enabled

    @classmethod
    def main_loop(cls):
        while True:
            if cls.sync_enabled is True:
                blocks_range = cls.db.select(f"SELECT * FROM hive.app_next_block('{APPLICATION_CONTEXT}');")[0]
                print(blocks_range)
                (first_block, last_block) = blocks_range
                if blocks_range is None or first_block is None:
                    time.sleep(0.2)
                    continue
                if (last_block - first_block) > 100:
                    print("massive sync in progress")
                    steps = range_split(first_block, last_block, BATCH_PROCESS_SIZE)
                    for s in steps:
                        cls.db.select(f"SELECT hive.app_context_detach( '{APPLICATION_CONTEXT}' );")
                        progress = round(((s[0]/last_block) * 100),2)
                        print(f"Massive sync in progress: {s[0]} to {s[1]}    ({progress}) %)")
                        cls.db.select(f"SELECT gns.update_gns_ops( {s[0]}, {s[1]} );")
                        #print("batch sync done")
                        cls.db.select(f"SELECT hive.app_context_attach( '{APPLICATION_CONTEXT}', {s[1]} );")
                        #print("context attached again")
                        cls.db.commit()
                    print("massive sync done")
                    continue
                cls.db.select(f"SELECT gns.update_gns_ops( {first_block}, {last_block} );")
                cls.db.commit()
                print(f"Sync in progress: {first_block} to {last_block} ")
            time.sleep(0.2)
