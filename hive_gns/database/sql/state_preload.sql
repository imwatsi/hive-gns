CREATE OR REPLACE FUNCTION gns.load_state( _first_block BIGINT, _last_block BIGINT )
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
            _hash BYTEA;
            _new_id BIGINT;
        BEGIN
            FOR temprow IN
                SELECT
                    gnsov.id AS hive_opid,
                    gnsov.op_type_id,
                    gnsov.block_num,
                    gnsov.timestamp,
                    gnsov.trx_in_block,
                    gnsov.body,
                    gnstv.trx_hash
                FROM hive.gns_operations_view gnsov
                LEFT JOIN hive.gns_transactions_view gnstv
                    ON gnstv.block_num = gnsov.block_num
                    AND gnstv.trx_in_block = gnsov.trx_in_block
                WHERE gnsov.block_num >= _first_block
                    AND gnsov.block_num <= _last_block
                    AND gnsov.op_type_id = 18
                    AND gnsov.body::json->'value'->>'id' = 'gns'
                ORDER BY gnsov.block_num, trx_in_block, gnsov.id
            LOOP
                _hive_opid := temprow.hive_opid;
                _block_num := temprow.block_num;
                _block_timestamp = temprow.timestamp;
                _hash := temprow.trx_hash;
                _hive_op_type_id := temprow.op_type_id;
                _body := (temprow.body)::json;

                PERFORM gns.core_gns(0, encode('\x0000000000000000000000000000000000000000','hex'), _block_timestamp, _body, 'gns');

            END LOOP;
            UPDATE gns.global_props SET state_preloaded = true;
        END;
    $function$;