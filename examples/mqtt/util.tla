NewSet == {}
NewPool == [test |-> <<>>]

AddElement(s, e) == s \union {e}
DelElement(s, e) == s \ {e}

InSeq(s, e) == 
    IF s = <<>>
    THEN FALSE
    ELSE \E i \in DOMAIN s : s[i] = e

AddToSeq(s, e) == 
    IF InSeq(s, e)
    THEN s
    ELSE s \o <<e>>

DelFromSeq(s, e) ==
    IF InSeq(s, e)
    THEN 
        LET i == CHOOSE j \in 1..Len(s): s[j] = e 
        IN SubSeq(s, 1, i) \o SubSeq(s, i+1, Len(s))
    ELSE s

GetSubscribers(pool, e) == pool[e]
AddSubscriber(pool, e, s) == 
    IF e \in DOMAIN pool
    THEN [pool EXCEPT ![e] = AddToSeq(pool[e], s)]
    ELSE
    pool @@ [e |-> <<s>>]

RemoveSubscriber(pool, e, s) == [pool EXCEPT ![e] = DelFromSeq(pool[e], s)]

RECURSIVE Cardinality(_)
Cardinality(set) ==
        IF set = {}
        THEN 0
        ELSE 1 + Cardinality(set \ {CHOOSE x \in set : TRUE})
