CREATE OR REPLACE FUNCTION gns.transfer_operation (_gns_op_id BIGINT, _block_num BIGINT, _created TIMESTAMP, _from VARCHAR(16), _to VARCHAR(16), _nai VARCHAR(11), _amount BIGINT, _memo VARCHAR(2048))
    RETURNS void
    LANGUAGE plpgsql
    VOLATILE AS $function$
        DECLARE
            _currency VARCHAR(4);
        BEGIN
            -- HBD
            IF _nai = '@@000000013' THEN
                _currency := 'HBD';
            ELSIF _nai = '@@000000021' THEN
                _currency := 'HIVE';
            ELSIF _nai = '@@000000037' THEN
                _currency := 'HP';
            END IF;
            
            INSERT INTO gns.transfers_core(gns_op_id, block_num, created, from_acc, to_acc, currency, amount)
            VALUES (_gns_op_id, _block_num, _created, _from, _to, _currency, _amount, _memo);
        END;
    $function$;