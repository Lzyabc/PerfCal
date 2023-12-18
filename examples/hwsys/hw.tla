------------------------------- MODULE hw -------------------------------
EXTENDS Integers, TLC, Sequences
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

SERVER == 2

(*--algorithm hw
variables
    net = [ins \in {1, 2} |-> [chan \in {"req", "resp"} |-> <<>>]];
    instream = <<"hw1">>;
    stdPath = <<"answer1">>;
    out = <<>>;
    fileSystem = [hw1 |-> [Name |-> "Xiaoming", Answers |-> <<"A", "B">>], answer1 |-> [Answers |-> <<"A", "B">>]];
    json = TRUE;
    __call_stack = [p \in {"2Main", "1Main"} |-> <<>>];
    __path = 0;
    AServerIns = [r \in {2} |-> [kvStore |-> NewStore,kvFlag |-> NewStore]];

macro net_read (msg, id, channel) begin
    await Len(net[(id)][(channel)]) > 0;
    msg := Head(net[(id)][(channel)]);
    net[(id)][(channel)] := Tail(net[(id)][(channel)]);
end macro;
macro net_write (msg, id, channel) begin
    net[(id)][(channel)] := Append(net[(id)][(channel)], msg);
end macro;
macro instream_read (msg) begin
    await Len(instream) > 0;
    msg := Head(instream);
    instream := Tail(instream);
end macro;
macro stdPath_read (msg) begin
    await Len(stdPath) > 0;
    msg := Head(stdPath);
    stdPath := Tail(stdPath);
end macro;
macro fileSystem_read (msg, path) begin
    msg := fileSystem[(path)];
end macro;
macro out_write (msg) begin
    out := Append(out, msg);
end macro;
macro json_read (res, action, input, res) begin
    res := input;
end macro;

procedure __AServer_saveFS(name, pID)
variables
clientID;requestID;value;flag;
__Profile = "__AServer";
begin
    L56:
    clientID := Head(__call_stack[name]) ||
    requestID := Head(Tail(__call_stack[name])) ||
    value := Head(Tail(Tail(__call_stack[name]))) ||
    __call_stack[name] := Tail(Tail(Tail(__call_stack[name])));
    AtomSave:
    flag := StoreGet(AServerIns[pID].kvFlag, clientID);
    if flag < requestID then
        AServerIns[pID].kvStore := StoreSet(AServerIns[pID].kvStore, clientID, value);
        Label_72_9: AServerIns[pID].kvFlag := StoreSet(AServerIns[pID].kvFlag, clientID, requestID);
    end if;
    Label_74_5: return;
end procedure;

procedure __AServer_computeScore(name, pID)
variables
studentResponse;stdAnswer;responseID;requestID;uName;feedBack;res;score;i;
__Profile = "__AServer";
begin
    L71:
    studentResponse := Head(__call_stack[name]) ||
    stdAnswer := Head(Tail(__call_stack[name])) ||
    responseID := Head(Tail(Tail(__call_stack[name]))) ||
    requestID := Head(Tail(Tail(Tail(__call_stack[name])))) ||
    uName := Head(Tail(Tail(Tail(Tail(__call_stack[name]))))) ||
    __call_stack[name] := Tail(Tail(Tail(Tail(Tail(__call_stack[name])))));
    feedBack := [Answers |-> <<>>, Score |-> 0];
    res := "";
    score := 0;
    if Len(stdAnswer.Answers) = Len(studentResponse.Answers) then
        i := 1;
        Label_94_9: while i <= Len(stdAnswer.Answers) do
            if stdAnswer.Answers[(i)] /= studentResponse.Answers[(i)] then
                feedBack.Answers := Append(feedBack.Answers, "False");
                score := score + 1;
            else
                feedBack.Answers := Append(feedBack.Answers, "True");
            end if;
            i := i + 1;
        end while;
    end if;
    Label_104_5: feedBack.Score := score;
    json_read(res, "dump", feedBack, res);
    __call_stack[self] := <<uName, requestID, score>> \o __call_stack[self];
    call __AServer_saveFS(self, pID);
    resp:
    net_write(res, responseID, "resp");
    return;
end procedure;
process AClientMain \in {"1Main"}
variables
    id, path, submit, hwID, res, reqMsg, pMap=[1Main |-> 1], pID=pMap[self];
begin
    Label_116_5: id := pID;
    path := "";
    submit := "";
    hwID := "";
    c:
    while TRUE do
        submit := "";
        res := "";
        instream_read(path);
        stdPath_read(hwID);
        Label_126_9: fileSystem_read(submit, path);
        reqMsg := [Name |-> submit.Name, Request_id |-> id, Client_id |-> id, Path |-> hwID, Content |-> [Answers |-> submit.Answers]];
        net_write(reqMsg, SERVER, "req");
        Label_129_9: net_read(res, id, "resp");
        out_write(res);
        print(<<"client", id, "received resp:", res>>);
    end while;
end process;

process AServerMain \in {"2Main"}
variables
    id, answer, req, studentResponse, stdAnswer, pMap=[2Main |-> 2], pID=pMap[self];
begin
    Label_139_5: id := pID;
    answer := "";
    req := [__reserved |-> 0];
    studentResponse := [__reserved |-> 0];
    stdAnswer := [__reserved |-> 0];
    Label_144_5: while TRUE do
        net_read(req, id, "req");
        json_read(studentResponse, "load", req.Content, studentResponse);
        fileSystem_read(answer, req.Path);
        json_read(stdAnswer, "load", answer, stdAnswer);
        computeScore:
        __call_stack[self] := <<studentResponse, stdAnswer, req.Client_id, req.Request_id, req.Name>> \o __call_stack[self];
        call __AServer_computeScore(self, pID);
    end while;
end process;
end algorithm;*)
\* BEGIN TRANSLATION (chksum(pcal) = "a6d9962b" /\ chksum(tla) = "5c61b3f")
\* Process variable id of process AClientMain at line 114 col 5 changed to id_
\* Process variable res of process AClientMain at line 114 col 29 changed to res_
\* Process variable pMap of process AClientMain at line 114 col 42 changed to pMap_
\* Process variable pID of process AClientMain at line 114 col 62 changed to pID_
\* Process variable studentResponse of process AServerMain at line 137 col 22 changed to studentResponse_
\* Process variable stdAnswer of process AServerMain at line 137 col 39 changed to stdAnswer_
\* Process variable pID of process AServerMain at line 137 col 70 changed to pID_A
\* Procedure variable requestID of procedure __AServer_saveFS at line 60 col 10 changed to requestID_
\* Procedure variable __Profile of procedure __AServer_saveFS at line 61 col 1 changed to __Profile_
\* Parameter name of procedure __AServer_saveFS at line 58 col 28 changed to name_
\* Parameter pID of procedure __AServer_saveFS at line 58 col 34 changed to pID__
CONSTANT defaultInitValue
VARIABLES net, instream, stdPath, out, fileSystem, json, __call_stack, __path, 
          AServerIns, pc, stack, name_, pID__, clientID, requestID_, value, 
          flag, __Profile_, name, pID, studentResponse, stdAnswer, responseID, 
          requestID, uName, feedBack, res, score, i, __Profile, id_, path, 
          submit, hwID, res_, reqMsg, pMap_, pID_, id, answer, req, 
          studentResponse_, stdAnswer_, pMap, pID_A

