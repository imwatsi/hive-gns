-- check context

CREATE OR REPLACE PROCEDURE gns.sync_module(_module_name VARCHAR(64))
    LANGUAGE plpgsql
    AS $$
        DECLARE
            temprow RECORD;
            _app_context VARCHAR;
            _ops JSON;
            _op_ids SMALLINT[];
            _next_block_range hive.blocks_range;
            _latest_block_num INTEGER;
            _range BIGINT[];
        BEGIN
            SELECT defs->'props'->>'context' INTO _app_context FROM gns.module_state WHERE module = _module_name;
            SELECT defs->'ops' INTO _ops FROM gns.module_state WHERE module = _module_name;
            SELECT ARRAY (SELECT json_array_elements_text(defs->'op_ids')) INTO _op_ids FROM gns.module_state WHERE module = _module_name;

            IF _app_context IS NULL THEN
                RAISE NOTICE 'Could not start sync for module: %. DB entry not found.', _module_name;
                RETURN;
            END IF;

            SELECT latest_block_num INTO _latest_block_num FROM gns.module_state WHERE module = _module_name;
            IF NOT hive.app_context_is_attached(_app_context) THEN
                PERFORM hive.app_context_attach(_app_context, _latest_block_num);
            END IF;

            WHILE gns.module_enabled(_module_name) LOOP
                _next_block_range := hive.app_next_block(_app_context);
                IF _next_block_range IS NULL THEN
                    RAISE WARNING 'Waiting for next block...';
                ELSE
                    RAISE NOTICE 'Attempting to process block range: <%,%>', _next_block_range.first_block, _next_block_range.last_block;
                    CALL gns.process_block_range(_module_name, _app_context, _next_block_range.first_block, _next_block_range.last_block, _ops, _op_ids);
                END IF;
            END LOOP;
            COMMIT;
        END;
    $$;

CREATE OR REPLACE PROCEDURE gns.process_block_range(_module_name VARCHAR, _app_context VARCHAR, _start INTEGER, _end INTEGER, _ops JSON, _op_ids SMALLINT[] )
    LANGUAGE plpgsql
    AS $$

        DECLARE
            temprow RECORD;
            _module_schema VARCHAR;
            _done BOOLEAN;
            _massive BOOLEAN;
            _first_block INTEGER;
            _last_block INTEGER;
            _step INTEGER;
        BEGIN
            _step := 1000;
            -- determine if massive sync is needed
            IF _end - _start > 0 THEN
                -- detach context
                PERFORM hive.app_context_detach(_app_context);
                _massive := true;
            END IF;
            -- divide range
            FOR _first_block IN _start .. _end BY _step LOOP
                _last_block := _first_block + _step - 1;

                IF _last_block > _end THEN --- in case the _step is larger than range length
                    _last_block := _end;
                END IF;

                RAISE NOTICE 'Attempting to process a block range: <%, %>', _first_block, _last_block;
                -- record run start
                    -- select records and pass records to relevant functions
                FOR temprow IN
                    EXECUTE FORMAT('
                        SELECT
                            %1$sov.id,
                            %1$sov.op_type_id,
                            %1$sov.block_num,
                            %1$sov.timestamp,
                            %1$sov.trx_in_block,
                            %1$stv.trx_hash,
                            %1$sov.body::json
                        FROM hive.%1$s_operations_view %1$sov
                        LEFT JOIN hive.%1$s_transactions_view %1$stv
                            ON %1$stv.block_num = %1$sov.block_num
                            AND %1$stv.trx_in_block = %1$sov.trx_in_block
                        WHERE %1$sov.block_num >= $1
                            AND %1$sov.block_num <= $2
                            AND %1$sov.op_type_id = ANY ($3)
                        ORDER BY %1$sov.block_num, trx_in_block, %1$sov.id;', _app_context)
                    USING _first_block, _last_block, _op_ids
                LOOP
                    EXECUTE FORMAT('SELECT %s ($1,$2,$3,$4);', (_ops->>(temprow.op_type_id::varchar)))
                        USING temprow.block_num, temprow.timestamp, temprow.trx_hash, temprow.body;
                END LOOP;
                -- save done as run end
                RAISE NOTICE 'Block range: <%, %> processed successfully.', _first_block, _last_block;
                UPDATE gns.module_state SET check_in = NOW() WHERE module = _module_name;
                UPDATE gns.module_state SET latest_block_num = _last_block WHERE module = _module_name;
                COMMIT;
            END LOOP;
            IF _massive = true THEN
                -- attach context
                PERFORM hive.app_context_attach(_app_context, _last_block);
            END IF;
        END;
    $$;