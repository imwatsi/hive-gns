class Fields:
    """Main class to hold fields for SQL queries made by endpoints."""
    class Core:
        """Core module SQL fields."""
        @classmethod
        def get_transfers(cls, extra=[]):
            """Field for the `_get_transfers()` core endpoint function."""
            return ['created', 'remark'].extend(extra)
    
    class Splinterlands:
        """Splinterlands module's SQL fields."""
        @classmethod
        def get_transfers(cls, extra=[]):
            """FIeld for the `_get_transfers()` Splinterlands endpoint function."""
            return ['created', 'remark'].extend(extra)