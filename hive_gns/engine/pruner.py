import time

from hive_gns.database.access import delete

class Pruner:

    @classmethod
    def delete_old_ops(cls):
        sql = f"""
            DELETE FROM gns.ops
            WHERE created <= NOW() - INTERVAL '30 DAYS';
        """
        return delete(sql)

    @classmethod
    def run_pruner(cls):
        while True:
            cls.delete_old_ops()
            time.sleep(300)
