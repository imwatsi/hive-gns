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
                ORDER BY gnsov.block_num, trx_in_block, gnsov.id
            LOOP
                _hive_opid := temprow.hive_opid;
                _block_num := temprow.block_num;
                _block_timestamp = temprow.timestamp;
                _hash := temprow.trx_hash;
                _hive_op_type_id := temprow.op_type_id;
                _body := (temprow.body)::json;

                WITH _ins AS (
                    INSERT INTO gns.ops(
                        hive_opid, op_type_id, block_num, created, transaction_id, body)
                    VALUES
                        (_hive_opid, _hive_op_type_id, _block_num, _block_timestamp, _hash, _body)
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
            _value JSON;
            _filter JSON;
            _op_type_id SMALLINT;
            _func VARCHAR;
            _internal_func VARCHAR;
        BEGIN

            SELECT hooks INTO _hooks FROM gns.module_state WHERE module = _module;

            FOR _code, _value IN SELECT (json_each(_hooks))
            LOOP
                _filter := _value->'filter';
                _op_type_id := _value->'op_type_id';
                _func := _value->'func';
                -- select function by op type
                _internal_func := gns.get_internal_func(_op_type_id);
                -- init update
                EXECUTE FORMAT('SELECT %s ($1,$2,$3,$4,$5);', _internal_func)
                USING _start_gns_op_id, _end_gns_op_id, _code, _func, _filter;
            END LOOP;

            UPDATE gns.module_state
                SET latest_gns_op_id = _end_gns_op_id
                WHERE module = _module;

        EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE E'Got exception:
                SQLSTATE: % 
                SQLERRM: %', SQLSTATE, SQLERRM;
        END;
    $function$;


CREATE OR REPLACE FUNCTION gns.get_internal_func( _op_type_id SMALLINT)
    RETURNS VARCHAR
    LANGUAGE plpgsql
    VOLATILE AS $function$
        BEGIN
            IF _op_type_id = 18 THEN
                RETURN 'process_custom_json_operation';
            ELSIF _op_type_id = 2 THEN
                RETURN 'process_transfer_operation';
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

CREATE OR REPLACE FUNCTION gns.run_pruner()
    RETURNS void
    LANGUAGE plpgsql
    VOLATILE AS $function$
        BEGIN
            IF _op_type_id = 18 THEN
                RETURN 'process_custom_json_operation';
            ELSIF _op_type_id = 2 THEN
                RETURN 'process_transfer_operation';
            END IF;
        EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE E'Got exception:
                SQLSTATE: % 
                SQLERRM: %', SQLSTATE, SQLERRM;
        END;
    $function$;