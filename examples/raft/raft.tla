------------------------------- MODULE raft -------------------------------
EXTENDS Integers, TLC, Sequences
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

Follower == 0
Candidate == 1
Leader == 2
MaxServer == 2
QurmMaxServer == 2
InitValue == 0

(*--algorithm raft
variables
    net = [ins \in {1, 2, 4} |-> [chan \in {"ClientRequest", "ClientRequestResponse", "RequestVote", "RequestVoteResponse", "AppendEntries", "AppendEntriesResponse"} |-> <<>>]];
    reqCh = <<[Type |-> "Put", Key |-> "x", Value |-> "1", Idx |-> 1]>>;
    respCh = <<>>;
    clientNum = 1;
    log = <<>>;
    clientReqNum = 0;
    serverVoteNum = 0;
    __call_stack = [p \in {"2HandleAppendEntriesResponse", "2RequestVote", "1HandleRequestVoteRequest", "2HandleRequestVoteRequest", "4Main", "2HandleAppendEntriesRequest", "1HandleAppendEntriesResponse", "1RequestVote", "1HandleRequestVoteResponse", "1HandleClientRequest", "2HandleClientRequest", "2HandleRequestVoteResponse", "1HandleAppendEntriesRequest"} |-> <<>>];
    __path = 0;
    AClientIns = [r \in {4} |-> [mleader |-> 1,reqId |-> r,me |-> r]];
    AServerIns = [r \in {1, 2} |-> [currentTerm |-> 0,state |-> 0,votedFor |-> 0,commitIndex |-> 0,me |-> r,mleader |-> InitValue,votesResponded |-> NewSetInit,votesGranted |-> NewSetInit,logs |-> NewLogEntry,nextIndex |-> NewMap(MaxServer, 1),matchIndex |-> NewMap(MaxServer, 0),kvStore |-> NewStore]];

macro net_read (msg, id, channel) begin
    await Len(net[(id)][(channel)]) > 0;
    msg := Head(net[(id)][(channel)]);
    net[(id)][(channel)] := Tail(net[(id)][(channel)]);
end macro;
macro net_write (msg, id, channel) begin
    net[(id)][(channel)] := Append(net[(id)][(channel)], msg);
end macro;
macro reqCh_read (msg) begin
    await Len(reqCh) > 0;
    msg := Head(reqCh);
    reqCh := Tail(reqCh);
end macro;
macro respCh_write (msg) begin
    respCh := Append(respCh, msg);
end macro;
macro clientNum_read (msg) begin
    msg := clientNum;
end macro;
macro log_read (msg) begin
    msg := log;
end macro;
macro clientReqNum_write (msg) begin
    clientReqNum := clientReqNum + 1;
end macro;
macro serverVoteNum_write (msg) begin
    serverVoteNum := serverVoteNum + 1;
end macro;

procedure __AServer_SendRequestVote(name, pID)
begin
    L125:
    req := Head(__call_stack[name]) ||
    dest := Head(Tail(__call_stack[name])) ||
    __call_stack[name] := Tail(Tail(__call_stack[name]));
    net_write(req, dest, "RequestVote");
    Label_97_5: return;
end procedure;

procedure __AServer_HandleAppendEntriesRequestFunc(name, pID)
variables
resp;success;logOk;needReply;req;mIndex;index;tmpi;
__Profile = "__AServer";
begin
    L135:
    req := Head(__call_stack[name]) ||
    __call_stack[name] := Tail(__call_stack[name]);
    resp := [__reserved |-> 0];
    success := FALSE;
    logOk := FALSE;
    needReply := FALSE;
    AtomCheckTerm:
    if req.Mterm > AServerIns[pID].currentTerm then
        AServerIns[pID].currentTerm := req.Mterm ||
        AServerIns[pID].votedFor := 0 ||
        AServerIns[pID].state := Follower ||
        AServerIns[pID].mleader := InitValue ||
        AServerIns[pID].mleader := req.Msource;
    end if;
    mIndex := InitValue;
    index := 0;
    if (req.MprevLogIndex < 1 \/ (req.MprevLogIndex <= Len(AServerIns[pID].logs) /\ req.MprevLogIndex >= 1 /\ AServerIns[pID].logs[(req.MprevLogIndex)].Mterm = req.MprevLogTerm)) then
        logOk := TRUE;
        print(<<AServerIns[pID].me, "log ok", Len(AServerIns[pID].logs), req.MprevLogIndex, req.MprevLogTerm, req.Mterm, AServerIns[pID].state, AServerIns[pID].currentTerm>>);
    else
        logOk := FALSE;
    end if;
    if req.Mterm <= AServerIns[pID].currentTerm then
        if (req.Mterm < AServerIns[pID].currentTerm \/ (req.Mterm = AServerIns[pID].currentTerm /\ ~logOk /\ AServerIns[pID].state = Follower)) then
            needReply := TRUE;
        elsif (req.Mterm = AServerIns[pID].currentTerm /\ AServerIns[pID].state = Candidate) then
            Label_132_13: AServerIns[pID].state := Follower ||
            AServerIns[pID].votedFor := 0 ||
            AServerIns[pID].mleader := InitValue ||
            success := TRUE;
        elsif (req.Mterm = AServerIns[pID].currentTerm /\ AServerIns[pID].state = Follower /\ logOk) then
            Label_137_13: index := req.MprevLogIndex + 1;
            print(<<AServerIns[pID].me, "wait update logs", index, Len(AServerIns[pID].logs), (Len(req.Mlog) = 0 \/ (Len(req.Mlog) > 0 /\ index >= 1 /\ index <= Len(AServerIns[pID].logs) /\ req.Mlog[(1)].Mterm = AServerIns[pID].logs[(index)].Mterm) \/ (Len(req.Mlog) > 0 /\ index = Len(AServerIns[pID].logs)))>>);
            if (Len(req.Mlog) = 0 \/ (Len(req.Mlog) > 0 /\ index >= 1 /\ index <= Len(AServerIns[pID].logs) /\ req.Mlog[(1)].Mterm = AServerIns[pID].logs[(index)].Mterm) \/ (Len(req.Mlog) > 0 /\ index = Len(AServerIns[pID].logs) + 1)) then
                AServerIns[pID].logs := LogAppend(SubSeqI(AServerIns[pID].logs, 1, req.MprevLogIndex + 1), req.Mlog) ||
                AServerIns[pID].commitIndex := req.MleaderCommit;
                success := TRUE;
                mIndex := req.MprevLogIndex + Len(req.Mlog);
                print(<<AServerIns[pID].me, "update logs", mIndex, Len(AServerIns[pID].logs)>>);
                needReply := TRUE;
                tmpi := 1;
                Label_147_17: while tmpi <= Len(req.Mlog) do
                    if req.Mlog[(tmpi)].Mcommand.Type = "Put" then
                        AServerIns[pID].kvStore := AddKey(AServerIns[pID].kvStore, req.Mlog[(tmpi)].Mcommand.Key, req.Mlog[(tmpi)].Mcommand.Value);
                    else
                        AServerIns[pID].kvStore := AddKey(AServerIns[pID].kvStore, req.Mlog[(tmpi)].Mcommand.Key, "");
                    end if;
                    tmpi := tmpi + 1;
                end while;
            elsif (Len(req.Mlog) > 0 /\ Len(AServerIns[pID].logs) >= index /\ index >= 1 /\ req.Mlog[(1)].Mterm /= AServerIns[pID].logs[(index)].Mterm) then
                AServerIns[pID].logs := SubSeqI(AServerIns[pID].logs, 1, Len(AServerIns[pID].logs));
            end if;
        end if;
        EndAtomCheckState:
        if needReply then
            needReply := FALSE;
            resp := [Mterm |-> AServerIns[pID].currentTerm, Msource |-> AServerIns[pID].me, Msuccess |-> success, Mdest |-> req.Msource, MmatchIndex |-> mIndex];
            net_write(resp, req.Msource, "AppendEntriesResponse");
        end if;
    end if;
    Label_166_5: __call_stack[name] := <<>> \o __call_stack[name];
    
    L214:
    return;
    Label_170_5: return;
end procedure;

procedure __AServer_ApplyAndResponseClient(name, pID)
variables
success;dest;id;idx;resp;value;
__Profile = "__AServer";
begin
    L241:
    id := Head(__call_stack[name]) ||
    __call_stack[name] := Tail(__call_stack[name]);
    success := TRUE;
    dest := AServerIns[pID].logs[(id)].Client;
    idx := AServerIns[pID].logs[(id)].Mcommand.Idx;
    resp := [__reserved |-> 0];
    value := "";
    if AServerIns[pID].logs[(id)].Mcommand.Type = "Get" then
        Label_187_9: value := AServerIns[pID].kvStore[(AServerIns[pID].logs[(id)].Mcommand.Key)];
    else
        AServerIns[pID].kvStore[(AServerIns[pID].logs[(id)].Mcommand.Key)] := AServerIns[pID].logs[(id)].Mcommand.Value;
    end if;
    Label_191_5: resp := [Msuccess |-> success, Msource |-> AServerIns[pID].me, Mdest |-> dest, Idx |-> idx, LeaderHint |-> AServerIns[pID].me, Value |-> value];
    net_write(resp, dest, "ClientRequestResponse");
    Label_193_5: return;
end procedure;

procedure __AServer_AdvanceCommitIndex(name, pID)
variables
hasCommit;i;tmpCommitIndex;count;j;
__Profile = "__AServer";
begin
    L271:
    hasCommit := FALSE;
    i := AServerIns[pID].commitIndex + 1;
    tmpCommitIndex := i;
    Label_205_5: while i <= Len(AServerIns[pID].logs) do
        if tmpCommitIndex = i then
            count := 0;
            j := 1;
            hasCommit := FALSE;
            Label_210_13: while (j <= MaxServer /\ ~hasCommit) do
                if AServerIns[pID].matchIndex[(j)] >= i then
                    count := count + 1;
                    if count >= QurmMaxServer then
                        AServerIns[pID].commitIndex := i;
                        tmpCommitIndex := i;
                        hasCommit := TRUE;
                        __call_stack[self] := <<AServerIns[pID].commitIndex>> \o __call_stack[self];
                        call __AServer_ApplyAndResponseClient(self, pID);
                    end if;
                end if;
                Label_221_17: j := j + 1;
            end while;
        end if;
        Label_224_9: i := i + 1;
    end while;
    __call_stack[name] := <<hasCommit>> \o __call_stack[name];
    
    L303:
    return;
    Label_230_5: return;
end procedure;

procedure __AServer_SendAppendEntry(name, pID)
begin
    L308:
    req := Head(__call_stack[name]) ||
    dest := Head(Tail(__call_stack[name])) ||
    __call_stack[name] := Tail(Tail(__call_stack[name]));
    net_write(req, dest, "AppendEntries");
    Label_240_5: return;
end procedure;

procedure __AServer_HandleAppendEntriesResponseFunc(name, pID)
variables
resp;
__Profile = "__AServer";
begin
    L332:
    resp := Head(__call_stack[name]) ||
    __call_stack[name] := Tail(__call_stack[name]);
    AtomCheckTerm:
    if resp.Mterm > AServerIns[pID].currentTerm then
        AServerIns[pID].currentTerm := resp.Mterm ||
        AServerIns[pID].state := Follower ||
        AServerIns[pID].mleader := InitValue ||
        AServerIns[pID].mleader := resp.Msource ||
        AServerIns[pID].votedFor := 0;
    elsif resp.Mterm = AServerIns[pID].currentTerm then
        AServerIns[pID].mleader := resp.Msource;
        if resp.Msuccess then
            Label_261_13: AServerIns[pID].nextIndex[(resp.Msource)] := resp.MmatchIndex + 1 ||
            AServerIns[pID].matchIndex[(resp.Msource)] := resp.MmatchIndex;
            __call_stack[self] := <<>> \o __call_stack[self];
            call __AServer_AdvanceCommitIndex(self, pID);
        else
            Label_266_13: AServerIns[pID].nextIndex[(resp.Msource)] := Max(1, AServerIns[pID].nextIndex[(resp.Msource)]);
        end if;
    end if;
    Label_269_5: return;
end procedure;

procedure __AServer_HandleClientRequestFunc(name, pID)
variables
entry;req;success;resp;
__Profile = "__AServer";
begin
    L372:
    req := Head(__call_stack[name]) ||
    __call_stack[name] := Tail(__call_stack[name]);
    entry := [__reserved |-> 0];
    if AServerIns[pID].state = Leader then
        AtomAddLog:
        entry := [Mterm |-> AServerIns[pID].currentTerm, Mcommand |-> req.Mcommand, Client |-> req.Msource];
        AServerIns[pID].logs := Append(AServerIns[pID].logs, entry);
        Label_285_9: AServerIns[pID].matchIndex[(AServerIns[pID].me)] := Len(AServerIns[pID].logs) - 1 ||
        AServerIns[pID].nextIndex[(AServerIns[pID].me)] := Len(AServerIns[pID].logs);
        Heartbeat:
        __call_stack[self] := <<>> \o __call_stack[self];
        call __AServer_heartbeat(self, pID);
    else
        success := FALSE;
        resp := [Msuccess |-> success, Msource |-> AServerIns[pID].me, Mdest |-> req.Msource, Idx |-> req.Mcommand.Idx, LeaderHint |-> AServerIns[pID].mleader];
        net_write(resp, req.Msource, "ClientRequestResponse");
    end if;
    Label_295_5: return;
end procedure;

procedure __AServer_heartbeat(name, pID)
variables
i;lastEntry;prevLogIndex;prevLogTerm;entries;req;
__Profile = "__AServer";
begin
    L401:
    if AServerIns[pID].state = Leader then
        i := 1;
        AtomCheckTerm:
        while (i <= MaxServer /\ AServerIns[pID].state = Leader) do
            if i /= AServerIns[pID].me then
                lastEntry := Len(AServerIns[pID].logs);
                prevLogIndex := AServerIns[pID].nextIndex[(i)] - 1;
                prevLogTerm := 0;
                entries := SubSeqI(AServerIns[pID].logs, AServerIns[pID].nextIndex[(i)], lastEntry + 1);
                if prevLogIndex >= 1 then
                    Label_314_21: prevLogTerm := AServerIns[pID].logs[(prevLogIndex)].Mterm;
                end if;
                Label_316_17: req := [Mterm |-> AServerIns[pID].currentTerm, MprevLogIndex |-> prevLogIndex, MprevLogTerm |-> prevLogTerm, Mlog |-> entries, MleaderCommit |-> Min(AServerIns[pID].commitIndex, lastEntry), Msource |-> AServerIns[pID].me, Mdest |-> i];
                __call_stack[self] := <<req, i>> \o __call_stack[self];
                call __AServer_SendAppendEntry(self, pID);
            end if;
            Label_320_13: i := i + 1;
        end while;
        i := 1;
    end if;
    Label_324_5: return;
end procedure;
process AClientMain \in {"4Main"}
variables
    cmd, ok, nClient, clientReq, t1, dest, req, resp, pMap=[4Main |-> 4], pID=pMap[self];
begin
    Label_330_5: cmd := [__reserved |-> 0];
    ok := FALSE;
    nClient := 0;
    clientReq := 0;
    Label_334_5: clientNum_read(nClient);
    Label_335_5: while TRUE do
        reqCh_read(cmd);
        AClientIns[pID].reqId := AClientIns[pID].reqId + nClient ||
        clientReq := clientReq + 1;
        clientReqNum_write(clientReq);
        t1 := Time("now");
        Label_341_9: while ~ok do
            dest := AClientIns[pID].mleader;
            cmd.Idx := AClientIns[pID].reqId;
            req := [Mcommand |-> cmd, Msource |-> AClientIns[pID].me, Mdest |-> dest];
            net_write(req, dest, "ClientRequest");
            resp := [__reserved |-> 0];
            Label_347_13: net_read(resp, AClientIns[pID].me, "ClientRequestResponse");
            Label_348_13: while resp.Idx /= AClientIns[pID].reqId do
                net_read(resp, AClientIns[pID].me, "ClientRequestResponse");
            end while;
            if resp.Msuccess then
                respCh_write(resp);
                ok := TRUE;
                print(<<"client", AClientIns[pID].me, "resp success", resp>>);
            else
                if resp.LeaderHint /= InitValue then
                    AClientIns[pID].mleader := resp.LeaderHint;
                end if;
            end if;
        end while;
        ok := FALSE;
    end while;
end process;

process AServerHandleAppendEntriesRequest \in {"1HandleAppendEntriesRequest", "2HandleAppendEntriesRequest"}
variables
    req, pMap=[1HandleAppendEntriesRequest |-> 1,2HandleAppendEntriesRequest |-> 2], pID=pMap[self];
begin
    Label_369_5: req := [__reserved |-> 0];
    Label_370_5: while TRUE do
        net_read(req, AServerIns[pID].me, "AppendEntries");
        if (req.Mterm = AServerIns[pID].currentTerm /\ AServerIns[pID].state = Follower) then
            AServerIns[pID].mleader := req.Msource;
        end if;
        __call_stack[self] := <<req>> \o __call_stack[self];
        call __AServer_HandleAppendEntriesRequestFunc(self, pID);
    end while;
end process;

process AServerHandleAppendEntriesResponse \in {"1HandleAppendEntriesResponse", "2HandleAppendEntriesResponse"}
variables
    resp, pMap=[1HandleAppendEntriesResponse |-> 1,2HandleAppendEntriesResponse |-> 2], pID=pMap[self];
begin
    Label_384_5: resp := [__reserved |-> 0];
    Label_385_5: while TRUE do
        net_read(resp, AServerIns[pID].me, "AppendEntriesResponse");
        __call_stack[self] := <<resp>> \o __call_stack[self];
        call __AServer_HandleAppendEntriesResponseFunc(self, pID);
    end while;
end process;

process AServerHandleClientRequest \in {"1HandleClientRequest", "2HandleClientRequest"}
variables
    req, pMap=[1HandleClientRequest |-> 1,2HandleClientRequest |-> 2], pID=pMap[self];
begin
    Label_396_5: req := [__reserved |-> 0];
    Label_397_5: while TRUE do
        net_read(req, AServerIns[pID].me, "ClientRequest");
        __call_stack[self] := <<req>> \o __call_stack[self];
        call __AServer_HandleClientRequestFunc(self, pID);
    end while;
end process;

process AServerRequestVote \in {"1RequestVote", "2RequestVote"}
variables
    i, needVotes, election, req, pMap=[1RequestVote |-> 1,2RequestVote |-> 2], pID=pMap[self];
begin
    Label_408_5: i := 1;
    needVotes := TRUE;
    election := FALSE;
    req := [__reserved |-> 0];
    Label_412_5: while TRUE do
        serverVoteNum_write(10);
        AtomCheck:
        if AServerIns[pID].state /= Leader then
            needVotes := TRUE ||
            AServerIns[pID].state := Candidate ||
            AServerIns[pID].votedFor := AServerIns[pID].me ||
            AServerIns[pID].votesResponded := NewSet(AServerIns[pID].me) ||
            AServerIns[pID].votesGranted := NewSet(AServerIns[pID].me) ||
            AServerIns[pID].currentTerm := AServerIns[pID].currentTerm + 1 ||
            AServerIns[pID].mleader := InitValue;
            req := [Mterm |-> AServerIns[pID].currentTerm, MlastLogTerm |-> 0, MlastLogIndex |-> 0, Msource |-> AServerIns[pID].me, Mdest |-> 0];
        end if;
        CheckandVotes:
        if needVotes then
            needVotes := FALSE;
            Label_428_13: while i <= MaxServer do
                if i /= AServerIns[pID].me then
                    __call_stack[self] := <<req, i>> \o __call_stack[self];
                    call __AServer_SendRequestVote(self, pID);
                end if;
                Label_433_17: i := i + 1;
            end while;
            i := 1;
        end if;
    end while;
end process;

process AServerHandleRequestVoteRequest \in {"1HandleRequestVoteRequest", "2HandleRequestVoteRequest"}
variables
    req, resp, grant, needResp, pMap=[1HandleRequestVoteRequest |-> 1,2HandleRequestVoteRequest |-> 2], pID=pMap[self];
begin
    Label_444_5: req := [__reserved |-> 0];
    resp := [__reserved |-> 0];
    grant := FALSE;
    needResp := FALSE;
    Label_448_5: while TRUE do
        net_read(req, AServerIns[pID].me, "RequestVote");
        AtomHandle:
        if req.Mterm > AServerIns[pID].currentTerm then
            AServerIns[pID].currentTerm := req.Mterm ||
            AServerIns[pID].state := Follower ||
            AServerIns[pID].mleader := InitValue ||
            AServerIns[pID].votedFor := 0;
        end if;
        if req.Mterm = AServerIns[pID].currentTerm then
            grant := (req.Mterm <= AServerIns[pID].currentTerm /\ (AServerIns[pID].votedFor = 0 \/ AServerIns[pID].votedFor = req.Msource));
            resp := [Mterm |-> AServerIns[pID].currentTerm, Msource |-> AServerIns[pID].me, Mgrant |-> grant];
            needResp := TRUE;
        end if;
        EndAtomHandle:
        if needResp then
            needResp := FALSE;
            net_write(resp, req.Msource, "RequestVoteResponse");
        end if;
    end while;
end process;

process AServerHandleRequestVoteResponse \in {"1HandleRequestVoteResponse", "2HandleRequestVoteResponse"}
variables
    resp, i, pMap=[1HandleRequestVoteResponse |-> 1,2HandleRequestVoteResponse |-> 2], pID=pMap[self];
begin
    Label_474_5: resp := [__reserved |-> 0];
    Label_475_5: while TRUE do
        net_read(resp, AServerIns[pID].me, "RequestVoteResponse");
        if resp.Mterm > AServerIns[pID].currentTerm then
            AServerIns[pID].currentTerm := resp.Mterm ||
            AServerIns[pID].state := Follower ||
            AServerIns[pID].votedFor := 0 ||
            AServerIns[pID].mleader := InitValue;
        end if;
        if (resp.Mterm = AServerIns[pID].currentTerm /\ AServerIns[pID].state = Candidate) then
            if (resp.Mgrant /\ ~Contains(AServerIns[pID].votesGranted, resp.Msource)) then
                Label_485_17: AServerIns[pID].votesGranted := Add(AServerIns[pID].votesGranted, resp.Msource);
            end if;
            Label_487_13: if ~Contains(AServerIns[pID].votesResponded, resp.Msource) then
                AServerIns[pID].votesResponded := Add(AServerIns[pID].votesResponded, resp.Msource);
            end if;
            AtomCheck:
            if (Cardinality(AServerIns[pID].votesGranted) >= QurmMaxServer /\ AServerIns[pID].state = Candidate /\ AServerIns[pID].currentTerm = resp.Mterm) then
                AServerIns[pID].state := Leader ||
                AServerIns[pID].mleader := AServerIns[pID].me ||
                AServerIns[pID].nextIndex := NewMap(MaxServer, 1) ||
                AServerIns[pID].matchIndex := NewMap(MaxServer, 0);
                i := 1;
                Label_497_17: while i <= MaxServer do
                    if i /= AServerIns[pID].me then
                        AServerIns[pID].nextIndex[(i)] := Len(AServerIns[pID].logs) + 1 ||
                        AServerIns[pID].matchIndex[(i)] := 0;
                    else
                        AServerIns[pID].nextIndex[(i)] := Len(AServerIns[pID].logs) + 1 ||
                        AServerIns[pID].matchIndex[(i)] := Len(AServerIns[pID].logs);
                    end if;
                    i := i + 1;
                end while;
            end if;
            CheckandVotes:
            if Cardinality(AServerIns[pID].votesResponded) - Cardinality(AServerIns[pID].votesGranted) >= QurmMaxServer then
                AServerIns[pID].state := Follower;
                Label_511_17: AServerIns[pID].votedFor := 0;
                Label_512_17: AServerIns[pID].mleader := InitValue;
            end if;
        end if;
    end while;
end process;
end algorithm;*)
\* BEGIN TRANSLATION (chksum(pcal) = "e9b136a0" /\ chksum(tla) = "d6f784f3")
\* Label AtomCheckTerm of procedure __AServer_HandleAppendEntriesRequestFunc at line 113 col 5 changed to AtomCheckTerm_
\* Label AtomCheckTerm of procedure __AServer_HandleAppendEntriesResponseFunc at line 252 col 5 changed to AtomCheckTerm__
\* Label AtomCheck of process AServerRequestVote at line 415 col 9 changed to AtomCheck_
\* Label CheckandVotes of process AServerRequestVote at line 426 col 9 changed to CheckandVotes_
\* Process variable dest of process AClientMain at line 328 col 38 changed to dest_
\* Process variable req of process AClientMain at line 328 col 44 changed to req_
\* Process variable resp of process AClientMain at line 328 col 49 changed to resp_
\* Process variable pMap of process AClientMain at line 328 col 55 changed to pMap_
\* Process variable pID of process AClientMain at line 328 col 75 changed to pID_
\* Process variable req of process AServerHandleAppendEntriesRequest at line 367 col 5 changed to req_A
\* Process variable pMap of process AServerHandleAppendEntriesRequest at line 367 col 10 changed to pMap_A
\* Process variable pID of process AServerHandleAppendEntriesRequest at line 367 col 86 changed to pID_A
\* Process variable resp of process AServerHandleAppendEntriesResponse at line 382 col 5 changed to resp_A
\* Process variable pMap of process AServerHandleAppendEntriesResponse at line 382 col 11 changed to pMap_AS
\* Process variable pID of process AServerHandleAppendEntriesResponse at line 382 col 89 changed to pID_AS
\* Process variable req of process AServerHandleClientRequest at line 394 col 5 changed to req_AS
\* Process variable pMap of process AServerHandleClientRequest at line 394 col 10 changed to pMap_ASe
\* Process variable pID of process AServerHandleClientRequest at line 394 col 72 changed to pID_ASe
\* Process variable i of process AServerRequestVote at line 406 col 5 changed to i_
\* Process variable req of process AServerRequestVote at line 406 col 29 changed to req_ASe
\* Process variable pMap of process AServerRequestVote at line 406 col 34 changed to pMap_ASer
\* Process variable pID of process AServerRequestVote at line 406 col 80 changed to pID_ASer
\* Process variable req of process AServerHandleRequestVoteRequest at line 442 col 5 changed to req_ASer
\* Process variable resp of process AServerHandleRequestVoteRequest at line 442 col 10 changed to resp_AS
\* Process variable pMap of process AServerHandleRequestVoteRequest at line 442 col 33 changed to pMap_AServ
\* Process variable pID of process AServerHandleRequestVoteRequest at line 442 col 105 changed to pID_AServ
\* Process variable resp of process AServerHandleRequestVoteResponse at line 472 col 5 changed to resp_ASe
\* Process variable i of process AServerHandleRequestVoteResponse at line 472 col 11 changed to i_A
\* Process variable pID of process AServerHandleRequestVoteResponse at line 472 col 88 changed to pID_AServe
\* Procedure variable resp of procedure __AServer_HandleAppendEntriesRequestFunc at line 102 col 1 changed to resp__
\* Procedure variable success of procedure __AServer_HandleAppendEntriesRequestFunc at line 102 col 6 changed to success_
\* Procedure variable req of procedure __AServer_HandleAppendEntriesRequestFunc at line 102 col 30 changed to req__
\* Procedure variable __Profile of procedure __AServer_HandleAppendEntriesRequestFunc at line 103 col 1 changed to __Profile_
\* Procedure variable success of procedure __AServer_ApplyAndResponseClient at line 175 col 1 changed to success__
\* Procedure variable resp of procedure __AServer_ApplyAndResponseClient at line 175 col 21 changed to resp___
\* Procedure variable __Profile of procedure __AServer_ApplyAndResponseClient at line 176 col 1 changed to __Profile__
\* Procedure variable i of procedure __AServer_AdvanceCommitIndex at line 198 col 11 changed to i__
\* Procedure variable __Profile of procedure __AServer_AdvanceCommitIndex at line 199 col 1 changed to __Profile___
\* Procedure variable resp of procedure __AServer_HandleAppendEntriesResponseFunc at line 245 col 1 changed to resp___A
\* Procedure variable __Profile of procedure __AServer_HandleAppendEntriesResponseFunc at line 246 col 1 changed to __Profile___A
\* Procedure variable req of procedure __AServer_HandleClientRequestFunc at line 274 col 7 changed to req___
\* Procedure variable __Profile of procedure __AServer_HandleClientRequestFunc at line 275 col 1 changed to __Profile___AS
\* Parameter name of procedure __AServer_SendRequestVote at line 90 col 37 changed to name_
\* Parameter pID of procedure __AServer_SendRequestVote at line 90 col 43 changed to pID__
\* Parameter name of procedure __AServer_HandleAppendEntriesRequestFunc at line 100 col 52 changed to name__
\* Parameter pID of procedure __AServer_HandleAppendEntriesRequestFunc at line 100 col 58 changed to pID___
\* Parameter name of procedure __AServer_ApplyAndResponseClient at line 173 col 44 changed to name___
\* Parameter pID of procedure __AServer_ApplyAndResponseClient at line 173 col 50 changed to pID___A
\* Parameter name of procedure __AServer_AdvanceCommitIndex at line 196 col 40 changed to name___A
\* Parameter pID of procedure __AServer_AdvanceCommitIndex at line 196 col 46 changed to pID___AS
\* Parameter name of procedure __AServer_SendAppendEntry at line 233 col 37 changed to name___AS
\* Parameter pID of procedure __AServer_SendAppendEntry at line 233 col 43 changed to pID___ASe
\* Parameter name of procedure __AServer_HandleAppendEntriesResponseFunc at line 243 col 53 changed to name___ASe
\* Parameter pID of procedure __AServer_HandleAppendEntriesResponseFunc at line 243 col 59 changed to pID___ASer
\* Parameter name of procedure __AServer_HandleClientRequestFunc at line 272 col 45 changed to name___ASer
\* Parameter pID of procedure __AServer_HandleClientRequestFunc at line 272 col 51 changed to pID___AServ
CONSTANT defaultInitValue
VARIABLES net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, 
          __call_stack, __path, AClientIns, AServerIns, pc, stack, name_, 
          pID__, name__, pID___, resp__, success_, logOk, needReply, req__, 
          mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, 
          id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, 
          i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, 
          name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, 
          pID___AServ, entry, req___, success, resp, __Profile___AS, name, 
          pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, 
          __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, 
          pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, 
          pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, 
          pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, 
          resp_ASe, i_A, pMap, pID_AServe

