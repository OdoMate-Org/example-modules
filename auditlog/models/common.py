LOG_TYPE_SELECTION = [
    ("full", "Full log"),
    ("fast", "Fast log"),
]

LOGGABLE_METHODS = ("create", "read", "write", "unlink", "export_data")

FIELDS_BLACKLIST = frozenset({
    "id",
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
    "display_name",
    "__last_update",
})
