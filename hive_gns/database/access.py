from hive_gns.database.core import DbSession
from hive_gns.tools import populate_by_schema, normalize_types

_read_db = DbSession()
_write_db = DbSession()

def select(sql:str, schema:list):
    _res = _read_db.select(sql)
    res = []
    if _res:
        assert len(schema) == len(_res[0])
        for x in _res:
            res.append(populate_by_schema(x,schema))
        return normalize_types(res)

def write(sql:str):
    try:
        _write_db.execute(sql, None)
        _write_db.commit()
        return True
    except:
        return False

def perform(func:str, params:list):
    #for p in params:
        #assert isinstance(p, str), 'function params must be strings'
    string_params = ["%s" for p in params]
    parameters = ", ".join(string_params)
    try:
        _write_db.execute(f"SELECT {func}( {parameters} );", params)
        _write_db.commit()
        return True
    except:
        return False

def alter_schema(sql:str):
    _write_db.execute(sql)
    _write_db.commit()