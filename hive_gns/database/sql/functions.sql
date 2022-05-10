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

CREATE OR REPLACE FUNCTION gns.update_module( _module VARCHAR(128), _start_gns_op_id BIGINT, _end_gns_op_id BIGINT )
    RETURNS void
    LANGUAGE plpgsql
    VOLATILE AS $function$
        DECLARE
            temprow RECORD;
            _hooks JSON;
            _code VARCHAR(3);
            _funct VARCHAR;
            _op_ids INT[];
        BEGIN
            SELECT hooks INTO _hooks FROM gns.module_state WHERE module = _module;
            _op_ids := ARRAY(SELECT json_array_elements_text(_hooks->'ids'));
            IF _hooks IS NOT NULL THEN
                FOR temprow IN
                    SELECT
                        gns_op_id, op_type_id, created,
                        transaction_id, body
                    FROM gns.ops
                    WHERE op_type_id = ANY (_op_ids)
                    AND gns_op_id >= _start_gns_op_id
                    AND gns_op_id <= _end_gns_op_id
                ORDER BY gns_op_id ASC
                LOOP
                    _code := _hooks->temprow.op_type_id::varchar->>'code';
                    _funct := _hooks->temprow.op_type_id::varchar->>'func';
                    EXECUTE FORMAT('SELECT %s ($1,$2,$3,$4,$5);', _funct) USING temprow.gns_op_id, temprow.transaction_id, temprow.created, temprow.body, _code;
                END LOOP;
                UPDATE gns.module_state
                SET latest_gns_op_id = _end_gns_op_id
                WHERE module = _module;
            END IF;
        EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE E'Got exception:
                SQLSTATE: % 
                SQLERRM: %', SQLSTATE, SQLERRM;
        END;
    $function$;

CREATE OR REPLACE FUNCTION gns.account_check_notif( _account VARCHAR(16), _module VARCHAR(128), _notif_code VARCHAR(3))
    RETURNS BOOLEAN
    LANGUAGE plpgsql
    VOLATILE AS $function$
        DECLARE
            temprow RECORD;
            _prefs JSON;
            _module_prefs JSON;
            _notifs_enabled VARCHAR(3)[];
            _op_ids INT[];
        BEGIN
            SELECT prefs INTO _prefs FROM gns.accounts WHERE account = _account;

            _module_prefs := _prefs->_module;
            IF _module_prefs IS NULL THEN
                RETURN false;
            ELSIF _module_prefs->>'enabled' = '*' THEN
                RETURN true;
            END IF;

            _notifs_enabled := ARRAY(SELECT json_array_elements_text(_module_prefs->'enabled'));
            IF _notif_code = ANY (_notifs_enabled) THEN
                RETURN true;
            ELSE
                RETURN false;
            END IF;
        EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE E'Got exception:
                SQLSTATE: % 
                SQLERRM: %', SQLSTATE, SQLERRM;
        END;
    $function$;