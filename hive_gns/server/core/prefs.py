from fastapi import APIRouter, HTTPException
from hive_gns.database.access import select
from hive_gns.server.fields import Fields

from hive_gns.server.system_status import get_module_list

router_core_prefs = APIRouter()

def _get_preferences(account, module=None):
    fields = Fields.Core.get_preferences()
    _fields = ", ".join(fields)
    sql = f"""
        SELECT {_fields} FROM gns.accounts
        WHERE account = '{account}';
    """
    res = select(sql, fields, True)
    if module and module in res:
        return res[module]
    return res

@router_core_prefs.get("/api/{account}/preferences")
def account_preferences(account:str, module:str = None):
    if module and module not in get_module_list():
        raise HTTPException(status_code=400, detail="the module is not valid or is unavailable at the moment")
    prefs = _get_preferences(account, module)
    return prefs or {}