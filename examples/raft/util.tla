NewSetInit ==  {}
NewSet(a) == {a}

RECURSIVE NewMap(_, _)
NewMap(n, v) == 
        IF n = 0 
        THEN <<>>
        ELSE NewMap(n-1, v) \o <<v>>

RECURSIVE SubSeqI(_, _, _)
SubSeqI(seq, start, end) == 
        IF start > end \/ start < 1 \/ start > Len(seq)
        THEN <<>>
        ELSE <<seq[start]>> \o SubSeqI(seq, start+1, end)
    

NewStore == [test |-> 0]
NewLogEntry == <<>>

Max(a, b) == IF a > b THEN a ELSE b
Min(a, b) == IF a > b THEN b ELSE a
LogAppend(logs, log) == Append(logs, log)

AddKey(store, key, value) == store @@ [key |-> value]

Time(a) == 100

Add(a, b) == a \union {b} 

RECURSIVE Cardinality(_)
Cardinality(set) ==
        IF set = {}
        THEN 0
        ELSE 1 + Cardinality(set \ {CHOOSE x \in set : TRUE})

Contains(set, elem) == elem \in set