CREATE OR REPLACE FUNCTION gns.core_transfer( _gns_op_id BIGINT, _created TIMESTAMP, _body JSON, _notif_name VARCHAR(128) )
    RETURNS void
    LANGUAGE plpgsql
    VOLATILE AS $function$
        DECLARE
            _from VARCHAR(16);
            _to VARCHAR(16);
            _nai VARCHAR(11);
            _amount DOUBLE PRECISION;
            _memo VARCHAR(2048);
            _currency VARCHAR(4);
            _remark VARCHAR(500);
        BEGIN
            -- transfer_operation
            _from := _body->'value'->>'from';
            _to := _body->'value'->>'to';
            _nai := (_body->'value'->>'amount')::json->>'nai';
            _memo := _body->'value'->>'memo';

            IF _nai = '@@000000013' THEN
                _currency := 'HBD';
                _amount := ((_body->'value'->>'amount')::json->>'amount')::float / 1000;
            ELSIF _nai = '@@000000021' THEN
                _currency := 'HIVE';
                _amount := ((_body->'value'->>'amount')::json->>'amount')::float / 1000;
            ELSIF _nai = '@@000000037' THEN
                _currency := 'HP';
                _amount := ((_body->'value'->>'amount')::json->>'amount')::float / 1000000;
            END IF;

            _remark := FORMAT('you have received %s %s from %s', _amount, _currency, _from);

            -- check acount
            INSERT INTO gns.accounts (account)
            SELECT _to
            WHERE NOT EXISTS (SELECT * FROM gns.accounts WHERE account = _to);

            -- make notification entry
            INSERT INTO gns.account_notifs (gns_op_id, account, module_name, notif_name, created, remark, payload)
            VALUES (_gns_op_id, _to, 'core', _notif_name, _created, _remark, _body);

        END;
        $function$;