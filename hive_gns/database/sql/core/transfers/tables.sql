CREATE TABLE IF NOT EXISTS gns.transfers_core (
    id BIGSERIAL PRIMARY KEY,
    gns_op_id BIGINT NOT NULL REFERENCES gns.ops(gns_op_id) ON DELETE CASCADE,
    block_num INTEGER NOT NULL,
    created TIMESTAMP NOT NULL,
    from_acc VARCHAR(16) NOT NULL REFERENCES gns.accounts(name),
    to_acc VARCHAR(16) NOT NULL REFERENCES gns.accounts(name),
    currency VARCHAR(4) NOT NULL,
    amount DECIMAL(10, 3) NOT NULL,
    memo VARCHAR(2048)
);