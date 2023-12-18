NewStore == [_default |-> 0]

StoreGet(store, key) == 
    IF key \in DOMAIN store
    THEN store[key]
    ELSE 0

StoreSet(store, key, value) == 
    IF key \in DOMAIN store
    THEN [store EXCEPT ![key] = value]
    ELSE 
        store @@ [key |-> value]