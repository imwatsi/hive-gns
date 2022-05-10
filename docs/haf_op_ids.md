# HAF Internal Operation IDs


- `2` | `transfer_operation`

```
{"type":"transfer_operation","value":{"from":"ksmith7","to":"orinoco","amount":{"amount":"110000","precision":3,"nai":"@@000000013"},"memo":"fd4ccb59d550"}}
```

- `18` | `custom_json_operation`

```
{"type":"custom_json_operation","value":{"required_auths":[],"required_posting_auths":["john-jerry"],"id":"notify","json":["setLastRead",{"date":"2022-05-10T11:20:37"}]}}
```