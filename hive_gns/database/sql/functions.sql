CREATE OR REPLACE FUNCTION gns.ops( _first_block BIGINT, _last_block BIGINT )
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
            _body TEXT;
            _new_id BIGINT;
        BEGIN
            FOR temprow IN
                SELECT
                    gnsov.id AS hive_opid,
                    gnsov.block_num,
                    gnsov.timestamp,
                    gnsov.trx_in_block,
                    gnsov.body
                FROM hive.gns_operations_view gnsov
                WHERE gnsov.block_num >= _first_block
                    AND gnsov.block_num <= _last_block
                    AND gnsov.op_type_id = 18
                ORDER BY gnsov.block_num, gnsov.id
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
                _body := temprow.body;

                WITH _ins AS (
                    INSERT INTO gns.ops AS gnsops(
                        hive_opid, op_type_id, block_num, created, transaction_id, body)
                    VALUES
                        (_hive_opid, _block_num, _block_timestamp, _transaction_id, _body);
                    RETURNING gns_op_id
                )
                SELECT gns_op_id INTO _new_id FROM _ins;

                -- transfer_operation
                IF _hive_op_type_id = 2 THEN
                    PERFORM SELECT gns.transfer_operation (
                        _new_id,
                        _block_num,
                        _created,
                        _body::json->'value'->>'from',
                        _body::json->'value'->>'to',
                        _body::json->'value'->>'nai',
                        _body::json->'value'->>'amount',
                        _body::json->'value'->>'memo'
                    );

            END LOOP;
            UPDATE global_props SET (head_hive_opid, head_block_num, head_block_time) = (_hive_opid, _block_num, _block_timestamp);
        END;
        $function$;