vars == << net, instream, stdPath, out, fileSystem, json, __call_stack, 
           __path, AServerIns, pc, stack, name_, pID__, clientID, requestID_, 
           value, flag, __Profile_, name, pID, studentResponse, stdAnswer, 
           responseID, requestID, uName, feedBack, res, score, i, __Profile, 
           id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, id, answer, 
           req, studentResponse_, stdAnswer_, pMap, pID_A >>

ProcSet == ({"1Main"}) \cup ({"2Main"})

Init == (* Global variables *)
        /\ net = [ins \in {1, 2} |-> [chan \in {"req", "resp"} |-> <<>>]]
        /\ instream = <<"hw1">>
        /\ stdPath = <<"answer1">>
        /\ out = <<>>
        /\ fileSystem = [hw1 |-> [Name |-> "Xiaoming", Answers |-> <<"A", "B">>], answer1 |-> [Answers |-> <<"A", "B">>]]
        /\ json = TRUE
        /\ __call_stack = [p \in {"2Main", "1Main"} |-> <<>>]
        /\ __path = 0
        /\ AServerIns = [r \in {2} |-> [kvStore |-> NewStore,kvFlag |-> NewStore]]
        (* Procedure __AServer_saveFS *)
        /\ name_ = [ self \in ProcSet |-> defaultInitValue]
        /\ pID__ = [ self \in ProcSet |-> defaultInitValue]
        /\ clientID = [ self \in ProcSet |-> defaultInitValue]
        /\ requestID_ = [ self \in ProcSet |-> defaultInitValue]
        /\ value = [ self \in ProcSet |-> defaultInitValue]
        /\ flag = [ self \in ProcSet |-> defaultInitValue]
        /\ __Profile_ = [ self \in ProcSet |-> "__AServer"]
        (* Procedure __AServer_computeScore *)
        /\ name = [ self \in ProcSet |-> defaultInitValue]
        /\ pID = [ self \in ProcSet |-> defaultInitValue]
        /\ studentResponse = [ self \in ProcSet |-> defaultInitValue]
        /\ stdAnswer = [ self \in ProcSet |-> defaultInitValue]
        /\ responseID = [ self \in ProcSet |-> defaultInitValue]
        /\ requestID = [ self \in ProcSet |-> defaultInitValue]
        /\ uName = [ self \in ProcSet |-> defaultInitValue]
        /\ feedBack = [ self \in ProcSet |-> defaultInitValue]
        /\ res = [ self \in ProcSet |-> defaultInitValue]
        /\ score = [ self \in ProcSet |-> defaultInitValue]
        /\ i = [ self \in ProcSet |-> defaultInitValue]
        /\ __Profile = [ self \in ProcSet |-> "__AServer"]
        (* Process AClientMain *)
        /\ id_ = [self \in {"1Main"} |-> defaultInitValue]
        /\ path = [self \in {"1Main"} |-> defaultInitValue]
        /\ submit = [self \in {"1Main"} |-> defaultInitValue]
        /\ hwID = [self \in {"1Main"} |-> defaultInitValue]
        /\ res_ = [self \in {"1Main"} |-> defaultInitValue]
        /\ reqMsg = [self \in {"1Main"} |-> defaultInitValue]
        /\ pMap_ = [self \in {"1Main"} |-> [1Main |-> 1]]
        /\ pID_ = [self \in {"1Main"} |-> pMap_[self][self]]
        (* Process AServerMain *)
        /\ id = [self \in {"2Main"} |-> defaultInitValue]
        /\ answer = [self \in {"2Main"} |-> defaultInitValue]
        /\ req = [self \in {"2Main"} |-> defaultInitValue]
        /\ studentResponse_ = [self \in {"2Main"} |-> defaultInitValue]
        /\ stdAnswer_ = [self \in {"2Main"} |-> defaultInitValue]
        /\ pMap = [self \in {"2Main"} |-> [2Main |-> 2]]
        /\ pID_A = [self \in {"2Main"} |-> pMap[self][self]]
        /\ stack = [self \in ProcSet |-> << >>]
        /\ pc = [self \in ProcSet |-> CASE self \in {"1Main"} -> "Label_116_5"
                                        [] self \in {"2Main"} -> "Label_139_5"]

