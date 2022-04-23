import json
from unittest import result
import requests

SPLINTERLANDS_API = "https://api2.splinterlands.com"

class Splinterlands:

    @classmethod
    def _request_get(cls, endpoint:str, params:dict):
        try:
            req = requests.get(f"{SPLINTERLANDS_API}{endpoint}", params=params)
            if req.status_code == 200:
                res = json.loads(req.content)
                if 'error' in res and res['error_code'] == 1:
                    return False
                success = res['trx_info']['success']
                if success not in [True, False]:
                    # log and mark for retry
                    print('invalid response from Splinterlands API')
                    return None
                return success
        except:
            # log and mark for retry
            print(f"Splinterlands API:: failed to access endpoint '{endpoint}'")
            return None

    @classmethod
    def verify_transaction(cls, trx_id):
        return cls._request_get('/transactions/lookup', {'trx_id': trx_id})