vars == << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, 
           __call_stack, __path, AClientIns, AServerIns, pc, stack, name_, 
           pID__, name__, pID___, resp__, success_, logOk, needReply, req__, 
           mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, 
           id, idx, resp___, value, __Profile__, name___A, pID___AS, 
           hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, 
           pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, 
           name___ASer, pID___AServ, entry, req___, success, resp, 
           __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, 
           entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, 
           req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, 
           pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, 
           req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, 
           pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

ProcSet == ({"4Main"}) \cup ({"1HandleAppendEntriesRequest", "2HandleAppendEntriesRequest"}) \cup ({"1HandleAppendEntriesResponse", "2HandleAppendEntriesResponse"}) \cup ({"1HandleClientRequest", "2HandleClientRequest"}) \cup ({"1RequestVote", "2RequestVote"}) \cup ({"1HandleRequestVoteRequest", "2HandleRequestVoteRequest"}) \cup ({"1HandleRequestVoteResponse", "2HandleRequestVoteResponse"})

Init == (* Global variables *)
        /\ net = [ins \in {1, 2, 4} |-> [chan \in {"ClientRequest", "ClientRequestResponse", "RequestVote", "RequestVoteResponse", "AppendEntries", "AppendEntriesResponse"} |-> <<>>]]
        /\ reqCh = <<[Type |-> "Put", Key |-> "x", Value |-> "1", Idx |-> 1]>>
        /\ respCh = <<>>
        /\ clientNum = 1
        /\ log = <<>>
        /\ clientReqNum = 0
        /\ serverVoteNum = 0
        /\ __call_stack = [p \in {"2HandleAppendEntriesResponse", "2RequestVote", "1HandleRequestVoteRequest", "2HandleRequestVoteRequest", "4Main", "2HandleAppendEntriesRequest", "1HandleAppendEntriesResponse", "1RequestVote", "1HandleRequestVoteResponse", "1HandleClientRequest", "2HandleClientRequest", "2HandleRequestVoteResponse", "1HandleAppendEntriesRequest"} |-> <<>>]
        /\ __path = 0
        /\ AClientIns = [r \in {4} |-> [mleader |-> 1,reqId |-> r,me |-> r]]
        /\ AServerIns = [r \in {1, 2} |-> [currentTerm |-> 0,state |-> 0,votedFor |-> 0,commitIndex |-> 0,me |-> r,mleader |-> InitValue,votesResponded |-> NewSetInit,votesGranted |-> NewSetInit,logs |-> NewLogEntry,nextIndex |-> NewMap(MaxServer, 1),matchIndex |-> NewMap(MaxServer, 0),kvStore |-> NewStore]]
        (* Procedure __AServer_SendRequestVote *)
        /\ name_ = [ self \in ProcSet |-> defaultInitValue]
        /\ pID__ = [ self \in ProcSet |-> defaultInitValue]
        (* Procedure __AServer_HandleAppendEntriesRequestFunc *)
        /\ name__ = [ self \in ProcSet |-> defaultInitValue]
        /\ pID___ = [ self \in ProcSet |-> defaultInitValue]
        /\ resp__ = [ self \in ProcSet |-> defaultInitValue]
        /\ success_ = [ self \in ProcSet |-> defaultInitValue]
        /\ logOk = [ self \in ProcSet |-> defaultInitValue]
        /\ needReply = [ self \in ProcSet |-> defaultInitValue]
        /\ req__ = [ self \in ProcSet |-> defaultInitValue]
        /\ mIndex = [ self \in ProcSet |-> defaultInitValue]
        /\ index = [ self \in ProcSet |-> defaultInitValue]
        /\ tmpi = [ self \in ProcSet |-> defaultInitValue]
        /\ __Profile_ = [ self \in ProcSet |-> "__AServer"]
        (* Procedure __AServer_ApplyAndResponseClient *)
        /\ name___ = [ self \in ProcSet |-> defaultInitValue]
        /\ pID___A = [ self \in ProcSet |-> defaultInitValue]
        /\ success__ = [ self \in ProcSet |-> defaultInitValue]
        /\ dest = [ self \in ProcSet |-> defaultInitValue]
        /\ id = [ self \in ProcSet |-> defaultInitValue]
        /\ idx = [ self \in ProcSet |-> defaultInitValue]
        /\ resp___ = [ self \in ProcSet |-> defaultInitValue]
        /\ value = [ self \in ProcSet |-> defaultInitValue]
        /\ __Profile__ = [ self \in ProcSet |-> "__AServer"]
        (* Procedure __AServer_AdvanceCommitIndex *)
        /\ name___A = [ self \in ProcSet |-> defaultInitValue]
        /\ pID___AS = [ self \in ProcSet |-> defaultInitValue]
        /\ hasCommit = [ self \in ProcSet |-> defaultInitValue]
        /\ i__ = [ self \in ProcSet |-> defaultInitValue]
        /\ tmpCommitIndex = [ self \in ProcSet |-> defaultInitValue]
        /\ count = [ self \in ProcSet |-> defaultInitValue]
        /\ j = [ self \in ProcSet |-> defaultInitValue]
        /\ __Profile___ = [ self \in ProcSet |-> "__AServer"]
        (* Procedure __AServer_SendAppendEntry *)
        /\ name___AS = [ self \in ProcSet |-> defaultInitValue]
        /\ pID___ASe = [ self \in ProcSet |-> defaultInitValue]
        (* Procedure __AServer_HandleAppendEntriesResponseFunc *)
        /\ name___ASe = [ self \in ProcSet |-> defaultInitValue]
        /\ pID___ASer = [ self \in ProcSet |-> defaultInitValue]
        /\ resp___A = [ self \in ProcSet |-> defaultInitValue]
        /\ __Profile___A = [ self \in ProcSet |-> "__AServer"]
        (* Procedure __AServer_HandleClientRequestFunc *)
        /\ name___ASer = [ self \in ProcSet |-> defaultInitValue]
        /\ pID___AServ = [ self \in ProcSet |-> defaultInitValue]
        /\ entry = [ self \in ProcSet |-> defaultInitValue]
        /\ req___ = [ self \in ProcSet |-> defaultInitValue]
        /\ success = [ self \in ProcSet |-> defaultInitValue]
        /\ resp = [ self \in ProcSet |-> defaultInitValue]
        /\ __Profile___AS = [ self \in ProcSet |-> "__AServer"]
        (* Procedure __AServer_heartbeat *)
        /\ name = [ self \in ProcSet |-> defaultInitValue]
        /\ pID = [ self \in ProcSet |-> defaultInitValue]
        /\ i = [ self \in ProcSet |-> defaultInitValue]
        /\ lastEntry = [ self \in ProcSet |-> defaultInitValue]
        /\ prevLogIndex = [ self \in ProcSet |-> defaultInitValue]
        /\ prevLogTerm = [ self \in ProcSet |-> defaultInitValue]
        /\ entries = [ self \in ProcSet |-> defaultInitValue]
        /\ req = [ self \in ProcSet |-> defaultInitValue]
        /\ __Profile = [ self \in ProcSet |-> "__AServer"]
        (* Process AClientMain *)
        /\ cmd = [self \in {"4Main"} |-> defaultInitValue]
        /\ ok = [self \in {"4Main"} |-> defaultInitValue]
        /\ nClient = [self \in {"4Main"} |-> defaultInitValue]
        /\ clientReq = [self \in {"4Main"} |-> defaultInitValue]
        /\ t1 = [self \in {"4Main"} |-> defaultInitValue]
        /\ dest_ = [self \in {"4Main"} |-> defaultInitValue]
        /\ req_ = [self \in {"4Main"} |-> defaultInitValue]
        /\ resp_ = [self \in {"4Main"} |-> defaultInitValue]
        /\ pMap_ = [self \in {"4Main"} |-> [4Main |-> 4]]
        /\ pID_ = [self \in {"4Main"} |-> pMap_[self][self]]
        (* Process AServerHandleAppendEntriesRequest *)
        /\ req_A = [self \in {"1HandleAppendEntriesRequest", "2HandleAppendEntriesRequest"} |-> defaultInitValue]
        /\ pMap_A = [self \in {"1HandleAppendEntriesRequest", "2HandleAppendEntriesRequest"} |-> [1HandleAppendEntriesRequest |-> 1,2HandleAppendEntriesRequest |-> 2]]
        /\ pID_A = [self \in {"1HandleAppendEntriesRequest", "2HandleAppendEntriesRequest"} |-> pMap_A[self][self]]
        (* Process AServerHandleAppendEntriesResponse *)
        /\ resp_A = [self \in {"1HandleAppendEntriesResponse", "2HandleAppendEntriesResponse"} |-> defaultInitValue]
        /\ pMap_AS = [self \in {"1HandleAppendEntriesResponse", "2HandleAppendEntriesResponse"} |-> [1HandleAppendEntriesResponse |-> 1,2HandleAppendEntriesResponse |-> 2]]
        /\ pID_AS = [self \in {"1HandleAppendEntriesResponse", "2HandleAppendEntriesResponse"} |-> pMap_AS[self][self]]
        (* Process AServerHandleClientRequest *)
        /\ req_AS = [self \in {"1HandleClientRequest", "2HandleClientRequest"} |-> defaultInitValue]
        /\ pMap_ASe = [self \in {"1HandleClientRequest", "2HandleClientRequest"} |-> [1HandleClientRequest |-> 1,2HandleClientRequest |-> 2]]
        /\ pID_ASe = [self \in {"1HandleClientRequest", "2HandleClientRequest"} |-> pMap_ASe[self][self]]
        (* Process AServerRequestVote *)
        /\ i_ = [self \in {"1RequestVote", "2RequestVote"} |-> defaultInitValue]
        /\ needVotes = [self \in {"1RequestVote", "2RequestVote"} |-> defaultInitValue]
        /\ election = [self \in {"1RequestVote", "2RequestVote"} |-> defaultInitValue]
        /\ req_ASe = [self \in {"1RequestVote", "2RequestVote"} |-> defaultInitValue]
        /\ pMap_ASer = [self \in {"1RequestVote", "2RequestVote"} |-> [1RequestVote |-> 1,2RequestVote |-> 2]]
        /\ pID_ASer = [self \in {"1RequestVote", "2RequestVote"} |-> pMap_ASer[self][self]]
        (* Process AServerHandleRequestVoteRequest *)
        /\ req_ASer = [self \in {"1HandleRequestVoteRequest", "2HandleRequestVoteRequest"} |-> defaultInitValue]
        /\ resp_AS = [self \in {"1HandleRequestVoteRequest", "2HandleRequestVoteRequest"} |-> defaultInitValue]
        /\ grant = [self \in {"1HandleRequestVoteRequest", "2HandleRequestVoteRequest"} |-> defaultInitValue]
        /\ needResp = [self \in {"1HandleRequestVoteRequest", "2HandleRequestVoteRequest"} |-> defaultInitValue]
        /\ pMap_AServ = [self \in {"1HandleRequestVoteRequest", "2HandleRequestVoteRequest"} |-> [1HandleRequestVoteRequest |-> 1,2HandleRequestVoteRequest |-> 2]]
        /\ pID_AServ = [self \in {"1HandleRequestVoteRequest", "2HandleRequestVoteRequest"} |-> pMap_AServ[self][self]]
        (* Process AServerHandleRequestVoteResponse *)
        /\ resp_ASe = [self \in {"1HandleRequestVoteResponse", "2HandleRequestVoteResponse"} |-> defaultInitValue]
        /\ i_A = [self \in {"1HandleRequestVoteResponse", "2HandleRequestVoteResponse"} |-> defaultInitValue]
        /\ pMap = [self \in {"1HandleRequestVoteResponse", "2HandleRequestVoteResponse"} |-> [1HandleRequestVoteResponse |-> 1,2HandleRequestVoteResponse |-> 2]]
        /\ pID_AServe = [self \in {"1HandleRequestVoteResponse", "2HandleRequestVoteResponse"} |-> pMap[self][self]]
        /\ stack = [self \in ProcSet |-> << >>]
        /\ pc = [self \in ProcSet |-> CASE self \in {"4Main"} -> "Label_330_5"
                                        [] self \in {"1HandleAppendEntriesRequest", "2HandleAppendEntriesRequest"} -> "Label_369_5"
                                        [] self \in {"1HandleAppendEntriesResponse", "2HandleAppendEntriesResponse"} -> "Label_384_5"
                                        [] self \in {"1HandleClientRequest", "2HandleClientRequest"} -> "Label_396_5"
                                        [] self \in {"1RequestVote", "2RequestVote"} -> "Label_408_5"
                                        [] self \in {"1HandleRequestVoteRequest", "2HandleRequestVoteRequest"} -> "Label_444_5"
                                        [] self \in {"1HandleRequestVoteResponse", "2HandleRequestVoteResponse"} -> "Label_474_5"]

