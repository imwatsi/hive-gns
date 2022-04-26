class Fields:
    """Main class to hold fields for SQL queries made by endpoints."""
    class Core:
        """Core module SQL fields."""
        @classmethod
        def get_transfers(cls, extra=None):
            """Field for the `_get_transfers()` core endpoint function."""
            res = ['created', 'remark']
            if extra:
                return res.extend(extra)
            else:
                return res
    
    class Splinterlands:
        """Splinterlands module's SQL fields."""
        @classmethod
        def get_transfers(cls, extra=None):
            """Field for the `_get_transfers()` Splinterlands endpoint function."""
            res = ['created', 'remark']
            if extra:
                return res.extend(extra)
            else:
                return res