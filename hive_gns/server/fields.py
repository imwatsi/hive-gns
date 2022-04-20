class Fields:
    """Main class to hold fields for SQL queries made by endpoints."""
    class Core:
        """Core module SQL fields."""
        @classmethod
        def get_transfers(cls):
            """Field for the `_get_transfers()` core endpoint function."""
            return ['created', 'remark']