L125(self) == /\ pc[self] = "L125"
              /\ /\ __call_stack' = [__call_stack EXCEPT ![name_[self]] = Tail(Tail(__call_stack[name_[self]]))]
                 /\ dest' = [dest EXCEPT ![self] = Head(Tail(__call_stack[name_[self]]))]
                 /\ req' = [req EXCEPT ![self] = Head(__call_stack[name_[self]])]
              /\ net' = [net EXCEPT ![(dest'[self])][("RequestVote")] = Append(net[(dest'[self])][("RequestVote")], req'[self])]
              /\ pc' = [pc EXCEPT ![self] = "Label_97_5"]
              /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_97_5(self) == /\ pc[self] = "Label_97_5"
                    /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
                    /\ name_' = [name_ EXCEPT ![self] = Head(stack[self]).name_]
                    /\ pID__' = [pID__ EXCEPT ![self] = Head(stack[self]).pID__]
                    /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
                    /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

__AServer_SendRequestVote(self) == L125(self) \/ Label_97_5(self)

L135(self) == /\ pc[self] = "L135"
              /\ /\ __call_stack' = [__call_stack EXCEPT ![name__[self]] = Tail(__call_stack[name__[self]])]
                 /\ req__' = [req__ EXCEPT ![self] = Head(__call_stack[name__[self]])]
              /\ resp__' = [resp__ EXCEPT ![self] = [__reserved |-> 0]]
              /\ success_' = [success_ EXCEPT ![self] = FALSE]
              /\ logOk' = [logOk EXCEPT ![self] = FALSE]
              /\ needReply' = [needReply EXCEPT ![self] = FALSE]
              /\ pc' = [pc EXCEPT ![self] = "AtomCheckTerm_"]
              /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AtomCheckTerm_(self) == /\ pc[self] = "AtomCheckTerm_"
                        /\ IF req__[self].Mterm > AServerIns[pID___[self]].currentTerm
                              THEN /\ AServerIns' = [AServerIns EXCEPT ![pID___[self]].currentTerm = req__[self].Mterm,
                                                                       ![pID___[self]].votedFor = 0,
                                                                       ![pID___[self]].state = Follower,
                                                                       ![pID___[self]].mleader = InitValue,
                                                                       ![pID___[self]].mleader = req__[self].Msource]
                              ELSE /\ TRUE
                                   /\ UNCHANGED AServerIns
                        /\ mIndex' = [mIndex EXCEPT ![self] = InitValue]
                        /\ index' = [index EXCEPT ![self] = 0]
                        /\ IF (req__[self].MprevLogIndex < 1 \/ (req__[self].MprevLogIndex <= Len(AServerIns'[pID___[self]].logs) /\ req__[self].MprevLogIndex >= 1 /\ AServerIns'[pID___[self]].logs[(req__[self].MprevLogIndex)].Mterm = req__[self].MprevLogTerm))
                              THEN /\ logOk' = [logOk EXCEPT ![self] = TRUE]
                                   /\ PrintT((<<AServerIns'[pID___[self]].me, "log ok", Len(AServerIns'[pID___[self]].logs), req__[self].MprevLogIndex, req__[self].MprevLogTerm, req__[self].Mterm, AServerIns'[pID___[self]].state, AServerIns'[pID___[self]].currentTerm>>))
                              ELSE /\ logOk' = [logOk EXCEPT ![self] = FALSE]
                        /\ IF req__[self].Mterm <= AServerIns'[pID___[self]].currentTerm
                              THEN /\ IF (req__[self].Mterm < AServerIns'[pID___[self]].currentTerm \/ (req__[self].Mterm = AServerIns'[pID___[self]].currentTerm /\ ~logOk'[self] /\ AServerIns'[pID___[self]].state = Follower))
                                         THEN /\ needReply' = [needReply EXCEPT ![self] = TRUE]
                                              /\ pc' = [pc EXCEPT ![self] = "EndAtomCheckState"]
                                         ELSE /\ IF (req__[self].Mterm = AServerIns'[pID___[self]].currentTerm /\ AServerIns'[pID___[self]].state = Candidate)
                                                    THEN /\ pc' = [pc EXCEPT ![self] = "Label_132_13"]
                                                    ELSE /\ IF (req__[self].Mterm = AServerIns'[pID___[self]].currentTerm /\ AServerIns'[pID___[self]].state = Follower /\ logOk'[self])
                                                               THEN /\ pc' = [pc EXCEPT ![self] = "Label_137_13"]
                                                               ELSE /\ pc' = [pc EXCEPT ![self] = "EndAtomCheckState"]
                                              /\ UNCHANGED needReply
                              ELSE /\ pc' = [pc EXCEPT ![self] = "Label_166_5"]
                                   /\ UNCHANGED needReply
                        /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, req__, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

EndAtomCheckState(self) == /\ pc[self] = "EndAtomCheckState"
                           /\ IF needReply[self]
                                 THEN /\ needReply' = [needReply EXCEPT ![self] = FALSE]
                                      /\ resp__' = [resp__ EXCEPT ![self] = [Mterm |-> AServerIns[pID___[self]].currentTerm, Msource |-> AServerIns[pID___[self]].me, Msuccess |-> success_[self], Mdest |-> req__[self].Msource, MmatchIndex |-> mIndex[self]]]
                                      /\ net' = [net EXCEPT ![((req__[self].Msource))][("AppendEntriesResponse")] = Append(net[((req__[self].Msource))][("AppendEntriesResponse")], resp__'[self])]
                                 ELSE /\ TRUE
                                      /\ UNCHANGED << net, resp__, needReply >>
                           /\ pc' = [pc EXCEPT ![self] = "Label_166_5"]
                           /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, success_, logOk, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_132_13(self) == /\ pc[self] = "Label_132_13"
                      /\ /\ AServerIns' = [AServerIns EXCEPT ![pID___[self]].state = Follower,
                                                             ![pID___[self]].votedFor = 0,
                                                             ![pID___[self]].mleader = InitValue]
                         /\ success_' = [success_ EXCEPT ![self] = TRUE]
                      /\ pc' = [pc EXCEPT ![self] = "EndAtomCheckState"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_137_13(self) == /\ pc[self] = "Label_137_13"
                      /\ index' = [index EXCEPT ![self] = req__[self].MprevLogIndex + 1]
                      /\ PrintT((<<AServerIns[pID___[self]].me, "wait update logs", index'[self], Len(AServerIns[pID___[self]].logs), (Len(req__[self].Mlog) = 0 \/ (Len(req__[self].Mlog) > 0 /\ index'[self] >= 1 /\ index'[self] <= Len(AServerIns[pID___[self]].logs) /\ req__[self].Mlog[(1)].Mterm = AServerIns[pID___[self]].logs[(index'[self])].Mterm) \/ (Len(req__[self].Mlog) > 0 /\ index'[self] = Len(AServerIns[pID___[self]].logs)))>>))
                      /\ IF (Len(req__[self].Mlog) = 0 \/ (Len(req__[self].Mlog) > 0 /\ index'[self] >= 1 /\ index'[self] <= Len(AServerIns[pID___[self]].logs) /\ req__[self].Mlog[(1)].Mterm = AServerIns[pID___[self]].logs[(index'[self])].Mterm) \/ (Len(req__[self].Mlog) > 0 /\ index'[self] = Len(AServerIns[pID___[self]].logs) + 1))
                            THEN /\ AServerIns' = [AServerIns EXCEPT ![pID___[self]].logs = LogAppend(SubSeqI(AServerIns[pID___[self]].logs, 1, req__[self].MprevLogIndex + 1), req__[self].Mlog),
                                                                     ![pID___[self]].commitIndex = req__[self].MleaderCommit]
                                 /\ success_' = [success_ EXCEPT ![self] = TRUE]
                                 /\ mIndex' = [mIndex EXCEPT ![self] = req__[self].MprevLogIndex + Len(req__[self].Mlog)]
                                 /\ PrintT((<<AServerIns'[pID___[self]].me, "update logs", mIndex'[self], Len(AServerIns'[pID___[self]].logs)>>))
                                 /\ needReply' = [needReply EXCEPT ![self] = TRUE]
                                 /\ tmpi' = [tmpi EXCEPT ![self] = 1]
                                 /\ pc' = [pc EXCEPT ![self] = "Label_147_17"]
                            ELSE /\ IF (Len(req__[self].Mlog) > 0 /\ Len(AServerIns[pID___[self]].logs) >= index'[self] /\ index'[self] >= 1 /\ req__[self].Mlog[(1)].Mterm /= AServerIns[pID___[self]].logs[(index'[self])].Mterm)
                                       THEN /\ AServerIns' = [AServerIns EXCEPT ![pID___[self]].logs = SubSeqI(AServerIns[pID___[self]].logs, 1, Len(AServerIns[pID___[self]].logs))]
                                       ELSE /\ TRUE
                                            /\ UNCHANGED AServerIns
                                 /\ pc' = [pc EXCEPT ![self] = "EndAtomCheckState"]
                                 /\ UNCHANGED << success_, needReply, mIndex, 
                                                 tmpi >>
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, logOk, req__, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_147_17(self) == /\ pc[self] = "Label_147_17"
                      /\ IF tmpi[self] <= Len(req__[self].Mlog)
                            THEN /\ IF req__[self].Mlog[(tmpi[self])].Mcommand.Type = "Put"
                                       THEN /\ AServerIns' = [AServerIns EXCEPT ![pID___[self]].kvStore = AddKey(AServerIns[pID___[self]].kvStore, req__[self].Mlog[(tmpi[self])].Mcommand.Key, req__[self].Mlog[(tmpi[self])].Mcommand.Value)]
                                       ELSE /\ AServerIns' = [AServerIns EXCEPT ![pID___[self]].kvStore = AddKey(AServerIns[pID___[self]].kvStore, req__[self].Mlog[(tmpi[self])].Mcommand.Key, "")]
                                 /\ tmpi' = [tmpi EXCEPT ![self] = tmpi[self] + 1]
                                 /\ pc' = [pc EXCEPT ![self] = "Label_147_17"]
                            ELSE /\ pc' = [pc EXCEPT ![self] = "EndAtomCheckState"]
                                 /\ UNCHANGED << AServerIns, tmpi >>
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_166_5(self) == /\ pc[self] = "Label_166_5"
                     /\ __call_stack' = [__call_stack EXCEPT ![name__[self]] = <<>> \o __call_stack[name__[self]]]
                     /\ pc' = [pc EXCEPT ![self] = "L214"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

L214(self) == /\ pc[self] = "L214"
              /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
              /\ resp__' = [resp__ EXCEPT ![self] = Head(stack[self]).resp__]
              /\ success_' = [success_ EXCEPT ![self] = Head(stack[self]).success_]
              /\ logOk' = [logOk EXCEPT ![self] = Head(stack[self]).logOk]
              /\ needReply' = [needReply EXCEPT ![self] = Head(stack[self]).needReply]
              /\ req__' = [req__ EXCEPT ![self] = Head(stack[self]).req__]
              /\ mIndex' = [mIndex EXCEPT ![self] = Head(stack[self]).mIndex]
              /\ index' = [index EXCEPT ![self] = Head(stack[self]).index]
              /\ tmpi' = [tmpi EXCEPT ![self] = Head(stack[self]).tmpi]
              /\ __Profile_' = [__Profile_ EXCEPT ![self] = Head(stack[self]).__Profile_]
              /\ name__' = [name__ EXCEPT ![self] = Head(stack[self]).name__]
              /\ pID___' = [pID___ EXCEPT ![self] = Head(stack[self]).pID___]
              /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
              /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, name_, pID__, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_170_5(self) == /\ pc[self] = "Label_170_5"
                     /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
                     /\ resp__' = [resp__ EXCEPT ![self] = Head(stack[self]).resp__]
                     /\ success_' = [success_ EXCEPT ![self] = Head(stack[self]).success_]
                     /\ logOk' = [logOk EXCEPT ![self] = Head(stack[self]).logOk]
                     /\ needReply' = [needReply EXCEPT ![self] = Head(stack[self]).needReply]
                     /\ req__' = [req__ EXCEPT ![self] = Head(stack[self]).req__]
                     /\ mIndex' = [mIndex EXCEPT ![self] = Head(stack[self]).mIndex]
                     /\ index' = [index EXCEPT ![self] = Head(stack[self]).index]
                     /\ tmpi' = [tmpi EXCEPT ![self] = Head(stack[self]).tmpi]
                     /\ __Profile_' = [__Profile_ EXCEPT ![self] = Head(stack[self]).__Profile_]
                     /\ name__' = [name__ EXCEPT ![self] = Head(stack[self]).name__]
                     /\ pID___' = [pID___ EXCEPT ![self] = Head(stack[self]).pID___]
                     /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, name_, pID__, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

__AServer_HandleAppendEntriesRequestFunc(self) == L135(self)
                                                     \/ AtomCheckTerm_(self)
                                                     \/ EndAtomCheckState(self)
                                                     \/ Label_132_13(self)
                                                     \/ Label_137_13(self)
                                                     \/ Label_147_17(self)
                                                     \/ Label_166_5(self)
                                                     \/ L214(self)
                                                     \/ Label_170_5(self)

L241(self) == /\ pc[self] = "L241"
              /\ /\ __call_stack' = [__call_stack EXCEPT ![name___[self]] = Tail(__call_stack[name___[self]])]
                 /\ id' = [id EXCEPT ![self] = Head(__call_stack[name___[self]])]
              /\ success__' = [success__ EXCEPT ![self] = TRUE]
              /\ dest' = [dest EXCEPT ![self] = AServerIns[pID___A[self]].logs[(id'[self])].Client]
              /\ idx' = [idx EXCEPT ![self] = AServerIns[pID___A[self]].logs[(id'[self])].Mcommand.Idx]
              /\ resp___' = [resp___ EXCEPT ![self] = [__reserved |-> 0]]
              /\ value' = [value EXCEPT ![self] = ""]
              /\ IF AServerIns[pID___A[self]].logs[(id'[self])].Mcommand.Type = "Get"
                    THEN /\ pc' = [pc EXCEPT ![self] = "Label_187_9"]
                         /\ UNCHANGED AServerIns
                    ELSE /\ AServerIns' = [AServerIns EXCEPT ![pID___A[self]].kvStore[(AServerIns[pID___A[self]].logs[(id'[self])].Mcommand.Key)] = AServerIns[pID___A[self]].logs[(id'[self])].Mcommand.Value]
                         /\ pc' = [pc EXCEPT ![self] = "Label_191_5"]
              /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_187_9(self) == /\ pc[self] = "Label_187_9"
                     /\ value' = [value EXCEPT ![self] = AServerIns[pID___A[self]].kvStore[(AServerIns[pID___A[self]].logs[(id[self])].Mcommand.Key)]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_191_5"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_191_5(self) == /\ pc[self] = "Label_191_5"
                     /\ resp___' = [resp___ EXCEPT ![self] = [Msuccess |-> success__[self], Msource |-> AServerIns[pID___A[self]].me, Mdest |-> dest[self], Idx |-> idx[self], LeaderHint |-> AServerIns[pID___A[self]].me, Value |-> value[self]]]
                     /\ net' = [net EXCEPT ![(dest[self])][("ClientRequestResponse")] = Append(net[(dest[self])][("ClientRequestResponse")], resp___'[self])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_193_5"]
                     /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_193_5(self) == /\ pc[self] = "Label_193_5"
                     /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
                     /\ success__' = [success__ EXCEPT ![self] = Head(stack[self]).success__]
                     /\ dest' = [dest EXCEPT ![self] = Head(stack[self]).dest]
                     /\ id' = [id EXCEPT ![self] = Head(stack[self]).id]
                     /\ idx' = [idx EXCEPT ![self] = Head(stack[self]).idx]
                     /\ resp___' = [resp___ EXCEPT ![self] = Head(stack[self]).resp___]
                     /\ value' = [value EXCEPT ![self] = Head(stack[self]).value]
                     /\ __Profile__' = [__Profile__ EXCEPT ![self] = Head(stack[self]).__Profile__]
                     /\ name___' = [name___ EXCEPT ![self] = Head(stack[self]).name___]
                     /\ pID___A' = [pID___A EXCEPT ![self] = Head(stack[self]).pID___A]
                     /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

__AServer_ApplyAndResponseClient(self) == L241(self) \/ Label_187_9(self)
                                             \/ Label_191_5(self)
                                             \/ Label_193_5(self)

L271(self) == /\ pc[self] = "L271"
              /\ hasCommit' = [hasCommit EXCEPT ![self] = FALSE]
              /\ i__' = [i__ EXCEPT ![self] = AServerIns[pID___AS[self]].commitIndex + 1]
              /\ tmpCommitIndex' = [tmpCommitIndex EXCEPT ![self] = i__'[self]]
              /\ pc' = [pc EXCEPT ![self] = "Label_205_5"]
              /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_205_5(self) == /\ pc[self] = "Label_205_5"
                     /\ IF i__[self] <= Len(AServerIns[pID___AS[self]].logs)
                           THEN /\ IF tmpCommitIndex[self] = i__[self]
                                      THEN /\ count' = [count EXCEPT ![self] = 0]
                                           /\ j' = [j EXCEPT ![self] = 1]
                                           /\ hasCommit' = [hasCommit EXCEPT ![self] = FALSE]
                                           /\ pc' = [pc EXCEPT ![self] = "Label_210_13"]
                                      ELSE /\ pc' = [pc EXCEPT ![self] = "Label_224_9"]
                                           /\ UNCHANGED << hasCommit, count, j >>
                                /\ UNCHANGED __call_stack
                           ELSE /\ __call_stack' = [__call_stack EXCEPT ![name___A[self]] = <<hasCommit[self]>> \o __call_stack[name___A[self]]]
                                /\ pc' = [pc EXCEPT ![self] = "L303"]
                                /\ UNCHANGED << hasCommit, count, j >>
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, i__, tmpCommitIndex, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_224_9(self) == /\ pc[self] = "Label_224_9"
                     /\ i__' = [i__ EXCEPT ![self] = i__[self] + 1]
                     /\ pc' = [pc EXCEPT ![self] = "Label_205_5"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_210_13(self) == /\ pc[self] = "Label_210_13"
                      /\ IF (j[self] <= MaxServer /\ ~hasCommit[self])
                            THEN /\ IF AServerIns[pID___AS[self]].matchIndex[(j[self])] >= i__[self]
                                       THEN /\ count' = [count EXCEPT ![self] = count[self] + 1]
                                            /\ IF count'[self] >= QurmMaxServer
                                                  THEN /\ AServerIns' = [AServerIns EXCEPT ![pID___AS[self]].commitIndex = i__[self]]
                                                       /\ tmpCommitIndex' = [tmpCommitIndex EXCEPT ![self] = i__[self]]
                                                       /\ hasCommit' = [hasCommit EXCEPT ![self] = TRUE]
                                                       /\ __call_stack' = [__call_stack EXCEPT ![self] = <<AServerIns'[pID___AS[self]].commitIndex>> \o __call_stack[self]]
                                                       /\ /\ name___' = [name___ EXCEPT ![self] = self]
                                                          /\ pID___A' = [pID___A EXCEPT ![self] = pID___AS[self]]
                                                          /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__AServer_ApplyAndResponseClient",
                                                                                                   pc        |->  "Label_221_17",
                                                                                                   success__ |->  success__[self],
                                                                                                   dest      |->  dest[self],
                                                                                                   id        |->  id[self],
                                                                                                   idx       |->  idx[self],
                                                                                                   resp___   |->  resp___[self],
                                                                                                   value     |->  value[self],
                                                                                                   __Profile__ |->  __Profile__[self],
                                                                                                   name___   |->  name___[self],
                                                                                                   pID___A   |->  pID___A[self] ] >>
                                                                                               \o stack[self]]
                                                       /\ success__' = [success__ EXCEPT ![self] = defaultInitValue]
                                                       /\ dest' = [dest EXCEPT ![self] = defaultInitValue]
                                                       /\ id' = [id EXCEPT ![self] = defaultInitValue]
                                                       /\ idx' = [idx EXCEPT ![self] = defaultInitValue]
                                                       /\ resp___' = [resp___ EXCEPT ![self] = defaultInitValue]
                                                       /\ value' = [value EXCEPT ![self] = defaultInitValue]
                                                       /\ __Profile__' = [__Profile__ EXCEPT ![self] = "__AServer"]
                                                       /\ pc' = [pc EXCEPT ![self] = "L241"]
                                                  ELSE /\ pc' = [pc EXCEPT ![self] = "Label_221_17"]
                                                       /\ UNCHANGED << __call_stack, 
                                                                       AServerIns, 
                                                                       stack, 
                                                                       name___, 
                                                                       pID___A, 
                                                                       success__, 
                                                                       dest, 
                                                                       id, idx, 
                                                                       resp___, 
                                                                       value, 
                                                                       __Profile__, 
                                                                       hasCommit, 
                                                                       tmpCommitIndex >>
                                       ELSE /\ pc' = [pc EXCEPT ![self] = "Label_221_17"]
                                            /\ UNCHANGED << __call_stack, 
                                                            AServerIns, stack, 
                                                            name___, pID___A, 
                                                            success__, dest, 
                                                            id, idx, resp___, 
                                                            value, __Profile__, 
                                                            hasCommit, 
                                                            tmpCommitIndex, 
                                                            count >>
                            ELSE /\ pc' = [pc EXCEPT ![self] = "Label_224_9"]
                                 /\ UNCHANGED << __call_stack, AServerIns, 
                                                 stack, name___, pID___A, 
                                                 success__, dest, id, idx, 
                                                 resp___, value, __Profile__, 
                                                 hasCommit, tmpCommitIndex, 
                                                 count >>
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___A, pID___AS, i__, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_221_17(self) == /\ pc[self] = "Label_221_17"
                      /\ j' = [j EXCEPT ![self] = j[self] + 1]
                      /\ pc' = [pc EXCEPT ![self] = "Label_210_13"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

