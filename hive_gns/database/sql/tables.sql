CREATE SCHEMA IF NOT EXISTS gns;

CREATE TABLE IF NOT EXISTS gns.global_props(
    latest_block_num BIGINT DEFAULT 0,
    latest_hive_rowid BIGINT DEFAULT 0,
    latest_gns_op_id BIGINT DEFAULT 0,
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
) INHERITS( hive.gns );

CREATE TABLE IF NOT EXISTS gns.module_state(
    module VARCHAR(64) PRIMARY KEY,
    latest_gns_op_id BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS gns.accounts(
    account VARCHAR(16) PRIMARY KEY,
    last_read TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gns.account_prefs(
    gns_op_id BIGINT NOT NULL UNIQUE REFERENCES gns.ops(gns_op_id) ON DELETE CASCADE,
    account VARCHAR(16) NOT NULL REFERENCES gns.accounts(account) ON DELETE CASCADE,
    app VARCHAR(64) NOT NULL,
    subscriptions VARCHAR(128)[],
    subscriptions_opts JSON[],
    UNIQUE (account, app)
) INHERITS( hive.gns );

CREATE TABLE IF NOT EXISTS gns.account_notifs(
    gns_op_id BIGINT NOT NULL UNIQUE REFERENCES gns.ops(gns_op_id) ON DELETE CASCADE,
    account VARCHAR(16) NOT NULL REFERENCES gns.accounts(account) ON DELETE CASCADE,
    notif_id VARCHAR(128) NOT NULL,
    created TIMESTAMP NOT NULL,
    remark VARCHAR(500) NOT NULL,
    payload JSON
) INHERITS( hive.gns );
