CREATE SCHEMA IF NOT EXISTS gns;

CREATE TABLE IF NOT EXISTS gns.global_props(
    latest_block_num BIGINT DEFAULT 0,
    latest_hive_rowid BIGINT DEFAULT 0,
    latest_block_time TIMESTAMP,
    sync_enabled BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS gns.ops(
    gns_op_id BIGSERIAL PRIMARY KEY,
    hive_opid BIGINT NOT NULL,
    op_type_id SMALLINT NOT NULL,
    block_num INTEGER NOT NULL,
    created TIMESTAMP,
    transaction_id CHAR(40)
    body TEXT
);
