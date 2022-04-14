CREATE OR REPLACE FUNCTION gns.core_transfer( _gns_op_id BIGINT, _created TIMESTAMP, _body TEXT, _notif_name VARCHAR(128) )
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
            _remark VARCHAR(500);
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

            _remark := 'you have received % % from %', _amount, _currency, _from;

            -- make notification entry
            INSERT INTO gns.account_notifs (gns_op_id, account, module_name, notif_name, created, remark, payload)
            VALUES (_gns_op_id, _to, 'core', _notif_name, _created, _remark, _body);

        END;
        $function$;