L56(self) == /\ pc[self] = "L56"
             /\ /\ __call_stack' = [__call_stack EXCEPT ![name_[self]] = Tail(Tail(Tail(__call_stack[name_[self]])))]
                /\ clientID' = [clientID EXCEPT ![self] = Head(__call_stack[name_[self]])]
                /\ requestID_' = [requestID_ EXCEPT ![self] = Head(Tail(__call_stack[name_[self]]))]
                /\ value' = [value EXCEPT ![self] = Head(Tail(Tail(__call_stack[name_[self]])))]
             /\ pc' = [pc EXCEPT ![self] = "AtomSave"]
             /\ UNCHANGED << net, instream, stdPath, out, fileSystem, json, __path, AServerIns, stack, name_, pID__, flag, __Profile_, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, feedBack, res, score, i, __Profile, id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

AtomSave(self) == /\ pc[self] = "AtomSave"
                  /\ flag' = [flag EXCEPT ![self] = StoreGet(AServerIns[pID__[self]].kvFlag, clientID[self])]
                  /\ IF flag'[self] < requestID_[self]
                        THEN /\ AServerIns' = [AServerIns EXCEPT ![pID__[self]].kvStore = StoreSet(AServerIns[pID__[self]].kvStore, clientID[self], value[self])]
                             /\ pc' = [pc EXCEPT ![self] = "Label_72_9"]
                        ELSE /\ pc' = [pc EXCEPT ![self] = "Label_74_5"]
                             /\ UNCHANGED AServerIns
                  /\ UNCHANGED << net, instream, stdPath, out, fileSystem, json, __call_stack, __path, stack, name_, pID__, clientID, requestID_, value, __Profile_, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, feedBack, res, score, i, __Profile, id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

