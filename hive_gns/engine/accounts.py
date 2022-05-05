
import json
import time

from datetime import datetime

from hive_gns.database.access import select, write
from hive_gns.engine.hive import make_request
from hive_gns.tools import range_split, UTC_TIMESTAMP_FORMAT

MAX_ACCOUNT_BATCH = 100

class AccountsCache:
    """Holds cache values for account preferences."""
    account_prefs = {}
    accounts_to_check = []
    last_updated = datetime.utcnow()

class AccountsPrefs:
    """Manages account preference fetching at startup."""
    @classmethod
    def _hive_fetch_accounts(cls, accs:list):
        accs_prefs = make_request("condenser_api.get_accounts", accs)
        for acc in accs_prefs:
            if acc['posting_json_metadata'] == '':
                posting_json = {}
            else:
                json.loads(acc['posting_json_metadata'])
            updated = datetime.strftime(datetime.utcnow(), UTC_TIMESTAMP_FORMAT)
            if 'gns' in posting_json:
                AccountsCache.account_prefs[acc['name']] = posting_json['gns']
                data = json.dumps(posting_json['gns'])
                write(f"UPDATE gns.accounts SET prefs = '{data}' AND prefs_updated = '{updated}';")
            else:
                write(f"UPDATE gns.accounts SET prefs_updated = '{updated}';")

    @classmethod
    def fetch_accounts(cls, accs:list):
        if len(accs) > MAX_ACCOUNT_BATCH:
            steps = range_split(0, len(accs)+1, MAX_ACCOUNT_BATCH)
            print(steps)
            for s in steps:
                start, end = s
                cls._hive_fetch_accounts([accs[start:end+1]])
        else:
            cls._hive_fetch_accounts([accs])
        AccountsCache.last_updated = datetime.utcnow()

    @classmethod
    def prefs_sync(cls):
        """Periodically checks for new accounts in the DB that have been updated since last fetch."""
        while True:
            accs_db = select(
                "SELECT account FROM gns.accounts WHERE prefs_updated IS NULL;",
                ['account']
            ) or []
            if len(accs_db) > 0:
                time.sleep(180) # wait for any potential new data to reach irreversibility
                accs = []
                for acc in accs_db:
                    accs.append(acc['account'])
                cls.fetch_accounts(accs)
            time.sleep(30)