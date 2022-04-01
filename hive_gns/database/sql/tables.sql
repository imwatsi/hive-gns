CREATE SCHEMA IF NOT EXISTS gns;

REATE TABLE IF NOT EXISTS gns.global_props(
    latest_block_num BIGINT DEFAULT 0,
    latest_hive_rowid BIGINT DEFAULT 0,
    latest_block_time TIMESTAMP,
    sync_enabled BOOLEAN DEFAULT true
);


