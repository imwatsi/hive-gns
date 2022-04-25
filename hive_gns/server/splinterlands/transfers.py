from fastapi import APIRouter, HTTPException

from hive_gns.database.access import select
from hive_gns.server.fields import Fields
from hive_gns.tools import is_valid_hive_account

router_splinterlands_transfers = APIRouter()

def _get_transfers(acc, limit=None, token=None, sender=None, min_amount=None, max_amount=None, min_date=None, max_date=None, op_data=False):
    if op_data:
        fields = Fields.Splinterlands.get_transfers(['payload'])
    else:
        fields = Fields.Splinterlands.get_transfers()
    _fields = ", ".join(fields)
    sql = f"""
        SELECT {_fields}
        FROM gns.account_notifs
        WHERE account = '{acc}'
        AND module_name = 'splinterlands'
        AND notif_name = 'sm_token_transfer'
        AND created > (
            SELECT last_read FROM gns.accounts
            WHERE account = '{acc}'
        )
    """
    if token:
        sql += f"AND payload->'value'->>'json')::json->>'token' = '{token}' "
    if sender:
        sql += f"AND ARRAY(SELECT json_array_elements_text((_body->'value'->'required_auths')))[1] = '{sender}' "
    if min_amount:
        sql += f"AND payload->'value'->>'json')::json->>'qty' >= {min_amount} "
    if max_amount:
        sql += f"AND payload->'value'->>'json')::json->>'qty' <= {max_amount} "
    if min_date:
        sql += f"AND created >= '{min_date}'"
    if max_date:
        sql += f"AND created <= '{max_date}'"
    sql += "ORDER BY created DESC "
    if limit:
        sql += f"LIMIT {limit}"
    res = select(sql, fields)
    return res

@router_splinterlands_transfers.get("/api/{author}/splinterlands/transfers", tags=['splinterlands'])
async def core_transfers(author:str, limit:int=None, currency:str=None, sender:str=None, min_amount:int=None, max_amount:int=None, min_date:str=None, max_date:str=None, op_data=False):
    if limit and not isinstance(limit, int):
        raise HTTPException(status_code=400, detail="limit param must be an integer")
    if currency:
        if not isinstance(currency, str):
            raise HTTPException(status_code=400, detail="currency param must be a string")
        # TODO: validate against register of all token symbols
    if sender:
        if not isinstance(sender, str):
            raise HTTPException(status_code=400, detail="sender param must be a string")
        if not is_valid_hive_account(sender):
            raise HTTPException(status_code=400, detail="sender must be a valid Hive account name; no more than 16 chars in length, may contain only 'a-z', '0-9', '-' and '.'")
    if '@' not in author:
        raise HTTPException(status_code=400, detail="missing '@' in author")
    if not is_valid_hive_account(author.replace('@', '')):
        raise HTTPException(status_code=400, detail="invalid Hive account entered for 'author'")
    if min_date:
        min_date = min_date.replace('T', ' ')
    if max_date:
        max_date = max_date.replace('T', ' ')

    notifs = _get_transfers(author.replace('@', ''), limit, currency, sender, min_amount, max_amount, min_date, max_date, op_data)
    return notifs or []