L303(self) == /\ pc[self] = "L303"
              /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
              /\ hasCommit' = [hasCommit EXCEPT ![self] = Head(stack[self]).hasCommit]
              /\ i__' = [i__ EXCEPT ![self] = Head(stack[self]).i__]
              /\ tmpCommitIndex' = [tmpCommitIndex EXCEPT ![self] = Head(stack[self]).tmpCommitIndex]
              /\ count' = [count EXCEPT ![self] = Head(stack[self]).count]
              /\ j' = [j EXCEPT ![self] = Head(stack[self]).j]
              /\ __Profile___' = [__Profile___ EXCEPT ![self] = Head(stack[self]).__Profile___]
              /\ name___A' = [name___A EXCEPT ![self] = Head(stack[self]).name___A]
              /\ pID___AS' = [pID___AS EXCEPT ![self] = Head(stack[self]).pID___AS]
              /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
              /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_230_5(self) == /\ pc[self] = "Label_230_5"
                     /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
                     /\ hasCommit' = [hasCommit EXCEPT ![self] = Head(stack[self]).hasCommit]
                     /\ i__' = [i__ EXCEPT ![self] = Head(stack[self]).i__]
                     /\ tmpCommitIndex' = [tmpCommitIndex EXCEPT ![self] = Head(stack[self]).tmpCommitIndex]
                     /\ count' = [count EXCEPT ![self] = Head(stack[self]).count]
                     /\ j' = [j EXCEPT ![self] = Head(stack[self]).j]
                     /\ __Profile___' = [__Profile___ EXCEPT ![self] = Head(stack[self]).__Profile___]
                     /\ name___A' = [name___A EXCEPT ![self] = Head(stack[self]).name___A]
                     /\ pID___AS' = [pID___AS EXCEPT ![self] = Head(stack[self]).pID___AS]
                     /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

