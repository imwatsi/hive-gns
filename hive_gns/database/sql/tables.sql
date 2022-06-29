CREATE SCHEMA IF NOT EXISTS gns;

CREATE TABLE IF NOT EXISTS gns.global_props(
    head_block_num BIGINT DEFAULT 0,
    sync_enabled BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS gns.module_state(
    module VARCHAR(64) PRIMARY KEY,
    defs JSON,
    latest_block_num BIGINT DEFAULT 0,
    check_in TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gns.ops(
    gns_op_id BIGSERIAL PRIMARY KEY,
    hive_opid BIGINT UNIQUE NOT NULL,
    op_type_id SMALLINT NOT NULL,
    block_num INTEGER NOT NULL,
    created TIMESTAMP,
    transaction_id BYTEA,
    body JSON
) INHERITS( hive.gns );

CREATE TABLE IF NOT EXISTS gns.accounts(
    account VARCHAR(16) PRIMARY KEY,
    last_reads JSON DEFAULT FORMAT('{"all": "%s"}', timezone('UTC', now()) - '30 days'::interval)::json,
    prefs JSON DEFAULT '{}'::json,
    prefs_updated TIMESTAMP,
    prefs_flag BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS gns.account_notifs(
    id BIGSERIAL PRIMARY KEY,
    gns_op_id BIGINT NOT NULL UNIQUE REFERENCES gns.ops(gns_op_id) ON DELETE CASCADE DEFERRABLE,
    trx_id CHAR(40),
    account VARCHAR(16) NOT NULL REFERENCES gns.accounts(account) ON DELETE CASCADE DEFERRABLE,
    module_name VARCHAR(64) NOT NULL,
    notif_code VARCHAR(3) NOT NULL,
    created TIMESTAMP NOT NULL,
    remark VARCHAR(500) NOT NULL,
    payload JSON NOT NULL,
    verified BOOLEAN DEFAULT NULL
);