Label_72_9(self) == /\ pc[self] = "Label_72_9"
                    /\ AServerIns' = [AServerIns EXCEPT ![pID__[self]].kvFlag = StoreSet(AServerIns[pID__[self]].kvFlag, clientID[self], requestID_[self])]
                    /\ pc' = [pc EXCEPT ![self] = "Label_74_5"]
                    /\ UNCHANGED << net, instream, stdPath, out, fileSystem, json, __call_stack, __path, stack, name_, pID__, clientID, requestID_, value, flag, __Profile_, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, feedBack, res, score, i, __Profile, id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

Label_74_5(self) == /\ pc[self] = "Label_74_5"
                    /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
                    /\ clientID' = [clientID EXCEPT ![self] = Head(stack[self]).clientID]
                    /\ requestID_' = [requestID_ EXCEPT ![self] = Head(stack[self]).requestID_]
                    /\ value' = [value EXCEPT ![self] = Head(stack[self]).value]
                    /\ flag' = [flag EXCEPT ![self] = Head(stack[self]).flag]
                    /\ __Profile_' = [__Profile_ EXCEPT ![self] = Head(stack[self]).__Profile_]
                    /\ name_' = [name_ EXCEPT ![self] = Head(stack[self]).name_]
                    /\ pID__' = [pID__ EXCEPT ![self] = Head(stack[self]).pID__]
                    /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
                    /\ UNCHANGED << net, instream, stdPath, out, fileSystem, json, __call_stack, __path, AServerIns, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, feedBack, res, score, i, __Profile, id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

__AServer_saveFS(self) == L56(self) \/ AtomSave(self) \/ Label_72_9(self)
                             \/ Label_74_5(self)

L71(self) == /\ pc[self] = "L71"
             /\ /\ __call_stack' = [__call_stack EXCEPT ![name[self]] = Tail(Tail(Tail(Tail(Tail(__call_stack[name[self]])))))]
                /\ requestID' = [requestID EXCEPT ![self] = Head(Tail(Tail(Tail(__call_stack[name[self]]))))]
                /\ responseID' = [responseID EXCEPT ![self] = Head(Tail(Tail(__call_stack[name[self]])))]
                /\ stdAnswer' = [stdAnswer EXCEPT ![self] = Head(Tail(__call_stack[name[self]]))]
                /\ studentResponse' = [studentResponse EXCEPT ![self] = Head(__call_stack[name[self]])]
                /\ uName' = [uName EXCEPT ![self] = Head(Tail(Tail(Tail(Tail(__call_stack[name[self]])))))]
             /\ feedBack' = [feedBack EXCEPT ![self] = [Answers |-> <<>>, Score |-> 0]]
             /\ res' = [res EXCEPT ![self] = ""]
             /\ score' = [score EXCEPT ![self] = 0]
             /\ IF Len(stdAnswer'[self].Answers) = Len(studentResponse'[self].Answers)
                   THEN /\ i' = [i EXCEPT ![self] = 1]
                        /\ pc' = [pc EXCEPT ![self] = "Label_94_9"]
                   ELSE /\ pc' = [pc EXCEPT ![self] = "Label_104_5"]
                        /\ i' = i
             /\ UNCHANGED << net, instream, stdPath, out, fileSystem, json, __path, AServerIns, stack, name_, pID__, clientID, requestID_, value, flag, __Profile_, name, pID, __Profile, id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