__AServer_AdvanceCommitIndex(self) == L271(self) \/ Label_205_5(self)
                                         \/ Label_224_9(self)
                                         \/ Label_210_13(self)
                                         \/ Label_221_17(self)
                                         \/ L303(self) \/ Label_230_5(self)

L308(self) == /\ pc[self] = "L308"
              /\ /\ __call_stack' = [__call_stack EXCEPT ![name___AS[self]] = Tail(Tail(__call_stack[name___AS[self]]))]
                 /\ dest' = [dest EXCEPT ![self] = Head(Tail(__call_stack[name___AS[self]]))]
                 /\ req' = [req EXCEPT ![self] = Head(__call_stack[name___AS[self]])]
              /\ net' = [net EXCEPT ![(dest'[self])][("AppendEntries")] = Append(net[(dest'[self])][("AppendEntries")], req'[self])]
              /\ pc' = [pc EXCEPT ![self] = "Label_240_5"]
              /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_240_5(self) == /\ pc[self] = "Label_240_5"
                     /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
                     /\ name___AS' = [name___AS EXCEPT ![self] = Head(stack[self]).name___AS]
                     /\ pID___ASe' = [pID___ASe EXCEPT ![self] = Head(stack[self]).pID___ASe]
                     /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

__AServer_SendAppendEntry(self) == L308(self) \/ Label_240_5(self)

L332(self) == /\ pc[self] = "L332"
              /\ /\ __call_stack' = [__call_stack EXCEPT ![name___ASe[self]] = Tail(__call_stack[name___ASe[self]])]
                 /\ resp___A' = [resp___A EXCEPT ![self] = Head(__call_stack[name___ASe[self]])]
              /\ pc' = [pc EXCEPT ![self] = "AtomCheckTerm__"]
              /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AtomCheckTerm__(self) == /\ pc[self] = "AtomCheckTerm__"
                         /\ IF resp___A[self].Mterm > AServerIns[pID___ASer[self]].currentTerm
                               THEN /\ AServerIns' = [AServerIns EXCEPT ![pID___ASer[self]].currentTerm = resp___A[self].Mterm,
                                                                        ![pID___ASer[self]].state = Follower,
                                                                        ![pID___ASer[self]].mleader = InitValue,
                                                                        ![pID___ASer[self]].mleader = resp___A[self].Msource,
                                                                        ![pID___ASer[self]].votedFor = 0]
                                    /\ pc' = [pc EXCEPT ![self] = "Label_269_5"]
                               ELSE /\ IF resp___A[self].Mterm = AServerIns[pID___ASer[self]].currentTerm
                                          THEN /\ AServerIns' = [AServerIns EXCEPT ![pID___ASer[self]].mleader = resp___A[self].Msource]
                                               /\ IF resp___A[self].Msuccess
                                                     THEN /\ pc' = [pc EXCEPT ![self] = "Label_261_13"]
                                                     ELSE /\ pc' = [pc EXCEPT ![self] = "Label_266_13"]
                                          ELSE /\ pc' = [pc EXCEPT ![self] = "Label_269_5"]
                                               /\ UNCHANGED AServerIns
                         /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_261_13(self) == /\ pc[self] = "Label_261_13"
                      /\ AServerIns' = [AServerIns EXCEPT ![pID___ASer[self]].nextIndex[(resp___A[self].Msource)] = resp___A[self].MmatchIndex + 1,
                                                          ![pID___ASer[self]].matchIndex[(resp___A[self].Msource)] = resp___A[self].MmatchIndex]
                      /\ __call_stack' = [__call_stack EXCEPT ![self] = <<>> \o __call_stack[self]]
                      /\ /\ name___A' = [name___A EXCEPT ![self] = self]
                         /\ pID___AS' = [pID___AS EXCEPT ![self] = pID___ASer[self]]
                         /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__AServer_AdvanceCommitIndex",
                                                                  pc        |->  "Label_269_5",
                                                                  hasCommit |->  hasCommit[self],
                                                                  i__       |->  i__[self],
                                                                  tmpCommitIndex |->  tmpCommitIndex[self],
                                                                  count     |->  count[self],
                                                                  j         |->  j[self],
                                                                  __Profile___ |->  __Profile___[self],
                                                                  name___A  |->  name___A[self],
                                                                  pID___AS  |->  pID___AS[self] ] >>
                                                              \o stack[self]]
                      /\ hasCommit' = [hasCommit EXCEPT ![self] = defaultInitValue]
                      /\ i__' = [i__ EXCEPT ![self] = defaultInitValue]
                      /\ tmpCommitIndex' = [tmpCommitIndex EXCEPT ![self] = defaultInitValue]
                      /\ count' = [count EXCEPT ![self] = defaultInitValue]
                      /\ j' = [j EXCEPT ![self] = defaultInitValue]
                      /\ __Profile___' = [__Profile___ EXCEPT ![self] = "__AServer"]
                      /\ pc' = [pc EXCEPT ![self] = "L271"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_266_13(self) == /\ pc[self] = "Label_266_13"
                      /\ AServerIns' = [AServerIns EXCEPT ![pID___ASer[self]].nextIndex[(resp___A[self].Msource)] = Max(1, AServerIns[pID___ASer[self]].nextIndex[(resp___A[self].Msource)])]
                      /\ pc' = [pc EXCEPT ![self] = "Label_269_5"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_269_5(self) == /\ pc[self] = "Label_269_5"
                     /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
                     /\ resp___A' = [resp___A EXCEPT ![self] = Head(stack[self]).resp___A]
                     /\ __Profile___A' = [__Profile___A EXCEPT ![self] = Head(stack[self]).__Profile___A]
                     /\ name___ASe' = [name___ASe EXCEPT ![self] = Head(stack[self]).name___ASe]
                     /\ pID___ASer' = [pID___ASer EXCEPT ![self] = Head(stack[self]).pID___ASer]
                     /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

