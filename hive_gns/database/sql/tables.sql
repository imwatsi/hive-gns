CREATE SCHEMA IF NOT EXISTS gns;

CREATE TABLE IF NOT EXISTS gns.global_props(
    latest_block_num BIGINT DEFAULT 0,
    latest_hive_rowid BIGINT DEFAULT 0,
    latest_block_time TIMESTAMP,
    sync_enabled BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS gns.ops(
    gns_op_id BIGSERIAL PRIMARY KEY,
    hive_opid BIGINT UNIQUE NOT NULL,
    op_type_id SMALLINT NOT NULL,
    block_num INTEGER NOT NULL,
    created TIMESTAMP,
    transaction_id CHAR(40)
    body TEXT
);

CREATE TABLE IF NOT EXISTS gns.accounts(
    account VARCHAR(16) PRIMARY KEY,
    last_read TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gns.user_prefs(
    gns_op_id BIGINT NOT NULL UNIQUE REFERENCES gns.ops(gns_op_id),
    account VARCHAR(16) NOT NULL REFERENCES gns.accounts(account),
    app VARCHAR(64) NOT NULL,
    subscriptions INTEGER[],
    subscriptions_opts JSON[],
    UNIQUE (account, app)
);
