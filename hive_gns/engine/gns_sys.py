from hive_gns.database.access import select, write

GNS_OPS_FIELDS = ['gns_op_id', 'op_type_id', 'created', 'transaction_id', 'body']
GNS_GLOBAL_PROPS_FIELDS = [
    'latest_block_num', 'latest_hive_rowid', 'latest_gns_op_id',
    'latest_block_time', 'sync_enabled'
]
GNS_MODULE_STATE_FIELDS = ['module', 'latest_gns_op_id']


class GnsOps:

    @classmethod
    def get_ops_in_range(cls, op_type_ids, lower, upper):
        fields = ", ".join(GNS_OPS_FIELDS)
        _op_type_ids = ", AND op_type_id = ".join(op_type_ids)
        sql = f"""
            SELECT {fields} FROM gns.ops
            WHERE op_type_id = {_op_type_ids}
                AND gns_op_id >= {lower}
                AND gns_op_id <= {upper};
        """
        res = select(sql, GNS_OPS_FIELDS)
        return res

class GnsStatus:
    
    @classmethod
    def get_global_latest_state(cls):
        fields = ", ".join(GNS_GLOBAL_PROPS_FIELDS)
        sql = f"""
            SELECT {fields} FROM gns.global_props;
        """
        res = select(sql, GNS_GLOBAL_PROPS_FIELDS)
        return res[0]


    @classmethod
    def get_global_latest_gns_op_id(cls):
        state = cls.get_global_latest_state()
        return state['latest_gns_op_id']

    @classmethod
    def get_module_latest_state(cls, module):
        fields = ", ".join(GNS_MODULE_STATE_FIELDS)
        sql = f"""
            SELECT {fields} FROM gns.module_state
            WHERE module = '{module}';
        """
        res = select(sql, GNS_MODULE_STATE_FIELDS)
        return res[0]

    @classmethod
    def get_module_latest_gns_op_id(cls, module):
        state = cls.get_module_latest_state(module)
        return state['latest_gns_op_id']
    
    @classmethod
    def set_module_state(cls, module, latest_gns_op_id):
        sql = f"""
            UPDATE gns.module_state
            SET latest_gns_op_id = {latest_gns_op_id}
            WHERE module = '{module}';
        """
        done = write(sql)
        if done == False:
            print(f"Failed to update state for '{module}' module. {latest_gns_op_id}")  #TODO: send to logging module
