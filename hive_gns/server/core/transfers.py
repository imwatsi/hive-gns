from fastapi import APIRouter, HTTPException

from hive_gns.database.access import select
from hive_gns.server.fields import Fields
from hive_gns.tools import NAI_MAP, is_valid_hive_account

MODULE_NAME = 'core'
NOTIF_NAME = 'core_transfer'

router_core_transfers = APIRouter()

def _get_transfers(acc, limit=None, currency=None, sender=None, min_amount=None, max_amount=None, min_date=None, max_date=None, op_data=False):
    if op_data:
        fields = Fields.Core.get_transfers(['payload'])
    else:
        fields = Fields.Core.get_transfers()
    _fields = ", ".join(fields)
    sql = f"""
        SELECT {_fields}
        FROM gns.account_notifs
        WHERE account = '{acc}'
        AND module_name = '{MODULE_NAME}'
        AND notif_name = '{NOTIF_NAME}'
        AND created > (
            SELECT COALESCE(last_reads->'{MODULE_NAME}'->>'{NOTIF_NAME}'::timestamp, NOW() - INTERVAL '30 DAYS')
            FROM gns.accounts WHERE account = '{acc}'
        )
    """
    if currency:
        nai = NAI_MAP[currency]
        sql += f"AND payload->'value'->'amount'->>'nai' = '{nai}' "
    if sender:
        sql += f"AND payload->'value'->>'from' = '{sender}' "
    if min_amount:
        sql += f"AND (payload->'value'->'amount'->>'amount')::bigint >= {min_amount} "
    if max_amount:
        sql += f"AND (payload->'value'->'amount'->>'amount')::bigint <= {max_amount} "
    if min_date:
        sql += f"AND created >= '{min_date}'"
    if max_date:
        sql += f"AND created <= '{max_date}'"
    sql += "ORDER BY created DESC "
    if limit:
        sql += f"LIMIT {limit}"
    res = select(sql, fields)
    return res

@router_core_transfers.get("/api/{account}/core/transfers", tags=['core'])
async def core_transfers(account:str, limit:int=None, currency:str=None, sender:str=None, min_amount:int=None, max_amount:int=None, min_date:str=None, max_date:str=None, op_data:bool=False):
    if limit and not isinstance(limit, int):
        raise HTTPException(status_code=400, detail="limit param must be an integer")
    if currency:
        if not isinstance(currency, str):
            raise HTTPException(status_code=400, detail="currency param must be a string")
        if currency not in NAI_MAP:
            raise HTTPException(status_code=400, detail=f"currency param invalid; valid options are {NAI_MAP.keys()}")
    if sender:
        if not isinstance(sender, str):
            raise HTTPException(status_code=400, detail="sender param must be a string")
        if not is_valid_hive_account(sender):
            raise HTTPException(status_code=400, detail="sender must be a valid Hive account name; no more than 16 chars in length, may contain only 'a-z', '0-9', '-' and '.'")
    if '@' not in account:
        raise HTTPException(status_code=400, detail="missing '@' in account")
    if not is_valid_hive_account(account.replace('@', '')):
        raise HTTPException(status_code=400, detail="invalid Hive account entered")
    if min_date:
        min_date = min_date.replace('T', ' ')
    if max_date:
        max_date = max_date.replace('T', ' ')

    notifs = _get_transfers(account.replace('@', ''), limit, currency, sender, min_amount, max_amount, min_date, max_date, op_data)
    return notifs or []