Label_94_9(self) == /\ pc[self] = "Label_94_9"
                    /\ IF i[self] <= Len(stdAnswer[self].Answers)
                          THEN /\ IF stdAnswer[self].Answers[(i[self])] /= studentResponse[self].Answers[(i[self])]
                                     THEN /\ feedBack' = [feedBack EXCEPT ![self].Answers = Append(feedBack[self].Answers, "False")]
                                          /\ score' = [score EXCEPT ![self] = score[self] + 1]
                                     ELSE /\ feedBack' = [feedBack EXCEPT ![self].Answers = Append(feedBack[self].Answers, "True")]
                                          /\ score' = score
                               /\ i' = [i EXCEPT ![self] = i[self] + 1]
                               /\ pc' = [pc EXCEPT ![self] = "Label_94_9"]
                          ELSE /\ pc' = [pc EXCEPT ![self] = "Label_104_5"]
                               /\ UNCHANGED << feedBack, score, i >>
                    /\ UNCHANGED << net, instream, stdPath, out, fileSystem, json, __call_stack, __path, AServerIns, stack, name_, pID__, clientID, requestID_, value, flag, __Profile_, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, res, __Profile, id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

Label_104_5(self) == /\ pc[self] = "Label_104_5"
                     /\ feedBack' = [feedBack EXCEPT ![self].Score = score[self]]
                     /\ res' = [res EXCEPT ![self] = feedBack'[self]]
                     /\ __call_stack' = [__call_stack EXCEPT ![self] = <<uName[self], requestID[self], score[self]>> \o __call_stack[self]]
                     /\ /\ name_' = [name_ EXCEPT ![self] = self]
                        /\ pID__' = [pID__ EXCEPT ![self] = pID[self]]
                        /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__AServer_saveFS",
                                                                 pc        |->  "resp",
                                                                 clientID  |->  clientID[self],
                                                                 requestID_ |->  requestID_[self],
                                                                 value     |->  value[self],
                                                                 flag      |->  flag[self],
                                                                 __Profile_ |->  __Profile_[self],
                                                                 name_     |->  name_[self],
                                                                 pID__     |->  pID__[self] ] >>
                                                             \o stack[self]]
                     /\ clientID' = [clientID EXCEPT ![self] = defaultInitValue]
                     /\ requestID_' = [requestID_ EXCEPT ![self] = defaultInitValue]
                     /\ value' = [value EXCEPT ![self] = defaultInitValue]
                     /\ flag' = [flag EXCEPT ![self] = defaultInitValue]
                     /\ __Profile_' = [__Profile_ EXCEPT ![self] = "__AServer"]
                     /\ pc' = [pc EXCEPT ![self] = "L56"]
                     /\ UNCHANGED << net, instream, stdPath, out, fileSystem, json, __path, AServerIns, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, score, i, __Profile, id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

resp(self) == /\ pc[self] = "resp"
              /\ net' = [net EXCEPT ![(responseID[self])][("resp")] = Append(net[(responseID[self])][("resp")], res[self])]
              /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
              /\ studentResponse' = [studentResponse EXCEPT ![self] = Head(stack[self]).studentResponse]
              /\ stdAnswer' = [stdAnswer EXCEPT ![self] = Head(stack[self]).stdAnswer]
              /\ responseID' = [responseID EXCEPT ![self] = Head(stack[self]).responseID]
              /\ requestID' = [requestID EXCEPT ![self] = Head(stack[self]).requestID]
              /\ uName' = [uName EXCEPT ![self] = Head(stack[self]).uName]
              /\ feedBack' = [feedBack EXCEPT ![self] = Head(stack[self]).feedBack]
              /\ res' = [res EXCEPT ![self] = Head(stack[self]).res]
              /\ score' = [score EXCEPT ![self] = Head(stack[self]).score]
              /\ i' = [i EXCEPT ![self] = Head(stack[self]).i]
              /\ __Profile' = [__Profile EXCEPT ![self] = Head(stack[self]).__Profile]
              /\ name' = [name EXCEPT ![self] = Head(stack[self]).name]
              /\ pID' = [pID EXCEPT ![self] = Head(stack[self]).pID]
              /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
              /\ UNCHANGED << instream, stdPath, out, fileSystem, json, __call_stack, __path, AServerIns, name_, pID__, clientID, requestID_, value, flag, __Profile_, id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

