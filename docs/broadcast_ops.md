# GNS Broadcast Ops

GNS uses `custom_json` ops to record user related activity, like marking notifications as "read" and setting preferences.

To broadcast these operations, use `gns` as the `custom_json` ID.

- the main `json` payload is stored in an array
- the first element is the `op_name`
- the second is the actual payload

For example:

`id`: `gns`

`json`: 

```
[
    "read",
    ["core.trn"]
]
```

## Account preferences

- the op_name is `prefs`: to update preferences
- `module` is the key
- `enabled` lists the codes of notifs enabled, asterisk (*) for `all`
- subsequent keys are for specific notifs (`trn` | `vot`), under the relevant module

```
[
    "update",
    {
        "core": {
            "enabled": ["trn"],
            "trn": {
                "min_hbd": 1
            },
            "vot": {
                "min_weight": 12345,
                "freq": 12,                         # hours
                "summary": true
            }

        },
        "splinterlands": {
            "enabled": ["*"],
            "trn": {
                "min_dec": 1
            }
        }
    }
]
```

## Mark as read

- the op_name is `read`: to mark as read

```
[
    "read",
    ["core.trn"]
]
```