__AServer_HandleAppendEntriesResponseFunc(self) == L332(self)
                                                      \/ AtomCheckTerm__(self)
                                                      \/ Label_261_13(self)
                                                      \/ Label_266_13(self)
                                                      \/ Label_269_5(self)

L372(self) == /\ pc[self] = "L372"
              /\ /\ __call_stack' = [__call_stack EXCEPT ![name___ASer[self]] = Tail(__call_stack[name___ASer[self]])]
                 /\ req___' = [req___ EXCEPT ![self] = Head(__call_stack[name___ASer[self]])]
              /\ entry' = [entry EXCEPT ![self] = [__reserved |-> 0]]
              /\ IF AServerIns[pID___AServ[self]].state = Leader
                    THEN /\ pc' = [pc EXCEPT ![self] = "AtomAddLog"]
                         /\ UNCHANGED << net, success, resp >>
                    ELSE /\ success' = [success EXCEPT ![self] = FALSE]
                         /\ resp' = [resp EXCEPT ![self] = [Msuccess |-> success'[self], Msource |-> AServerIns[pID___AServ[self]].me, Mdest |-> req___'[self].Msource, Idx |-> req___'[self].Mcommand.Idx, LeaderHint |-> AServerIns[pID___AServ[self]].mleader]]
                         /\ net' = [net EXCEPT ![((req___'[self].Msource))][("ClientRequestResponse")] = Append(net[((req___'[self].Msource))][("ClientRequestResponse")], resp'[self])]
                         /\ pc' = [pc EXCEPT ![self] = "Label_295_5"]
              /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AtomAddLog(self) == /\ pc[self] = "AtomAddLog"
                    /\ entry' = [entry EXCEPT ![self] = [Mterm |-> AServerIns[pID___AServ[self]].currentTerm, Mcommand |-> req___[self].Mcommand, Client |-> req___[self].Msource]]
                    /\ AServerIns' = [AServerIns EXCEPT ![pID___AServ[self]].logs = Append(AServerIns[pID___AServ[self]].logs, entry'[self])]
                    /\ pc' = [pc EXCEPT ![self] = "Label_285_9"]
                    /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_285_9(self) == /\ pc[self] = "Label_285_9"
                     /\ AServerIns' = [AServerIns EXCEPT ![pID___AServ[self]].matchIndex[(AServerIns[pID___AServ[self]].me)] = Len(AServerIns[pID___AServ[self]].logs) - 1,
                                                         ![pID___AServ[self]].nextIndex[(AServerIns[pID___AServ[self]].me)] = Len(AServerIns[pID___AServ[self]].logs)]
                     /\ pc' = [pc EXCEPT ![self] = "Heartbeat"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Heartbeat(self) == /\ pc[self] = "Heartbeat"
                   /\ __call_stack' = [__call_stack EXCEPT ![self] = <<>> \o __call_stack[self]]
                   /\ /\ name' = [name EXCEPT ![self] = self]
                      /\ pID' = [pID EXCEPT ![self] = pID___AServ[self]]
                      /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__AServer_heartbeat",
                                                               pc        |->  "Label_295_5",
                                                               i         |->  i[self],
                                                               lastEntry |->  lastEntry[self],
                                                               prevLogIndex |->  prevLogIndex[self],
                                                               prevLogTerm |->  prevLogTerm[self],
                                                               entries   |->  entries[self],
                                                               req       |->  req[self],
                                                               __Profile |->  __Profile[self],
                                                               name      |->  name[self],
                                                               pID       |->  pID[self] ] >>
                                                           \o stack[self]]
                   /\ i' = [i EXCEPT ![self] = defaultInitValue]
                   /\ lastEntry' = [lastEntry EXCEPT ![self] = defaultInitValue]
                   /\ prevLogIndex' = [prevLogIndex EXCEPT ![self] = defaultInitValue]
                   /\ prevLogTerm' = [prevLogTerm EXCEPT ![self] = defaultInitValue]
                   /\ entries' = [entries EXCEPT ![self] = defaultInitValue]
                   /\ req' = [req EXCEPT ![self] = defaultInitValue]
                   /\ __Profile' = [__Profile EXCEPT ![self] = "__AServer"]
                   /\ pc' = [pc EXCEPT ![self] = "L401"]
                   /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_295_5(self) == /\ pc[self] = "Label_295_5"
                     /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
                     /\ entry' = [entry EXCEPT ![self] = Head(stack[self]).entry]
                     /\ req___' = [req___ EXCEPT ![self] = Head(stack[self]).req___]
                     /\ success' = [success EXCEPT ![self] = Head(stack[self]).success]
                     /\ resp' = [resp EXCEPT ![self] = Head(stack[self]).resp]
                     /\ __Profile___AS' = [__Profile___AS EXCEPT ![self] = Head(stack[self]).__Profile___AS]
                     /\ name___ASer' = [name___ASer EXCEPT ![self] = Head(stack[self]).name___ASer]
                     /\ pID___AServ' = [pID___AServ EXCEPT ![self] = Head(stack[self]).pID___AServ]
                     /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

__AServer_HandleClientRequestFunc(self) == L372(self) \/ AtomAddLog(self)
                                              \/ Label_285_9(self)
                                              \/ Heartbeat(self)
                                              \/ Label_295_5(self)

L401(self) == /\ pc[self] = "L401"
              /\ IF AServerIns[pID[self]].state = Leader
                    THEN /\ i' = [i EXCEPT ![self] = 1]
                         /\ pc' = [pc EXCEPT ![self] = "AtomCheckTerm"]
                    ELSE /\ pc' = [pc EXCEPT ![self] = "Label_324_5"]
                         /\ i' = i
              /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AtomCheckTerm(self) == /\ pc[self] = "AtomCheckTerm"
                       /\ IF (i[self] <= MaxServer /\ AServerIns[pID[self]].state = Leader)
                             THEN /\ IF i[self] /= AServerIns[pID[self]].me
                                        THEN /\ lastEntry' = [lastEntry EXCEPT ![self] = Len(AServerIns[pID[self]].logs)]
                                             /\ prevLogIndex' = [prevLogIndex EXCEPT ![self] = AServerIns[pID[self]].nextIndex[(i[self])] - 1]
                                             /\ prevLogTerm' = [prevLogTerm EXCEPT ![self] = 0]
                                             /\ entries' = [entries EXCEPT ![self] = SubSeqI(AServerIns[pID[self]].logs, AServerIns[pID[self]].nextIndex[(i[self])], lastEntry'[self] + 1)]
                                             /\ IF prevLogIndex'[self] >= 1
                                                   THEN /\ pc' = [pc EXCEPT ![self] = "Label_314_21"]
                                                   ELSE /\ pc' = [pc EXCEPT ![self] = "Label_316_17"]
                                        ELSE /\ pc' = [pc EXCEPT ![self] = "Label_320_13"]
                                             /\ UNCHANGED << lastEntry, 
                                                             prevLogIndex, 
                                                             prevLogTerm, 
                                                             entries >>
                                  /\ i' = i
                             ELSE /\ i' = [i EXCEPT ![self] = 1]
                                  /\ pc' = [pc EXCEPT ![self] = "Label_324_5"]
                                  /\ UNCHANGED << lastEntry, prevLogIndex, 
                                                  prevLogTerm, entries >>
                       /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_320_13(self) == /\ pc[self] = "Label_320_13"
                      /\ i' = [i EXCEPT ![self] = i[self] + 1]
                      /\ pc' = [pc EXCEPT ![self] = "AtomCheckTerm"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_316_17(self) == /\ pc[self] = "Label_316_17"
                      /\ req' = [req EXCEPT ![self] = [Mterm |-> AServerIns[pID[self]].currentTerm, MprevLogIndex |-> prevLogIndex[self], MprevLogTerm |-> prevLogTerm[self], Mlog |-> entries[self], MleaderCommit |-> Min(AServerIns[pID[self]].commitIndex, lastEntry[self]), Msource |-> AServerIns[pID[self]].me, Mdest |-> i[self]]]
                      /\ __call_stack' = [__call_stack EXCEPT ![self] = <<req'[self], i[self]>> \o __call_stack[self]]
                      /\ /\ name___AS' = [name___AS EXCEPT ![self] = self]
                         /\ pID___ASe' = [pID___ASe EXCEPT ![self] = pID[self]]
                         /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__AServer_SendAppendEntry",
                                                                  pc        |->  "Label_320_13",
                                                                  name___AS |->  name___AS[self],
                                                                  pID___ASe |->  pID___ASe[self] ] >>
                                                              \o stack[self]]
                      /\ pc' = [pc EXCEPT ![self] = "L308"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_314_21(self) == /\ pc[self] = "Label_314_21"
                      /\ prevLogTerm' = [prevLogTerm EXCEPT ![self] = AServerIns[pID[self]].logs[(prevLogIndex[self])].Mterm]
                      /\ pc' = [pc EXCEPT ![self] = "Label_316_17"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_324_5(self) == /\ pc[self] = "Label_324_5"
                     /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
                     /\ i' = [i EXCEPT ![self] = Head(stack[self]).i]
                     /\ lastEntry' = [lastEntry EXCEPT ![self] = Head(stack[self]).lastEntry]
                     /\ prevLogIndex' = [prevLogIndex EXCEPT ![self] = Head(stack[self]).prevLogIndex]
                     /\ prevLogTerm' = [prevLogTerm EXCEPT ![self] = Head(stack[self]).prevLogTerm]
                     /\ entries' = [entries EXCEPT ![self] = Head(stack[self]).entries]
                     /\ req' = [req EXCEPT ![self] = Head(stack[self]).req]
                     /\ __Profile' = [__Profile EXCEPT ![self] = Head(stack[self]).__Profile]
                     /\ name' = [name EXCEPT ![self] = Head(stack[self]).name]
                     /\ pID' = [pID EXCEPT ![self] = Head(stack[self]).pID]
                     /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

__AServer_heartbeat(self) == L401(self) \/ AtomCheckTerm(self)
                                \/ Label_320_13(self) \/ Label_316_17(self)
                                \/ Label_314_21(self) \/ Label_324_5(self)

