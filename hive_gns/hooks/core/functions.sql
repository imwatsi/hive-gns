CREATE OR REPLACE FUNCTION gns.core_transfer( gns_op_id BIGINT, _created TIMESTAMP, _body TEXT )
    RETURNS void
    LANGUAGE plpgsql
    VOLATILE AS $function$
        DECLARE
            _from VARCHAR(16);
            _to VARCHAR(16);
            _nai VARCHAR(11);
            _amount BIGINT;
            _memo VARCHAR(2048);
            _currency VARCHAR(4);
        BEGIN
            -- transfer_operation
            _from := _body::json->'value'->>'from';
            _to := _body::json->'value'->>'to';
            _nai := _body::json->'value'->>'nai';
            _amount := _body::json->'value'->>'amount';
            _memo := _body::json->'value'->>'memo';
            _currency := 

            IF _nai = '@@000000013' THEN
                _currency := 'HBD';
            ELSIF _nai = '@@000000021' THEN
                _currency := 'HIVE';
            ELSIF _nai = '@@000000037' THEN
                _currency := 'HP';
            END IF;

            -- make notification entry

        END;
        $function$;