CREATE OR REPLACE FUNCTION gns.update_ops( _first_block BIGINT, _last_block BIGINT )
    RETURNS void
    LANGUAGE plpgsql
    VOLATILE AS $function$
        DECLARE
            temprow RECORD;
            _hive_opid BIGINT;
            _block_num INTEGER;
            _block_timestamp TIMESTAMP;
            _hive_op_type_id SMALLINT;
            _transaction_id VARCHAR(40);
            _body JSON;
            _hash VARCHAR;
            _new_id BIGINT;
        BEGIN
            FOR temprow IN
                SELECT
                    gnsov.id AS hive_opid,
                    gnsov.op_type_id,
                    gnsov.block_num,
                    gnsov.timestamp,
                    gnsov.trx_in_block,
                    gnsov.body
                FROM hive.gns_operations_view gnsov
                WHERE gnsov.block_num >= _first_block
                    AND gnsov.block_num <= _last_block
                ORDER BY gnsov.block_num, trx_in_block, gnsov.id
            LOOP
                _hive_opid := temprow.hive_opid;
                _block_num := temprow.block_num;
                _block_timestamp = temprow.timestamp;
                _hash := (
                    SELECT gnstv.trx_hash FROM hive.gns_transactions_view gnstv
                    WHERE gnstv.block_num = temprow.block_num
                    AND gnstv.trx_in_block = temprow.trx_in_block);
                _transaction_id := encode(_hash::bytea, 'escape');
                _hive_op_type_id := temprow.op_type_id;
                _body := (temprow.body)::json;

                WITH _ins AS (
                    INSERT INTO gns.ops(
                        hive_opid, op_type_id, block_num, created, transaction_id, body)
                    VALUES
                        (_hive_opid, _hive_op_type_id, _block_num, _block_timestamp, _transaction_id, _body)
                    RETURNING gns_op_id
                )
                SELECT gns_op_id INTO _new_id FROM _ins;
            END LOOP;
            UPDATE gns.global_props 
            SET latest_block_num = _block_num,
                latest_hive_rowid = _hive_opid,
                latest_gns_op_id = _new_id,
                latest_block_time = _block_timestamp;
        END;
    $function$;

CREATE OR REPLACE FUNCTION gns.update_module( _module VARCHAR(128), _code VARCHAR(3), _funct VARCHAR, _start_gns_op_id BIGINT, _end_gns_op_id BIGINT )
    RETURNS void
    LANGUAGE plpgsql
    VOLATILE AS $function$
        DECLARE
            temprow RECORD;
            _hooks JSON;
            _code VARCHAR(3);
        BEGIN
            _hooks := (SELECT hooks FROM gns.module_state WHERE module = _module).hooks;
            IF _hooks IS NOT NULL THEN
                FOR temprow IN
                    SELECT
                        gns_op_id, op_type_id, created,
                        transaction_id, body
                    FROM gns.ops
                    WHERE op_type_id = {_op_type_ids}
                    AND gns_op_id >= _start_gns_op_id
                    AND gns_op_id <= _end_gns_op_id
                ORDER BY gns_op_id ASC;
                LOOP
                    _code := _hooks->op_type_id->>'code';
                    SELECT FORMAT('%s ( %s, %s, %s, %s, %s)', _funct, gns_op_id, transaction_id, created, body, _code);
                END LOOP;
                UPDATE gns.module_state
                SET latest_gns_op_id = _end_gns_op_id
                WHERE module = _module;
        END;
    $function$;