Label_330_5(self) == /\ pc[self] = "Label_330_5"
                     /\ cmd' = [cmd EXCEPT ![self] = [__reserved |-> 0]]
                     /\ ok' = [ok EXCEPT ![self] = FALSE]
                     /\ nClient' = [nClient EXCEPT ![self] = 0]
                     /\ clientReq' = [clientReq EXCEPT ![self] = 0]
                     /\ pc' = [pc EXCEPT ![self] = "Label_334_5"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_334_5(self) == /\ pc[self] = "Label_334_5"
                     /\ nClient' = [nClient EXCEPT ![self] = clientNum]
                     /\ pc' = [pc EXCEPT ![self] = "Label_335_5"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_335_5(self) == /\ pc[self] = "Label_335_5"
                     /\ Len(reqCh) > 0
                     /\ cmd' = [cmd EXCEPT ![self] = Head(reqCh)]
                     /\ reqCh' = Tail(reqCh)
                     /\ /\ AClientIns' = [AClientIns EXCEPT ![pID_[self]].reqId = AClientIns[pID_[self]].reqId + nClient[self]]
                        /\ clientReq' = [clientReq EXCEPT ![self] = clientReq[self] + 1]
                     /\ clientReqNum' = clientReqNum + 1
                     /\ t1' = [t1 EXCEPT ![self] = Time("now")]
                     /\ pc' = [pc EXCEPT ![self] = "Label_341_9"]
                     /\ UNCHANGED << net, respCh, clientNum, log, serverVoteNum, __call_stack, __path, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, ok, nClient, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_341_9(self) == /\ pc[self] = "Label_341_9"
                     /\ IF ~ok[self]
                           THEN /\ dest_' = [dest_ EXCEPT ![self] = AClientIns[pID_[self]].mleader]
                                /\ cmd' = [cmd EXCEPT ![self].Idx = AClientIns[pID_[self]].reqId]
                                /\ req_' = [req_ EXCEPT ![self] = [Mcommand |-> cmd'[self], Msource |-> AClientIns[pID_[self]].me, Mdest |-> dest_'[self]]]
                                /\ net' = [net EXCEPT ![(dest_'[self])][("ClientRequest")] = Append(net[(dest_'[self])][("ClientRequest")], req_'[self])]
                                /\ resp_' = [resp_ EXCEPT ![self] = [__reserved |-> 0]]
                                /\ pc' = [pc EXCEPT ![self] = "Label_347_13"]
                                /\ ok' = ok
                           ELSE /\ ok' = [ok EXCEPT ![self] = FALSE]
                                /\ pc' = [pc EXCEPT ![self] = "Label_335_5"]
                                /\ UNCHANGED << net, cmd, dest_, req_, resp_ >>
                     /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, nClient, clientReq, t1, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_347_13(self) == /\ pc[self] = "Label_347_13"
                      /\ Len(net[((AClientIns[pID_[self]].me))][("ClientRequestResponse")]) > 0
                      /\ resp_' = [resp_ EXCEPT ![self] = Head(net[((AClientIns[pID_[self]].me))][("ClientRequestResponse")])]
                      /\ net' = [net EXCEPT ![((AClientIns[pID_[self]].me))][("ClientRequestResponse")] = Tail(net[((AClientIns[pID_[self]].me))][("ClientRequestResponse")])]
                      /\ pc' = [pc EXCEPT ![self] = "Label_348_13"]
                      /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_348_13(self) == /\ pc[self] = "Label_348_13"
                      /\ IF resp_[self].Idx /= AClientIns[pID_[self]].reqId
                            THEN /\ Len(net[((AClientIns[pID_[self]].me))][("ClientRequestResponse")]) > 0
                                 /\ resp_' = [resp_ EXCEPT ![self] = Head(net[((AClientIns[pID_[self]].me))][("ClientRequestResponse")])]
                                 /\ net' = [net EXCEPT ![((AClientIns[pID_[self]].me))][("ClientRequestResponse")] = Tail(net[((AClientIns[pID_[self]].me))][("ClientRequestResponse")])]
                                 /\ pc' = [pc EXCEPT ![self] = "Label_348_13"]
                                 /\ UNCHANGED << respCh, AClientIns, ok >>
                            ELSE /\ IF resp_[self].Msuccess
                                       THEN /\ respCh' = Append(respCh, resp_[self])
                                            /\ ok' = [ok EXCEPT ![self] = TRUE]
                                            /\ PrintT((<<"client", AClientIns[pID_[self]].me, "resp success", resp_[self]>>))
                                            /\ UNCHANGED AClientIns
                                       ELSE /\ IF resp_[self].LeaderHint /= InitValue
                                                  THEN /\ AClientIns' = [AClientIns EXCEPT ![pID_[self]].mleader = resp_[self].LeaderHint]
                                                  ELSE /\ TRUE
                                                       /\ UNCHANGED AClientIns
                                            /\ UNCHANGED << respCh, ok >>
                                 /\ pc' = [pc EXCEPT ![self] = "Label_341_9"]
                                 /\ UNCHANGED << net, resp_ >>
                      /\ UNCHANGED << reqCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, nClient, clientReq, t1, dest_, req_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AClientMain(self) == Label_330_5(self) \/ Label_334_5(self)
                        \/ Label_335_5(self) \/ Label_341_9(self)
                        \/ Label_347_13(self) \/ Label_348_13(self)

Label_369_5(self) == /\ pc[self] = "Label_369_5"
                     /\ req_A' = [req_A EXCEPT ![self] = [__reserved |-> 0]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_370_5"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_370_5(self) == /\ pc[self] = "Label_370_5"
                     /\ Len(net[((AServerIns[pID_A[self]].me))][("AppendEntries")]) > 0
                     /\ req_A' = [req_A EXCEPT ![self] = Head(net[((AServerIns[pID_A[self]].me))][("AppendEntries")])]
                     /\ net' = [net EXCEPT ![((AServerIns[pID_A[self]].me))][("AppendEntries")] = Tail(net[((AServerIns[pID_A[self]].me))][("AppendEntries")])]
                     /\ IF (req_A'[self].Mterm = AServerIns[pID_A[self]].currentTerm /\ AServerIns[pID_A[self]].state = Follower)
                           THEN /\ AServerIns' = [AServerIns EXCEPT ![pID_A[self]].mleader = req_A'[self].Msource]
                           ELSE /\ TRUE
                                /\ UNCHANGED AServerIns
                     /\ __call_stack' = [__call_stack EXCEPT ![self] = <<req_A'[self]>> \o __call_stack[self]]
                     /\ /\ name__' = [name__ EXCEPT ![self] = self]
                        /\ pID___' = [pID___ EXCEPT ![self] = pID_A[self]]
                        /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__AServer_HandleAppendEntriesRequestFunc",
                                                                 pc        |->  "Label_370_5",
                                                                 resp__    |->  resp__[self],
                                                                 success_  |->  success_[self],
                                                                 logOk     |->  logOk[self],
                                                                 needReply |->  needReply[self],
                                                                 req__     |->  req__[self],
                                                                 mIndex    |->  mIndex[self],
                                                                 index     |->  index[self],
                                                                 tmpi      |->  tmpi[self],
                                                                 __Profile_ |->  __Profile_[self],
                                                                 name__    |->  name__[self],
                                                                 pID___    |->  pID___[self] ] >>
                                                             \o stack[self]]
                     /\ resp__' = [resp__ EXCEPT ![self] = defaultInitValue]
                     /\ success_' = [success_ EXCEPT ![self] = defaultInitValue]
                     /\ logOk' = [logOk EXCEPT ![self] = defaultInitValue]
                     /\ needReply' = [needReply EXCEPT ![self] = defaultInitValue]
                     /\ req__' = [req__ EXCEPT ![self] = defaultInitValue]
                     /\ mIndex' = [mIndex EXCEPT ![self] = defaultInitValue]
                     /\ index' = [index EXCEPT ![self] = defaultInitValue]
                     /\ tmpi' = [tmpi EXCEPT ![self] = defaultInitValue]
                     /\ __Profile_' = [__Profile_ EXCEPT ![self] = "__AServer"]
                     /\ pc' = [pc EXCEPT ![self] = "L135"]
                     /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, name_, pID__, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AServerHandleAppendEntriesRequest(self) == Label_369_5(self)
                                              \/ Label_370_5(self)

Label_384_5(self) == /\ pc[self] = "Label_384_5"
                     /\ resp_A' = [resp_A EXCEPT ![self] = [__reserved |-> 0]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_385_5"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_385_5(self) == /\ pc[self] = "Label_385_5"
                     /\ Len(net[((AServerIns[pID_AS[self]].me))][("AppendEntriesResponse")]) > 0
                     /\ resp_A' = [resp_A EXCEPT ![self] = Head(net[((AServerIns[pID_AS[self]].me))][("AppendEntriesResponse")])]
                     /\ net' = [net EXCEPT ![((AServerIns[pID_AS[self]].me))][("AppendEntriesResponse")] = Tail(net[((AServerIns[pID_AS[self]].me))][("AppendEntriesResponse")])]
                     /\ __call_stack' = [__call_stack EXCEPT ![self] = <<resp_A'[self]>> \o __call_stack[self]]
                     /\ /\ name___ASe' = [name___ASe EXCEPT ![self] = self]
                        /\ pID___ASer' = [pID___ASer EXCEPT ![self] = pID_AS[self]]
                        /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__AServer_HandleAppendEntriesResponseFunc",
                                                                 pc        |->  "Label_385_5",
                                                                 resp___A  |->  resp___A[self],
                                                                 __Profile___A |->  __Profile___A[self],
                                                                 name___ASe |->  name___ASe[self],
                                                                 pID___ASer |->  pID___ASer[self] ] >>
                                                             \o stack[self]]
                     /\ resp___A' = [resp___A EXCEPT ![self] = defaultInitValue]
                     /\ __Profile___A' = [__Profile___A EXCEPT ![self] = "__AServer"]
                     /\ pc' = [pc EXCEPT ![self] = "L332"]
                     /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AServerHandleAppendEntriesResponse(self) == Label_384_5(self)
                                               \/ Label_385_5(self)

Label_396_5(self) == /\ pc[self] = "Label_396_5"
                     /\ req_AS' = [req_AS EXCEPT ![self] = [__reserved |-> 0]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_397_5"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_397_5(self) == /\ pc[self] = "Label_397_5"
                     /\ Len(net[((AServerIns[pID_ASe[self]].me))][("ClientRequest")]) > 0
                     /\ req_AS' = [req_AS EXCEPT ![self] = Head(net[((AServerIns[pID_ASe[self]].me))][("ClientRequest")])]
                     /\ net' = [net EXCEPT ![((AServerIns[pID_ASe[self]].me))][("ClientRequest")] = Tail(net[((AServerIns[pID_ASe[self]].me))][("ClientRequest")])]
                     /\ __call_stack' = [__call_stack EXCEPT ![self] = <<req_AS'[self]>> \o __call_stack[self]]
                     /\ /\ name___ASer' = [name___ASer EXCEPT ![self] = self]
                        /\ pID___AServ' = [pID___AServ EXCEPT ![self] = pID_ASe[self]]
                        /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__AServer_HandleClientRequestFunc",
                                                                 pc        |->  "Label_397_5",
                                                                 entry     |->  entry[self],
                                                                 req___    |->  req___[self],
                                                                 success   |->  success[self],
                                                                 resp      |->  resp[self],
                                                                 __Profile___AS |->  __Profile___AS[self],
                                                                 name___ASer |->  name___ASer[self],
                                                                 pID___AServ |->  pID___AServ[self] ] >>
                                                             \o stack[self]]
                     /\ entry' = [entry EXCEPT ![self] = defaultInitValue]
                     /\ req___' = [req___ EXCEPT ![self] = defaultInitValue]
                     /\ success' = [success EXCEPT ![self] = defaultInitValue]
                     /\ resp' = [resp EXCEPT ![self] = defaultInitValue]
                     /\ __Profile___AS' = [__Profile___AS EXCEPT ![self] = "__AServer"]
                     /\ pc' = [pc EXCEPT ![self] = "L372"]
                     /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AServerHandleClientRequest(self) == Label_396_5(self) \/ Label_397_5(self)

Label_408_5(self) == /\ pc[self] = "Label_408_5"
                     /\ i_' = [i_ EXCEPT ![self] = 1]
                     /\ needVotes' = [needVotes EXCEPT ![self] = TRUE]
                     /\ election' = [election EXCEPT ![self] = FALSE]
                     /\ req_ASe' = [req_ASe EXCEPT ![self] = [__reserved |-> 0]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_412_5"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_412_5(self) == /\ pc[self] = "Label_412_5"
                     /\ serverVoteNum' = serverVoteNum + 1
                     /\ pc' = [pc EXCEPT ![self] = "AtomCheck_"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AtomCheck_(self) == /\ pc[self] = "AtomCheck_"
                    /\ IF AServerIns[pID_ASer[self]].state /= Leader
                          THEN /\ /\ AServerIns' = [AServerIns EXCEPT ![pID_ASer[self]].state = Candidate,
                                                                      ![pID_ASer[self]].votedFor = AServerIns[pID_ASer[self]].me,
                                                                      ![pID_ASer[self]].votesResponded = NewSet(AServerIns[pID_ASer[self]].me),
                                                                      ![pID_ASer[self]].votesGranted = NewSet(AServerIns[pID_ASer[self]].me),
                                                                      ![pID_ASer[self]].currentTerm = AServerIns[pID_ASer[self]].currentTerm + 1,
                                                                      ![pID_ASer[self]].mleader = InitValue]
                                  /\ needVotes' = [needVotes EXCEPT ![self] = TRUE]
                               /\ req_ASe' = [req_ASe EXCEPT ![self] = [Mterm |-> AServerIns'[pID_ASer[self]].currentTerm, MlastLogTerm |-> 0, MlastLogIndex |-> 0, Msource |-> AServerIns'[pID_ASer[self]].me, Mdest |-> 0]]
                          ELSE /\ TRUE
                               /\ UNCHANGED << AServerIns, needVotes, req_ASe >>
                    /\ pc' = [pc EXCEPT ![self] = "CheckandVotes_"]
                    /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, election, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

CheckandVotes_(self) == /\ pc[self] = "CheckandVotes_"
                        /\ IF needVotes[self]
                              THEN /\ needVotes' = [needVotes EXCEPT ![self] = FALSE]
                                   /\ pc' = [pc EXCEPT ![self] = "Label_428_13"]
                              ELSE /\ pc' = [pc EXCEPT ![self] = "Label_412_5"]
                                   /\ UNCHANGED needVotes
                        /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_428_13(self) == /\ pc[self] = "Label_428_13"
                      /\ IF i_[self] <= MaxServer
                            THEN /\ IF i_[self] /= AServerIns[pID_ASer[self]].me
                                       THEN /\ __call_stack' = [__call_stack EXCEPT ![self] = <<req_ASe[self], i_[self]>> \o __call_stack[self]]
                                            /\ /\ name_' = [name_ EXCEPT ![self] = self]
                                               /\ pID__' = [pID__ EXCEPT ![self] = pID_ASer[self]]
                                               /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__AServer_SendRequestVote",
                                                                                        pc        |->  "Label_433_17",
                                                                                        name_     |->  name_[self],
                                                                                        pID__     |->  pID__[self] ] >>
                                                                                    \o stack[self]]
                                            /\ pc' = [pc EXCEPT ![self] = "L125"]
                                       ELSE /\ pc' = [pc EXCEPT ![self] = "Label_433_17"]
                                            /\ UNCHANGED << __call_stack, 
                                                            stack, name_, 
                                                            pID__ >>
                                 /\ i_' = i_
                            ELSE /\ i_' = [i_ EXCEPT ![self] = 1]
                                 /\ pc' = [pc EXCEPT ![self] = "Label_412_5"]
                                 /\ UNCHANGED << __call_stack, stack, name_, 
                                                 pID__ >>
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __path, AClientIns, AServerIns, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_433_17(self) == /\ pc[self] = "Label_433_17"
                      /\ i_' = [i_ EXCEPT ![self] = i_[self] + 1]
                      /\ pc' = [pc EXCEPT ![self] = "Label_428_13"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AServerRequestVote(self) == Label_408_5(self) \/ Label_412_5(self)
                               \/ AtomCheck_(self) \/ CheckandVotes_(self)
                               \/ Label_428_13(self) \/ Label_433_17(self)

