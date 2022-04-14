from hive_gns.database.core import DbSession
from hive_gns.tools import populate_by_schema

read_db = DbSession()
write_db = DbSession()

def select(sql:str, schema:list):
    _res = read_db.execute(sql,None)
    res = []
    if _res:
        assert len(schema) == len(res[0])
        for x in res:
            res.append(populate_by_schema(x,schema))
        return res

def insert(sql:str):
    pass

def delete(sql:str):
    pass

def update(sql:str):
    try:
        write_db.execute(sql, None)
        return True
    except:
        return False

def perform(func:str, params:list):
    for p in params:
        assert isinstance(p, str), 'function params must be strings'
    _params = ", ".join(params)
    try:
        write_db.execute(f"PERFORM gns.{func}( {params} );", None)
        return True
    except:
        return False