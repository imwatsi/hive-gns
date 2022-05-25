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
                    AND ppov.op_type_id = 18
                    AND ppov.body::json->'value'->>'id' = 'gns'
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

                PERFORM gns.core_gns(0, '0000000000000000000000000000000000000000', _block_timestamp, _body, 'gns');

            END LOOP;
        END;
    $function$;