__AServer_computeScore(self) == L71(self) \/ Label_94_9(self)
                                   \/ Label_104_5(self) \/ resp(self)

Label_116_5(self) == /\ pc[self] = "Label_116_5"
                     /\ id_' = [id_ EXCEPT ![self] = pID_[self]]
                     /\ path' = [path EXCEPT ![self] = ""]
                     /\ submit' = [submit EXCEPT ![self] = ""]
                     /\ hwID' = [hwID EXCEPT ![self] = ""]
                     /\ pc' = [pc EXCEPT ![self] = "c"]
                     /\ UNCHANGED << net, instream, stdPath, out, fileSystem, json, __call_stack, __path, AServerIns, stack, name_, pID__, clientID, requestID_, value, flag, __Profile_, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, feedBack, res, score, i, __Profile, res_, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

c(self) == /\ pc[self] = "c"
           /\ submit' = [submit EXCEPT ![self] = ""]
           /\ res_' = [res_ EXCEPT ![self] = ""]
           /\ Len(instream) > 0
           /\ path' = [path EXCEPT ![self] = Head(instream)]
           /\ instream' = Tail(instream)
           /\ Len(stdPath) > 0
           /\ hwID' = [hwID EXCEPT ![self] = Head(stdPath)]
           /\ stdPath' = Tail(stdPath)
           /\ pc' = [pc EXCEPT ![self] = "Label_126_9"]
           /\ UNCHANGED << net, out, fileSystem, json, __call_stack, __path, AServerIns, stack, name_, pID__, clientID, requestID_, value, flag, __Profile_, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, feedBack, res, score, i, __Profile, id_, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

Label_126_9(self) == /\ pc[self] = "Label_126_9"
                     /\ submit' = [submit EXCEPT ![self] = fileSystem[(path[self])]]
                     /\ reqMsg' = [reqMsg EXCEPT ![self] = [Name |-> submit'[self].Name, Request_id |-> id_[self], Client_id |-> id_[self], Path |-> hwID[self], Content |-> [Answers |-> submit'[self].Answers]]]
                     /\ net' = [net EXCEPT ![(SERVER)][("req")] = Append(net[(SERVER)][("req")], reqMsg'[self])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_129_9"]
                     /\ UNCHANGED << instream, stdPath, out, fileSystem, json, __call_stack, __path, AServerIns, stack, name_, pID__, clientID, requestID_, value, flag, __Profile_, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, feedBack, res, score, i, __Profile, id_, path, hwID, res_, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

Label_129_9(self) == /\ pc[self] = "Label_129_9"
                     /\ Len(net[(id_[self])][("resp")]) > 0
                     /\ res_' = [res_ EXCEPT ![self] = Head(net[(id_[self])][("resp")])]
                     /\ net' = [net EXCEPT ![(id_[self])][("resp")] = Tail(net[(id_[self])][("resp")])]
                     /\ out' = Append(out, res_'[self])
                     /\ PrintT((<<"client", id_[self], "received resp:", res_'[self]>>))
                     /\ pc' = [pc EXCEPT ![self] = "c"]
                     /\ UNCHANGED << instream, stdPath, fileSystem, json, __call_stack, __path, AServerIns, stack, name_, pID__, clientID, requestID_, value, flag, __Profile_, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, feedBack, res, score, i, __Profile, id_, path, submit, hwID, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

AClientMain(self) == Label_116_5(self) \/ c(self) \/ Label_126_9(self)
                        \/ Label_129_9(self)

Label_139_5(self) == /\ pc[self] = "Label_139_5"
                     /\ id' = [id EXCEPT ![self] = pID_A[self]]
                     /\ answer' = [answer EXCEPT ![self] = ""]
                     /\ req' = [req EXCEPT ![self] = [__reserved |-> 0]]
                     /\ studentResponse_' = [studentResponse_ EXCEPT ![self] = [__reserved |-> 0]]
                     /\ stdAnswer_' = [stdAnswer_ EXCEPT ![self] = [__reserved |-> 0]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_144_5"]
                     /\ UNCHANGED << net, instream, stdPath, out, fileSystem, json, __call_stack, __path, AServerIns, stack, name_, pID__, clientID, requestID_, value, flag, __Profile_, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, feedBack, res, score, i, __Profile, id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, pMap, pID_A >>

Label_144_5(self) == /\ pc[self] = "Label_144_5"
                     /\ Len(net[(id[self])][("req")]) > 0
                     /\ req' = [req EXCEPT ![self] = Head(net[(id[self])][("req")])]
                     /\ net' = [net EXCEPT ![(id[self])][("req")] = Tail(net[(id[self])][("req")])]
                     /\ studentResponse_' = [studentResponse_ EXCEPT ![self] = req'[self].Content]
                     /\ answer' = [answer EXCEPT ![self] = fileSystem[((req'[self].Path))]]
                     /\ stdAnswer_' = [stdAnswer_ EXCEPT ![self] = answer'[self]]
                     /\ pc' = [pc EXCEPT ![self] = "computeScore"]
                     /\ UNCHANGED << instream, stdPath, out, fileSystem, json, __call_stack, __path, AServerIns, stack, name_, pID__, clientID, requestID_, value, flag, __Profile_, name, pID, studentResponse, stdAnswer, responseID, requestID, uName, feedBack, res, score, i, __Profile, id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, id, pMap, pID_A >>