Label_444_5(self) == /\ pc[self] = "Label_444_5"
                     /\ req_ASer' = [req_ASer EXCEPT ![self] = [__reserved |-> 0]]
                     /\ resp_AS' = [resp_AS EXCEPT ![self] = [__reserved |-> 0]]
                     /\ grant' = [grant EXCEPT ![self] = FALSE]
                     /\ needResp' = [needResp EXCEPT ![self] = FALSE]
                     /\ pc' = [pc EXCEPT ![self] = "Label_448_5"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_448_5(self) == /\ pc[self] = "Label_448_5"
                     /\ Len(net[((AServerIns[pID_AServ[self]].me))][("RequestVote")]) > 0
                     /\ req_ASer' = [req_ASer EXCEPT ![self] = Head(net[((AServerIns[pID_AServ[self]].me))][("RequestVote")])]
                     /\ net' = [net EXCEPT ![((AServerIns[pID_AServ[self]].me))][("RequestVote")] = Tail(net[((AServerIns[pID_AServ[self]].me))][("RequestVote")])]
                     /\ pc' = [pc EXCEPT ![self] = "AtomHandle"]
                     /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AtomHandle(self) == /\ pc[self] = "AtomHandle"
                    /\ IF req_ASer[self].Mterm > AServerIns[pID_AServ[self]].currentTerm
                          THEN /\ AServerIns' = [AServerIns EXCEPT ![pID_AServ[self]].currentTerm = req_ASer[self].Mterm,
                                                                   ![pID_AServ[self]].state = Follower,
                                                                   ![pID_AServ[self]].mleader = InitValue,
                                                                   ![pID_AServ[self]].votedFor = 0]
                          ELSE /\ TRUE
                               /\ UNCHANGED AServerIns
                    /\ IF req_ASer[self].Mterm = AServerIns'[pID_AServ[self]].currentTerm
                          THEN /\ grant' = [grant EXCEPT ![self] = (req_ASer[self].Mterm <= AServerIns'[pID_AServ[self]].currentTerm /\ (AServerIns'[pID_AServ[self]].votedFor = 0 \/ AServerIns'[pID_AServ[self]].votedFor = req_ASer[self].Msource))]
                               /\ resp_AS' = [resp_AS EXCEPT ![self] = [Mterm |-> AServerIns'[pID_AServ[self]].currentTerm, Msource |-> AServerIns'[pID_AServ[self]].me, Mgrant |-> grant'[self]]]
                               /\ needResp' = [needResp EXCEPT ![self] = TRUE]
                          ELSE /\ TRUE
                               /\ UNCHANGED << resp_AS, grant, needResp >>
                    /\ pc' = [pc EXCEPT ![self] = "EndAtomHandle"]
                    /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

EndAtomHandle(self) == /\ pc[self] = "EndAtomHandle"
                       /\ IF needResp[self]
                             THEN /\ needResp' = [needResp EXCEPT ![self] = FALSE]
                                  /\ net' = [net EXCEPT ![((req_ASer[self].Msource))][("RequestVoteResponse")] = Append(net[((req_ASer[self].Msource))][("RequestVoteResponse")], resp_AS[self])]
                             ELSE /\ TRUE
                                  /\ UNCHANGED << net, needResp >>
                       /\ pc' = [pc EXCEPT ![self] = "Label_448_5"]
                       /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AServerHandleRequestVoteRequest(self) == Label_444_5(self)
                                            \/ Label_448_5(self)
                                            \/ AtomHandle(self)
                                            \/ EndAtomHandle(self)

Label_474_5(self) == /\ pc[self] = "Label_474_5"
                     /\ resp_ASe' = [resp_ASe EXCEPT ![self] = [__reserved |-> 0]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_475_5"]
                     /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, AServerIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, i_A, pMap, pID_AServe >>

Label_475_5(self) == /\ pc[self] = "Label_475_5"
                     /\ Len(net[((AServerIns[pID_AServe[self]].me))][("RequestVoteResponse")]) > 0
                     /\ resp_ASe' = [resp_ASe EXCEPT ![self] = Head(net[((AServerIns[pID_AServe[self]].me))][("RequestVoteResponse")])]
                     /\ net' = [net EXCEPT ![((AServerIns[pID_AServe[self]].me))][("RequestVoteResponse")] = Tail(net[((AServerIns[pID_AServe[self]].me))][("RequestVoteResponse")])]
                     /\ IF resp_ASe'[self].Mterm > AServerIns[pID_AServe[self]].currentTerm
                           THEN /\ AServerIns' = [AServerIns EXCEPT ![pID_AServe[self]].currentTerm = resp_ASe'[self].Mterm,
                                                                    ![pID_AServe[self]].state = Follower,
                                                                    ![pID_AServe[self]].votedFor = 0,
                                                                    ![pID_AServe[self]].mleader = InitValue]
                           ELSE /\ TRUE
                                /\ UNCHANGED AServerIns
                     /\ IF (resp_ASe'[self].Mterm = AServerIns'[pID_AServe[self]].currentTerm /\ AServerIns'[pID_AServe[self]].state = Candidate)
                           THEN /\ IF (resp_ASe'[self].Mgrant /\ ~Contains(AServerIns'[pID_AServe[self]].votesGranted, resp_ASe'[self].Msource))
                                      THEN /\ pc' = [pc EXCEPT ![self] = "Label_485_17"]
                                      ELSE /\ pc' = [pc EXCEPT ![self] = "Label_487_13"]
                           ELSE /\ pc' = [pc EXCEPT ![self] = "Label_475_5"]
                     /\ UNCHANGED << reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, i_A, pMap, pID_AServe >>

Label_487_13(self) == /\ pc[self] = "Label_487_13"
                      /\ IF ~Contains(AServerIns[pID_AServe[self]].votesResponded, resp_ASe[self].Msource)
                            THEN /\ AServerIns' = [AServerIns EXCEPT ![pID_AServe[self]].votesResponded = Add(AServerIns[pID_AServe[self]].votesResponded, resp_ASe[self].Msource)]
                            ELSE /\ TRUE
                                 /\ UNCHANGED AServerIns
                      /\ pc' = [pc EXCEPT ![self] = "AtomCheck"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AtomCheck(self) == /\ pc[self] = "AtomCheck"
                   /\ IF (Cardinality(AServerIns[pID_AServe[self]].votesGranted) >= QurmMaxServer /\ AServerIns[pID_AServe[self]].state = Candidate /\ AServerIns[pID_AServe[self]].currentTerm = resp_ASe[self].Mterm)
                         THEN /\ AServerIns' = [AServerIns EXCEPT ![pID_AServe[self]].state = Leader,
                                                                  ![pID_AServe[self]].mleader = AServerIns[pID_AServe[self]].me,
                                                                  ![pID_AServe[self]].nextIndex = NewMap(MaxServer, 1),
                                                                  ![pID_AServe[self]].matchIndex = NewMap(MaxServer, 0)]
                              /\ i_A' = [i_A EXCEPT ![self] = 1]
                              /\ pc' = [pc EXCEPT ![self] = "Label_497_17"]
                         ELSE /\ pc' = [pc EXCEPT ![self] = "CheckandVotes"]
                              /\ UNCHANGED << AServerIns, i_A >>
                   /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, pMap, pID_AServe >>

Label_497_17(self) == /\ pc[self] = "Label_497_17"
                      /\ IF i_A[self] <= MaxServer
                            THEN /\ IF i_A[self] /= AServerIns[pID_AServe[self]].me
                                       THEN /\ AServerIns' = [AServerIns EXCEPT ![pID_AServe[self]].nextIndex[(i_A[self])] = Len(AServerIns[pID_AServe[self]].logs) + 1,
                                                                                ![pID_AServe[self]].matchIndex[(i_A[self])] = 0]
                                       ELSE /\ AServerIns' = [AServerIns EXCEPT ![pID_AServe[self]].nextIndex[(i_A[self])] = Len(AServerIns[pID_AServe[self]].logs) + 1,
                                                                                ![pID_AServe[self]].matchIndex[(i_A[self])] = Len(AServerIns[pID_AServe[self]].logs)]
                                 /\ i_A' = [i_A EXCEPT ![self] = i_A[self] + 1]
                                 /\ pc' = [pc EXCEPT ![self] = "Label_497_17"]
                            ELSE /\ pc' = [pc EXCEPT ![self] = "CheckandVotes"]
                                 /\ UNCHANGED << AServerIns, i_A >>
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, pMap, pID_AServe >>

CheckandVotes(self) == /\ pc[self] = "CheckandVotes"
                       /\ IF Cardinality(AServerIns[pID_AServe[self]].votesResponded) - Cardinality(AServerIns[pID_AServe[self]].votesGranted) >= QurmMaxServer
                             THEN /\ AServerIns' = [AServerIns EXCEPT ![pID_AServe[self]].state = Follower]
                                  /\ pc' = [pc EXCEPT ![self] = "Label_511_17"]
                             ELSE /\ pc' = [pc EXCEPT ![self] = "Label_475_5"]
                                  /\ UNCHANGED AServerIns
                       /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_511_17(self) == /\ pc[self] = "Label_511_17"
                      /\ AServerIns' = [AServerIns EXCEPT ![pID_AServe[self]].votedFor = 0]
                      /\ pc' = [pc EXCEPT ![self] = "Label_512_17"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_512_17(self) == /\ pc[self] = "Label_512_17"
                      /\ AServerIns' = [AServerIns EXCEPT ![pID_AServe[self]].mleader = InitValue]
                      /\ pc' = [pc EXCEPT ![self] = "Label_475_5"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

Label_485_17(self) == /\ pc[self] = "Label_485_17"
                      /\ AServerIns' = [AServerIns EXCEPT ![pID_AServe[self]].votesGranted = Add(AServerIns[pID_AServe[self]].votesGranted, resp_ASe[self].Msource)]
                      /\ pc' = [pc EXCEPT ![self] = "Label_487_13"]
                      /\ UNCHANGED << net, reqCh, respCh, clientNum, log, clientReqNum, serverVoteNum, __call_stack, __path, AClientIns, stack, name_, pID__, name__, pID___, resp__, success_, logOk, needReply, req__, mIndex, index, tmpi, __Profile_, name___, pID___A, success__, dest, id, idx, resp___, value, __Profile__, name___A, pID___AS, hasCommit, i__, tmpCommitIndex, count, j, __Profile___, name___AS, pID___ASe, name___ASe, pID___ASer, resp___A, __Profile___A, name___ASer, pID___AServ, entry, req___, success, resp, __Profile___AS, name, pID, i, lastEntry, prevLogIndex, prevLogTerm, entries, req, __Profile, cmd, ok, nClient, clientReq, t1, dest_, req_, resp_, pMap_, pID_, req_A, pMap_A, pID_A, resp_A, pMap_AS, pID_AS, req_AS, pMap_ASe, pID_ASe, i_, needVotes, election, req_ASe, pMap_ASer, pID_ASer, req_ASer, resp_AS, grant, needResp, pMap_AServ, pID_AServ, resp_ASe, i_A, pMap, pID_AServe >>

AServerHandleRequestVoteResponse(self) == Label_474_5(self)
                                             \/ Label_475_5(self)
                                             \/ Label_487_13(self)
                                             \/ AtomCheck(self)
                                             \/ Label_497_17(self)
                                             \/ CheckandVotes(self)
                                             \/ Label_511_17(self)
                                             \/ Label_512_17(self)
                                             \/ Label_485_17(self)

(* Allow infinite stuttering to prevent deadlock on termination. *)
Terminating == /\ \A self \in ProcSet: pc[self] = "Done"
               /\ UNCHANGED vars

Next == (\E self \in ProcSet:  \/ __AServer_SendRequestVote(self)
                               \/ __AServer_HandleAppendEntriesRequestFunc(self)
                               \/ __AServer_ApplyAndResponseClient(self)
                               \/ __AServer_AdvanceCommitIndex(self)
                               \/ __AServer_SendAppendEntry(self)
                               \/ __AServer_HandleAppendEntriesResponseFunc(self)
                               \/ __AServer_HandleClientRequestFunc(self)
                               \/ __AServer_heartbeat(self))
           \/ (\E self \in {"4Main"}: AClientMain(self))
           \/ (\E self \in {"1HandleAppendEntriesRequest", "2HandleAppendEntriesRequest"}: AServerHandleAppendEntriesRequest(self))
           \/ (\E self \in {"1HandleAppendEntriesResponse", "2HandleAppendEntriesResponse"}: AServerHandleAppendEntriesResponse(self))
           \/ (\E self \in {"1HandleClientRequest", "2HandleClientRequest"}: AServerHandleClientRequest(self))
           \/ (\E self \in {"1RequestVote", "2RequestVote"}: AServerRequestVote(self))
           \/ (\E self \in {"1HandleRequestVoteRequest", "2HandleRequestVoteRequest"}: AServerHandleRequestVoteRequest(self))
           \/ (\E self \in {"1HandleRequestVoteResponse", "2HandleRequestVoteResponse"}: AServerHandleRequestVoteResponse(self))
           \/ Terminating

Spec == Init /\ [][Next]_vars

Termination == <>(\A self \in ProcSet: pc[self] = "Done")

\* END TRANSLATION 
=============================================================================