computeScore(self) == /\ pc[self] = "computeScore"
                      /\ __call_stack' = [__call_stack EXCEPT ![self] = <<studentResponse_[self], stdAnswer_[self], req[self].Client_id, req[self].Request_id, req[self].Name>> \o __call_stack[self]]
                      /\ /\ name' = [name EXCEPT ![self] = self]
                         /\ pID' = [pID EXCEPT ![self] = pID_A[self]]
                         /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__AServer_computeScore",
                                                                  pc        |->  "Label_144_5",
                                                                  studentResponse |->  studentResponse[self],
                                                                  stdAnswer |->  stdAnswer[self],
                                                                  responseID |->  responseID[self],
                                                                  requestID |->  requestID[self],
                                                                  uName     |->  uName[self],
                                                                  feedBack  |->  feedBack[self],
                                                                  res       |->  res[self],
                                                                  score     |->  score[self],
                                                                  i         |->  i[self],
                                                                  __Profile |->  __Profile[self],
                                                                  name      |->  name[self],
                                                                  pID       |->  pID[self] ] >>
                                                              \o stack[self]]
                      /\ studentResponse' = [studentResponse EXCEPT ![self] = defaultInitValue]
                      /\ stdAnswer' = [stdAnswer EXCEPT ![self] = defaultInitValue]
                      /\ responseID' = [responseID EXCEPT ![self] = defaultInitValue]
                      /\ requestID' = [requestID EXCEPT ![self] = defaultInitValue]
                      /\ uName' = [uName EXCEPT ![self] = defaultInitValue]
                      /\ feedBack' = [feedBack EXCEPT ![self] = defaultInitValue]
                      /\ res' = [res EXCEPT ![self] = defaultInitValue]
                      /\ score' = [score EXCEPT ![self] = defaultInitValue]
                      /\ i' = [i EXCEPT ![self] = defaultInitValue]
                      /\ __Profile' = [__Profile EXCEPT ![self] = "__AServer"]
                      /\ pc' = [pc EXCEPT ![self] = "L71"]
                      /\ UNCHANGED << net, instream, stdPath, out, fileSystem, json, __path, AServerIns, name_, pID__, clientID, requestID_, value, flag, __Profile_, id_, path, submit, hwID, res_, reqMsg, pMap_, pID_, id, answer, req, studentResponse_, stdAnswer_, pMap, pID_A >>

AServerMain(self) == Label_139_5(self) \/ Label_144_5(self)
                        \/ computeScore(self)

(* Allow infinite stuttering to prevent deadlock on termination. *)
Terminating == /\ \A self \in ProcSet: pc[self] = "Done"
               /\ UNCHANGED vars

Next == (\E self \in ProcSet:  \/ __AServer_saveFS(self)
                               \/ __AServer_computeScore(self))
           \/ (\E self \in {"1Main"}: AClientMain(self))
           \/ (\E self \in {"2Main"}: AServerMain(self))
           \/ Terminating

Spec == Init /\ [][Next]_vars

Termination == <>(\A self \in ProcSet: pc[self] = "Done")

\* END TRANSLATION 
=============================================================================
