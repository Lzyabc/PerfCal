------------------------------- MODULE mqtt -------------------------------
EXTENDS Integers, TLC, Sequences
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

BrokerID == 1

(*--algorithm mqtt
variables
    net = [ins \in {1, 2, 4} |-> [chan \in {"unsubscribe_resp", "unsubscribe", "subscribe", "subscribe_resp", "publish", "pubrel", "pubrel_resp", "connect", "connect_resp", "publish_resp"} |-> <<>>]];
    QoS \in {0, 1, 2};
    instream = <<"30", "29">>;
    outstream = <<>>;
    log = <<>>;
    __call_stack = [p \in {"1HandlePuback", "1HandleUnsubscribe", "1HandlePublish", "2Main", "4Main", "1HandleConn", "1HandleSubscribe", "1HandlePubrel"} |-> <<>>];
    __path = 0;
    APublisherIns = [r \in {2} |-> [me |-> r]];
    ASubscriberIns = [r \in {4} |-> [me |-> r]];
    ABrokerIns = [r \in {1} |-> [waitREL |-> NewSet,activeClients |-> NewSet,TopicPool |-> NewPool,me |-> r]];

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
macro outstream_write (msg) begin
    outstream := Append(outstream, msg);
end macro;
macro log_write (msg) begin
    log := Append(log, msg);
end macro;
macro QoS_read (qos) begin
    qos := QoS;
end macro;
procedure __APublisher_Publish(name, pID)
variables
respMsg;reqMsg;
__Profile = "__APublisher";
begin
    L19:
    reqMsg := Head(__call_stack[name]) ||
    __call_stack[name] := Tail(__call_stack[name]);
    respMsg := [__reserved |-> 0];
    if reqMsg.QoS = 0 then
        net_write(reqMsg, BrokerID, "publish");
    elsif reqMsg.QoS = 1 then
        net_write(reqMsg, BrokerID, "publish");
        Label_91_9: net_read(respMsg, APublisherIns[pID].me, "publish_resp");
        Label_92_9: while respMsg.Type /= "PUBACK" do
            net_write(reqMsg, BrokerID, "publish");
            Label_94_13: net_read(respMsg, APublisherIns[pID].me, "publish_resp");
        end while;
    else
        net_write(reqMsg, BrokerID, "publish");
        Label_98_9: net_read(respMsg, APublisherIns[pID].me, "publish_resp");
        Label_99_9: while respMsg.Type /= "PUBREC" do
            net_write(reqMsg, BrokerID, "publish");
            Label_101_13: net_read(respMsg, APublisherIns[pID].me, "publish_resp");
        end while;
        reqMsg.Type := "PUBREL";
        net_write(reqMsg, BrokerID, "pubrel");
        Label_105_9: net_read(respMsg, APublisherIns[pID].me, "pubrel_resp");
        Label_106_9: while respMsg.Type /= "PUBCOMP" do
            net_write(reqMsg, BrokerID, "pubrel_resp");
            Label_108_13: net_read(respMsg, APublisherIns[pID].me, "pubrel");
        end while;
    end if;
    Label_111_5: outstream_write(respMsg);
    return;
end procedure;
procedure __ASubscriber_Subscribe(name, pID)
variables
respMsg;
__Profile = "__ASubscriber";
begin
    L113:
    reqMsg := Head(__call_stack[name]) ||
    __call_stack[name] := Tail(__call_stack[name]);
    respMsg := [__reserved |-> 0];
    net_write(reqMsg, BrokerID, "subscribe");
    Label_124_5: net_read(respMsg, ASubscriberIns[pID].me, "subscribe_resp");
    Label_125_5: while respMsg.Type /= "SUBACK" do
        net_write(reqMsg, BrokerID, "subscribe");
        Label_127_9: net_read(respMsg, ASubscriberIns[pID].me, "subscribe_resp");
    end while;
    __call_stack[name] := <<>> \o __call_stack[name];
    
    L124:
    return;
    Label_133_5: return;
end procedure;
process APublisherMain \in {"2Main"}
variables
    qos, msgContent, reqMsg, respMsg, pMap=[2Main |-> 2], pID=pMap[self];
begin
    Label_139_5: qos := QoS;
    msgContent := "";
    reqMsg := [Type |-> "CONNET", Sender |-> APublisherIns[pID].me];
    respMsg := [Type |-> ""];
    net_write(reqMsg, BrokerID, "connect");
    Label_144_5: net_read(respMsg, APublisherIns[pID].me, "connect_resp");
    Label_145_5: while respMsg.Type /= "CONNACK" do
        net_write(reqMsg, BrokerID, "connect");
        Label_147_9: net_read(respMsg, APublisherIns[pID].me, "connect_resp");
    end while;
    loopPublish:
    while TRUE do
        instream_read(msgContent);
        reqMsg := [Type |-> "PUBLISH", Sender |-> APublisherIns[pID].me, Content |-> msgContent, QoS |-> qos, Topic |-> "test"];
        __call_stack[self] := <<reqMsg>> \o __call_stack[self];
        call __APublisher_Publish(self, pID);
    end while;
end process;

process ASubscriberMain \in {"4Main"}
variables
    reqMsg, respMsg, msg, pMap=[4Main |-> 4], pID=pMap[self];
begin
    Label_162_5: reqMsg := [Type |-> "CONNET", Sender |-> ASubscriberIns[pID].me];
    respMsg := [Type |-> ""];
    Label_164_5: while respMsg.Type /= "CONNACK" do
        net_write(reqMsg, BrokerID, "connect");
        Label_166_9: net_read(respMsg, ASubscriberIns[pID].me, "connect_resp");
    end while;
    reqMsg := [Type |-> "SUBSCRIBE", Sender |-> ASubscriberIns[pID].me, Topic |-> "test"];
    __call_stack[self] := <<reqMsg>> \o __call_stack[self];
    call __ASubscriber_Subscribe(self, pID);
    Label_171_5: msg := [__reserved |-> 0];
    Label_172_5: while TRUE do
        net_read(msg, ASubscriberIns[pID].me, "publish");
        if msg.Type = "PUBLISH" then
            print(<<"Subscriber", ASubscriberIns[pID].me, "receive", msg>>);
            respMsg := [Type |-> "PUBACK", Sender |-> ASubscriberIns[pID].me];
            Label_177_13: net_write(respMsg, BrokerID, "publish_resp");
            log_write(msg.Content);
        end if;
    end while;
end process;

process ABrokerHandleConn \in {"1HandleConn"}
variables
    req, resp, pMap=[1HandleConn |-> 1], pID=pMap[self];
begin
    Label_187_5: req := [__reserved |-> 0];
    resp := [Type |-> ""];
    p:
    while TRUE do
        net_read(req, ABrokerIns[pID].me, "connect");
        resp.Type := "CONNACK";
        AtomAdd:
        ABrokerIns[pID].activeClients := AddElement(ABrokerIns[pID].activeClients, req.Sender);
        AddEnd:
        net_write(resp, req.Sender, "connect_resp");
    end while;
end process;

process ABrokerHandlePublish \in {"1HandlePublish"}
variables
    req, resp, pubMsg, clients, i, n, pMap=[1HandlePublish |-> 1], pID=pMap[self];
begin
    Label_204_5: req := [__reserved |-> 0];
    resp := [Sender |-> ABrokerIns[pID].me, Type |-> ""];
    pubMsg := [Type |-> "PUBLISH", Sender |-> ABrokerIns[pID].me];
    clients := <<>>;
    Label_208_5: while TRUE do
        net_read(req, ABrokerIns[pID].me, "publish");
        clients := GetSubscribers(ABrokerIns[pID].TopicPool, req.Topic);
        pubMsg := [Type |-> "PUBLISH", Sender |-> ABrokerIns[pID].me, Content |-> req.Content, QoS |-> req.QoS, Topic |-> req.Topic];
        i := 1;
        n := Len(clients);
        if req.QoS = 0 then
            Label_215_13: while i <= n do
                net_write(pubMsg, clients[(i)], "publish");
                i := i + 1;
            end while;
        elsif req.QoS = 1 then
            resp := [Sender |-> ABrokerIns[pID].me, Type |-> "PUBACK", QoS |-> 1];
            Label_221_13: while i <= n do
                net_write(pubMsg, clients[(i)], "publish");
                i := i + 1;
            end while;
            net_write(resp, req.Sender, "publish_resp");
        elsif req.QoS = 2 then
            resp.Type := "PUBREC";
            Label_228_13: while i <= n do
                net_write(pubMsg, clients[(i)], "publish");
                i := i + 1;
            end while;
            net_write(resp, req.Sender, "publish_resp");
            ABrokerIns[pID].waitREL := AddElement(ABrokerIns[pID].waitREL, req.Sender);
        end if;
    end while;
end process;

process ABrokerHandlePuback \in {"1HandlePuback"}
variables
    req, pMap=[1HandlePuback |-> 1], pID=pMap[self];
begin
    Label_242_5: req := [__reserved |-> 0];
    Label_243_5: while TRUE do
        net_read(req, ABrokerIns[pID].me, "publish_resp");
    end while;
end process;

process ABrokerHandlePubrel \in {"1HandlePubrel"}
variables
    req, resp, pMap=[1HandlePubrel |-> 1], pID=pMap[self];
begin
    Label_252_5: req := [__reserved |-> 0];
    resp := [Sender |-> ABrokerIns[pID].me, Type |-> ""];
    Label_254_5: while TRUE do
        net_read(req, ABrokerIns[pID].me, "pubrel");
        ABrokerIns[pID].waitREL := DelElement(ABrokerIns[pID].waitREL, req.Sender);
        resp.Type := "PUBCOMP";
        Label_258_9: net_write(resp, req.Sender, "pubrel_resp");
    end while;
end process;

process ABrokerHandleSubscribe \in {"1HandleSubscribe"}
variables
    req, resp, pMap=[1HandleSubscribe |-> 1], pID=pMap[self];
begin
    Label_266_5: req := [__reserved |-> 0];
    resp := [Sender |-> ABrokerIns[pID].me, Type |-> ""];
    Label_268_5: while TRUE do
        net_read(req, ABrokerIns[pID].me, "subscribe");
        ABrokerIns[pID].TopicPool := AddSubscriber(ABrokerIns[pID].TopicPool, req.Topic, req.Sender);
        resp.Type := "SUBACK";
        Label_272_9: net_write(resp, req.Sender, "subscribe_resp");
    end while;
end process;

process ABrokerHandleUnsubscribe \in {"1HandleUnsubscribe"}
variables
    req, resp, pMap=[1HandleUnsubscribe |-> 1], pID=pMap[self];
begin
    Label_280_5: req := [__reserved |-> 0];
    resp := [Sender |-> ABrokerIns[pID].me, Type |-> ""];
    Label_282_5: while TRUE do
        net_read(req, ABrokerIns[pID].me, "unsubscribe");
        ABrokerIns[pID].TopicPool := RemoveSubscriber(ABrokerIns[pID].TopicPool, req.Topic, req.Sender);
        resp.Type := "UNSUBACK";
        Label_286_9: net_write(resp, req.Sender, "unsubscribe_resp");
    end while;
end process;
end algorithm;*)
\* BEGIN TRANSLATION (chksum(pcal) = "25b0b4c1" /\ chksum(tla) = "da2fcf93")
\* Process variable reqMsg of process APublisherMain at line 137 col 22 changed to reqMsg_
\* Process variable respMsg of process APublisherMain at line 137 col 30 changed to respMsg_
\* Process variable pMap of process APublisherMain at line 137 col 39 changed to pMap_
\* Process variable pID of process APublisherMain at line 137 col 59 changed to pID_
\* Process variable reqMsg of process ASubscriberMain at line 160 col 5 changed to reqMsg_A
\* Process variable respMsg of process ASubscriberMain at line 160 col 13 changed to respMsg_A
\* Process variable pMap of process ASubscriberMain at line 160 col 27 changed to pMap_A
\* Process variable pID of process ASubscriberMain at line 160 col 47 changed to pID_A
\* Process variable req of process ABrokerHandleConn at line 185 col 5 changed to req_
\* Process variable resp of process ABrokerHandleConn at line 185 col 10 changed to resp_
\* Process variable pMap of process ABrokerHandleConn at line 185 col 16 changed to pMap_AB
\* Process variable pID of process ABrokerHandleConn at line 185 col 42 changed to pID_AB
\* Process variable req of process ABrokerHandlePublish at line 202 col 5 changed to req_A
\* Process variable resp of process ABrokerHandlePublish at line 202 col 10 changed to resp_A
\* Process variable pMap of process ABrokerHandlePublish at line 202 col 39 changed to pMap_ABr
\* Process variable pID of process ABrokerHandlePublish at line 202 col 68 changed to pID_ABr
\* Process variable req of process ABrokerHandlePuback at line 240 col 5 changed to req_AB
\* Process variable pMap of process ABrokerHandlePuback at line 240 col 10 changed to pMap_ABro
\* Process variable pID of process ABrokerHandlePuback at line 240 col 38 changed to pID_ABro
\* Process variable req of process ABrokerHandlePubrel at line 250 col 5 changed to req_ABr
\* Process variable resp of process ABrokerHandlePubrel at line 250 col 10 changed to resp_AB
\* Process variable pMap of process ABrokerHandlePubrel at line 250 col 16 changed to pMap_ABrok
\* Process variable pID of process ABrokerHandlePubrel at line 250 col 44 changed to pID_ABrok
\* Process variable req of process ABrokerHandleSubscribe at line 264 col 5 changed to req_ABro
\* Process variable resp of process ABrokerHandleSubscribe at line 264 col 10 changed to resp_ABr
\* Process variable pMap of process ABrokerHandleSubscribe at line 264 col 16 changed to pMap_ABroke
\* Process variable pID of process ABrokerHandleSubscribe at line 264 col 47 changed to pID_ABroke
\* Process variable pID of process ABrokerHandleUnsubscribe at line 278 col 49 changed to pID_ABroker
\* Procedure variable respMsg of procedure __APublisher_Publish at line 80 col 1 changed to respMsg__
\* Procedure variable __Profile of procedure __APublisher_Publish at line 81 col 1 changed to __Profile_
\* Parameter name of procedure __APublisher_Publish at line 78 col 32 changed to name_
\* Parameter pID of procedure __APublisher_Publish at line 78 col 38 changed to pID__
CONSTANT defaultInitValue
VARIABLES net, QoS, instream, outstream, log, __call_stack, __path, 
          APublisherIns, ASubscriberIns, ABrokerIns, pc, stack, name_, pID__, 
          respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, 
          msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, 
          msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, 
          pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, 
          pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, 
          resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker

vars == << net, QoS, instream, outstream, log, __call_stack, __path, 
           APublisherIns, ASubscriberIns, ABrokerIns, pc, stack, name_, pID__, 
           respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, 
           msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, 
           msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, 
           pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, 
           pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, 
           resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

ProcSet == ({"2Main"}) \cup ({"4Main"}) \cup ({"1HandleConn"}) \cup ({"1HandlePublish"}) \cup ({"1HandlePuback"}) \cup ({"1HandlePubrel"}) \cup ({"1HandleSubscribe"}) \cup ({"1HandleUnsubscribe"})

Init == (* Global variables *)
        /\ net = [ins \in {1, 2, 4} |-> [chan \in {"unsubscribe_resp", "unsubscribe", "subscribe", "subscribe_resp", "publish", "pubrel", "pubrel_resp", "connect", "connect_resp", "publish_resp"} |-> <<>>]]
        /\ QoS \in {0, 1, 2}
        /\ instream = <<"30", "29">>
        /\ outstream = <<>>
        /\ log = <<>>
        /\ __call_stack = [p \in {"1HandlePuback", "1HandleUnsubscribe", "1HandlePublish", "2Main", "4Main", "1HandleConn", "1HandleSubscribe", "1HandlePubrel"} |-> <<>>]
        /\ __path = 0
        /\ APublisherIns = [r \in {2} |-> [me |-> r]]
        /\ ASubscriberIns = [r \in {4} |-> [me |-> r]]
        /\ ABrokerIns = [r \in {1} |-> [waitREL |-> NewSet,activeClients |-> NewSet,TopicPool |-> NewPool,me |-> r]]
        (* Procedure __APublisher_Publish *)
        /\ name_ = [ self \in ProcSet |-> defaultInitValue]
        /\ pID__ = [ self \in ProcSet |-> defaultInitValue]
        /\ respMsg__ = [ self \in ProcSet |-> defaultInitValue]
        /\ reqMsg = [ self \in ProcSet |-> defaultInitValue]
        /\ __Profile_ = [ self \in ProcSet |-> "__APublisher"]
        (* Procedure __ASubscriber_Subscribe *)
        /\ name = [ self \in ProcSet |-> defaultInitValue]
        /\ pID = [ self \in ProcSet |-> defaultInitValue]
        /\ respMsg = [ self \in ProcSet |-> defaultInitValue]
        /\ __Profile = [ self \in ProcSet |-> "__ASubscriber"]
        (* Process APublisherMain *)
        /\ qos = [self \in {"2Main"} |-> defaultInitValue]
        /\ msgContent = [self \in {"2Main"} |-> defaultInitValue]
        /\ reqMsg_ = [self \in {"2Main"} |-> defaultInitValue]
        /\ respMsg_ = [self \in {"2Main"} |-> defaultInitValue]
        /\ pMap_ = [self \in {"2Main"} |-> [2Main |-> 2]]
        /\ pID_ = [self \in {"2Main"} |-> pMap_[self][self]]
        (* Process ASubscriberMain *)
        /\ reqMsg_A = [self \in {"4Main"} |-> defaultInitValue]
        /\ respMsg_A = [self \in {"4Main"} |-> defaultInitValue]
        /\ msg = [self \in {"4Main"} |-> defaultInitValue]
        /\ pMap_A = [self \in {"4Main"} |-> [4Main |-> 4]]
        /\ pID_A = [self \in {"4Main"} |-> pMap_A[self][self]]
        (* Process ABrokerHandleConn *)
        /\ req_ = [self \in {"1HandleConn"} |-> defaultInitValue]
        /\ resp_ = [self \in {"1HandleConn"} |-> defaultInitValue]
        /\ pMap_AB = [self \in {"1HandleConn"} |-> [1HandleConn |-> 1]]
        /\ pID_AB = [self \in {"1HandleConn"} |-> pMap_AB[self][self]]
        (* Process ABrokerHandlePublish *)
        /\ req_A = [self \in {"1HandlePublish"} |-> defaultInitValue]
        /\ resp_A = [self \in {"1HandlePublish"} |-> defaultInitValue]
        /\ pubMsg = [self \in {"1HandlePublish"} |-> defaultInitValue]
        /\ clients = [self \in {"1HandlePublish"} |-> defaultInitValue]
        /\ i = [self \in {"1HandlePublish"} |-> defaultInitValue]
        /\ n = [self \in {"1HandlePublish"} |-> defaultInitValue]
        /\ pMap_ABr = [self \in {"1HandlePublish"} |-> [1HandlePublish |-> 1]]
        /\ pID_ABr = [self \in {"1HandlePublish"} |-> pMap_ABr[self][self]]
        (* Process ABrokerHandlePuback *)
        /\ req_AB = [self \in {"1HandlePuback"} |-> defaultInitValue]
        /\ pMap_ABro = [self \in {"1HandlePuback"} |-> [1HandlePuback |-> 1]]
        /\ pID_ABro = [self \in {"1HandlePuback"} |-> pMap_ABro[self][self]]
        (* Process ABrokerHandlePubrel *)
        /\ req_ABr = [self \in {"1HandlePubrel"} |-> defaultInitValue]
        /\ resp_AB = [self \in {"1HandlePubrel"} |-> defaultInitValue]
        /\ pMap_ABrok = [self \in {"1HandlePubrel"} |-> [1HandlePubrel |-> 1]]
        /\ pID_ABrok = [self \in {"1HandlePubrel"} |-> pMap_ABrok[self][self]]
        (* Process ABrokerHandleSubscribe *)
        /\ req_ABro = [self \in {"1HandleSubscribe"} |-> defaultInitValue]
        /\ resp_ABr = [self \in {"1HandleSubscribe"} |-> defaultInitValue]
        /\ pMap_ABroke = [self \in {"1HandleSubscribe"} |-> [1HandleSubscribe |-> 1]]
        /\ pID_ABroke = [self \in {"1HandleSubscribe"} |-> pMap_ABroke[self][self]]
        (* Process ABrokerHandleUnsubscribe *)
        /\ req = [self \in {"1HandleUnsubscribe"} |-> defaultInitValue]
        /\ resp = [self \in {"1HandleUnsubscribe"} |-> defaultInitValue]
        /\ pMap = [self \in {"1HandleUnsubscribe"} |-> [1HandleUnsubscribe |-> 1]]
        /\ pID_ABroker = [self \in {"1HandleUnsubscribe"} |-> pMap[self][self]]
        /\ stack = [self \in ProcSet |-> << >>]
        /\ pc = [self \in ProcSet |-> CASE self \in {"2Main"} -> "Label_139_5"
                                        [] self \in {"4Main"} -> "Label_162_5"
                                        [] self \in {"1HandleConn"} -> "Label_187_5"
                                        [] self \in {"1HandlePublish"} -> "Label_204_5"
                                        [] self \in {"1HandlePuback"} -> "Label_242_5"
                                        [] self \in {"1HandlePubrel"} -> "Label_252_5"
                                        [] self \in {"1HandleSubscribe"} -> "Label_266_5"
                                        [] self \in {"1HandleUnsubscribe"} -> "Label_280_5"]

L19(self) == /\ pc[self] = "L19"
             /\ /\ __call_stack' = [__call_stack EXCEPT ![name_[self]] = Tail(__call_stack[name_[self]])]
                /\ reqMsg' = [reqMsg EXCEPT ![self] = Head(__call_stack[name_[self]])]
             /\ respMsg__' = [respMsg__ EXCEPT ![self] = [__reserved |-> 0]]
             /\ IF reqMsg'[self].QoS = 0
                   THEN /\ net' = [net EXCEPT ![(BrokerID)][("publish")] = Append(net[(BrokerID)][("publish")], reqMsg'[self])]
                        /\ pc' = [pc EXCEPT ![self] = "Label_111_5"]
                   ELSE /\ IF reqMsg'[self].QoS = 1
                              THEN /\ net' = [net EXCEPT ![(BrokerID)][("publish")] = Append(net[(BrokerID)][("publish")], reqMsg'[self])]
                                   /\ pc' = [pc EXCEPT ![self] = "Label_91_9"]
                              ELSE /\ net' = [net EXCEPT ![(BrokerID)][("publish")] = Append(net[(BrokerID)][("publish")], reqMsg'[self])]
                                   /\ pc' = [pc EXCEPT ![self] = "Label_98_9"]
             /\ UNCHANGED << QoS, instream, outstream, log, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_91_9(self) == /\ pc[self] = "Label_91_9"
                    /\ Len(net[((APublisherIns[pID__[self]].me))][("publish_resp")]) > 0
                    /\ respMsg__' = [respMsg__ EXCEPT ![self] = Head(net[((APublisherIns[pID__[self]].me))][("publish_resp")])]
                    /\ net' = [net EXCEPT ![((APublisherIns[pID__[self]].me))][("publish_resp")] = Tail(net[((APublisherIns[pID__[self]].me))][("publish_resp")])]
                    /\ pc' = [pc EXCEPT ![self] = "Label_92_9"]
                    /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_92_9(self) == /\ pc[self] = "Label_92_9"
                    /\ IF respMsg__[self].Type /= "PUBACK"
                          THEN /\ net' = [net EXCEPT ![(BrokerID)][("publish")] = Append(net[(BrokerID)][("publish")], reqMsg[self])]
                               /\ pc' = [pc EXCEPT ![self] = "Label_94_13"]
                          ELSE /\ pc' = [pc EXCEPT ![self] = "Label_111_5"]
                               /\ net' = net
                    /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_94_13(self) == /\ pc[self] = "Label_94_13"
                     /\ Len(net[((APublisherIns[pID__[self]].me))][("publish_resp")]) > 0
                     /\ respMsg__' = [respMsg__ EXCEPT ![self] = Head(net[((APublisherIns[pID__[self]].me))][("publish_resp")])]
                     /\ net' = [net EXCEPT ![((APublisherIns[pID__[self]].me))][("publish_resp")] = Tail(net[((APublisherIns[pID__[self]].me))][("publish_resp")])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_92_9"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_98_9(self) == /\ pc[self] = "Label_98_9"
                    /\ Len(net[((APublisherIns[pID__[self]].me))][("publish_resp")]) > 0
                    /\ respMsg__' = [respMsg__ EXCEPT ![self] = Head(net[((APublisherIns[pID__[self]].me))][("publish_resp")])]
                    /\ net' = [net EXCEPT ![((APublisherIns[pID__[self]].me))][("publish_resp")] = Tail(net[((APublisherIns[pID__[self]].me))][("publish_resp")])]
                    /\ pc' = [pc EXCEPT ![self] = "Label_99_9"]
                    /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_99_9(self) == /\ pc[self] = "Label_99_9"
                    /\ IF respMsg__[self].Type /= "PUBREC"
                          THEN /\ net' = [net EXCEPT ![(BrokerID)][("publish")] = Append(net[(BrokerID)][("publish")], reqMsg[self])]
                               /\ pc' = [pc EXCEPT ![self] = "Label_101_13"]
                               /\ UNCHANGED reqMsg
                          ELSE /\ reqMsg' = [reqMsg EXCEPT ![self].Type = "PUBREL"]
                               /\ net' = [net EXCEPT ![(BrokerID)][("pubrel")] = Append(net[(BrokerID)][("pubrel")], reqMsg'[self])]
                               /\ pc' = [pc EXCEPT ![self] = "Label_105_9"]
                    /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_101_13(self) == /\ pc[self] = "Label_101_13"
                      /\ Len(net[((APublisherIns[pID__[self]].me))][("publish_resp")]) > 0
                      /\ respMsg__' = [respMsg__ EXCEPT ![self] = Head(net[((APublisherIns[pID__[self]].me))][("publish_resp")])]
                      /\ net' = [net EXCEPT ![((APublisherIns[pID__[self]].me))][("publish_resp")] = Tail(net[((APublisherIns[pID__[self]].me))][("publish_resp")])]
                      /\ pc' = [pc EXCEPT ![self] = "Label_99_9"]
                      /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_105_9(self) == /\ pc[self] = "Label_105_9"
                     /\ Len(net[((APublisherIns[pID__[self]].me))][("pubrel_resp")]) > 0
                     /\ respMsg__' = [respMsg__ EXCEPT ![self] = Head(net[((APublisherIns[pID__[self]].me))][("pubrel_resp")])]
                     /\ net' = [net EXCEPT ![((APublisherIns[pID__[self]].me))][("pubrel_resp")] = Tail(net[((APublisherIns[pID__[self]].me))][("pubrel_resp")])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_106_9"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_106_9(self) == /\ pc[self] = "Label_106_9"
                     /\ IF respMsg__[self].Type /= "PUBCOMP"
                           THEN /\ net' = [net EXCEPT ![(BrokerID)][("pubrel_resp")] = Append(net[(BrokerID)][("pubrel_resp")], reqMsg[self])]
                                /\ pc' = [pc EXCEPT ![self] = "Label_108_13"]
                           ELSE /\ pc' = [pc EXCEPT ![self] = "Label_111_5"]
                                /\ net' = net
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_108_13(self) == /\ pc[self] = "Label_108_13"
                      /\ Len(net[((APublisherIns[pID__[self]].me))][("pubrel")]) > 0
                      /\ respMsg__' = [respMsg__ EXCEPT ![self] = Head(net[((APublisherIns[pID__[self]].me))][("pubrel")])]
                      /\ net' = [net EXCEPT ![((APublisherIns[pID__[self]].me))][("pubrel")] = Tail(net[((APublisherIns[pID__[self]].me))][("pubrel")])]
                      /\ pc' = [pc EXCEPT ![self] = "Label_106_9"]
                      /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_111_5(self) == /\ pc[self] = "Label_111_5"
                     /\ outstream' = Append(outstream, respMsg__[self])
                     /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
                     /\ respMsg__' = [respMsg__ EXCEPT ![self] = Head(stack[self]).respMsg__]
                     /\ reqMsg' = [reqMsg EXCEPT ![self] = Head(stack[self]).reqMsg]
                     /\ __Profile_' = [__Profile_ EXCEPT ![self] = Head(stack[self]).__Profile_]
                     /\ name_' = [name_ EXCEPT ![self] = Head(stack[self]).name_]
                     /\ pID__' = [pID__ EXCEPT ![self] = Head(stack[self]).pID__]
                     /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
                     /\ UNCHANGED << net, QoS, instream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

__APublisher_Publish(self) == L19(self) \/ Label_91_9(self)
                                 \/ Label_92_9(self) \/ Label_94_13(self)
                                 \/ Label_98_9(self) \/ Label_99_9(self)
                                 \/ Label_101_13(self) \/ Label_105_9(self)
                                 \/ Label_106_9(self) \/ Label_108_13(self)
                                 \/ Label_111_5(self)

L113(self) == /\ pc[self] = "L113"
              /\ /\ __call_stack' = [__call_stack EXCEPT ![name[self]] = Tail(__call_stack[name[self]])]
                 /\ reqMsg' = [reqMsg EXCEPT ![self] = Head(__call_stack[name[self]])]
              /\ respMsg' = [respMsg EXCEPT ![self] = [__reserved |-> 0]]
              /\ net' = [net EXCEPT ![(BrokerID)][("subscribe")] = Append(net[(BrokerID)][("subscribe")], reqMsg'[self])]
              /\ pc' = [pc EXCEPT ![self] = "Label_124_5"]
              /\ UNCHANGED << QoS, instream, outstream, log, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, __Profile_, name, pID, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_124_5(self) == /\ pc[self] = "Label_124_5"
                     /\ Len(net[((ASubscriberIns[pID[self]].me))][("subscribe_resp")]) > 0
                     /\ respMsg' = [respMsg EXCEPT ![self] = Head(net[((ASubscriberIns[pID[self]].me))][("subscribe_resp")])]
                     /\ net' = [net EXCEPT ![((ASubscriberIns[pID[self]].me))][("subscribe_resp")] = Tail(net[((ASubscriberIns[pID[self]].me))][("subscribe_resp")])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_125_5"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_125_5(self) == /\ pc[self] = "Label_125_5"
                     /\ IF respMsg[self].Type /= "SUBACK"
                           THEN /\ net' = [net EXCEPT ![(BrokerID)][("subscribe")] = Append(net[(BrokerID)][("subscribe")], reqMsg[self])]
                                /\ pc' = [pc EXCEPT ![self] = "Label_127_9"]
                                /\ UNCHANGED __call_stack
                           ELSE /\ __call_stack' = [__call_stack EXCEPT ![name[self]] = <<>> \o __call_stack[name[self]]]
                                /\ pc' = [pc EXCEPT ![self] = "L124"]
                                /\ net' = net
                     /\ UNCHANGED << QoS, instream, outstream, log, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_127_9(self) == /\ pc[self] = "Label_127_9"
                     /\ Len(net[((ASubscriberIns[pID[self]].me))][("subscribe_resp")]) > 0
                     /\ respMsg' = [respMsg EXCEPT ![self] = Head(net[((ASubscriberIns[pID[self]].me))][("subscribe_resp")])]
                     /\ net' = [net EXCEPT ![((ASubscriberIns[pID[self]].me))][("subscribe_resp")] = Tail(net[((ASubscriberIns[pID[self]].me))][("subscribe_resp")])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_125_5"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

L124(self) == /\ pc[self] = "L124"
              /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
              /\ respMsg' = [respMsg EXCEPT ![self] = Head(stack[self]).respMsg]
              /\ __Profile' = [__Profile EXCEPT ![self] = Head(stack[self]).__Profile]
              /\ name' = [name EXCEPT ![self] = Head(stack[self]).name]
              /\ pID' = [pID EXCEPT ![self] = Head(stack[self]).pID]
              /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
              /\ UNCHANGED << net, QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, name_, pID__, respMsg__, reqMsg, __Profile_, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_133_5(self) == /\ pc[self] = "Label_133_5"
                     /\ pc' = [pc EXCEPT ![self] = Head(stack[self]).pc]
                     /\ respMsg' = [respMsg EXCEPT ![self] = Head(stack[self]).respMsg]
                     /\ __Profile' = [__Profile EXCEPT ![self] = Head(stack[self]).__Profile]
                     /\ name' = [name EXCEPT ![self] = Head(stack[self]).name]
                     /\ pID' = [pID EXCEPT ![self] = Head(stack[self]).pID]
                     /\ stack' = [stack EXCEPT ![self] = Tail(stack[self])]
                     /\ UNCHANGED << net, QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, name_, pID__, respMsg__, reqMsg, __Profile_, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

__ASubscriber_Subscribe(self) == L113(self) \/ Label_124_5(self)
                                    \/ Label_125_5(self)
                                    \/ Label_127_9(self) \/ L124(self)
                                    \/ Label_133_5(self)

Label_139_5(self) == /\ pc[self] = "Label_139_5"
                     /\ qos' = [qos EXCEPT ![self] = QoS]
                     /\ msgContent' = [msgContent EXCEPT ![self] = ""]
                     /\ reqMsg_' = [reqMsg_ EXCEPT ![self] = [Type |-> "CONNET", Sender |-> APublisherIns[pID_[self]].me]]
                     /\ respMsg_' = [respMsg_ EXCEPT ![self] = [Type |-> ""]]
                     /\ net' = [net EXCEPT ![(BrokerID)][("connect")] = Append(net[(BrokerID)][("connect")], reqMsg_'[self])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_144_5"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_144_5(self) == /\ pc[self] = "Label_144_5"
                     /\ Len(net[((APublisherIns[pID_[self]].me))][("connect_resp")]) > 0
                     /\ respMsg_' = [respMsg_ EXCEPT ![self] = Head(net[((APublisherIns[pID_[self]].me))][("connect_resp")])]
                     /\ net' = [net EXCEPT ![((APublisherIns[pID_[self]].me))][("connect_resp")] = Tail(net[((APublisherIns[pID_[self]].me))][("connect_resp")])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_145_5"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_145_5(self) == /\ pc[self] = "Label_145_5"
                     /\ IF respMsg_[self].Type /= "CONNACK"
                           THEN /\ net' = [net EXCEPT ![(BrokerID)][("connect")] = Append(net[(BrokerID)][("connect")], reqMsg_[self])]
                                /\ pc' = [pc EXCEPT ![self] = "Label_147_9"]
                           ELSE /\ pc' = [pc EXCEPT ![self] = "loopPublish"]
                                /\ net' = net
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_147_9(self) == /\ pc[self] = "Label_147_9"
                     /\ Len(net[((APublisherIns[pID_[self]].me))][("connect_resp")]) > 0
                     /\ respMsg_' = [respMsg_ EXCEPT ![self] = Head(net[((APublisherIns[pID_[self]].me))][("connect_resp")])]
                     /\ net' = [net EXCEPT ![((APublisherIns[pID_[self]].me))][("connect_resp")] = Tail(net[((APublisherIns[pID_[self]].me))][("connect_resp")])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_145_5"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

loopPublish(self) == /\ pc[self] = "loopPublish"
                     /\ Len(instream) > 0
                     /\ msgContent' = [msgContent EXCEPT ![self] = Head(instream)]
                     /\ instream' = Tail(instream)
                     /\ reqMsg_' = [reqMsg_ EXCEPT ![self] = [Type |-> "PUBLISH", Sender |-> APublisherIns[pID_[self]].me, Content |-> msgContent'[self], QoS |-> qos[self], Topic |-> "test"]]
                     /\ __call_stack' = [__call_stack EXCEPT ![self] = <<reqMsg_'[self]>> \o __call_stack[self]]
                     /\ /\ name_' = [name_ EXCEPT ![self] = self]
                        /\ pID__' = [pID__ EXCEPT ![self] = pID_[self]]
                        /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__APublisher_Publish",
                                                                 pc        |->  "loopPublish",
                                                                 respMsg__ |->  respMsg__[self],
                                                                 reqMsg    |->  reqMsg[self],
                                                                 __Profile_ |->  __Profile_[self],
                                                                 name_     |->  name_[self],
                                                                 pID__     |->  pID__[self] ] >>
                                                             \o stack[self]]
                     /\ respMsg__' = [respMsg__ EXCEPT ![self] = defaultInitValue]
                     /\ reqMsg' = [reqMsg EXCEPT ![self] = defaultInitValue]
                     /\ __Profile_' = [__Profile_ EXCEPT ![self] = "__APublisher"]
                     /\ pc' = [pc EXCEPT ![self] = "L19"]
                     /\ UNCHANGED << net, QoS, outstream, log, __path, APublisherIns, ASubscriberIns, ABrokerIns, name, pID, respMsg, __Profile, qos, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

APublisherMain(self) == Label_139_5(self) \/ Label_144_5(self)
                           \/ Label_145_5(self) \/ Label_147_9(self)
                           \/ loopPublish(self)

Label_162_5(self) == /\ pc[self] = "Label_162_5"
                     /\ reqMsg_A' = [reqMsg_A EXCEPT ![self] = [Type |-> "CONNET", Sender |-> ASubscriberIns[pID_A[self]].me]]
                     /\ respMsg_A' = [respMsg_A EXCEPT ![self] = [Type |-> ""]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_164_5"]
                     /\ UNCHANGED << net, QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_164_5(self) == /\ pc[self] = "Label_164_5"
                     /\ IF respMsg_A[self].Type /= "CONNACK"
                           THEN /\ net' = [net EXCEPT ![(BrokerID)][("connect")] = Append(net[(BrokerID)][("connect")], reqMsg_A[self])]
                                /\ pc' = [pc EXCEPT ![self] = "Label_166_9"]
                                /\ UNCHANGED << __call_stack, stack, name, pID, 
                                                respMsg, __Profile, reqMsg_A >>
                           ELSE /\ reqMsg_A' = [reqMsg_A EXCEPT ![self] = [Type |-> "SUBSCRIBE", Sender |-> ASubscriberIns[pID_A[self]].me, Topic |-> "test"]]
                                /\ __call_stack' = [__call_stack EXCEPT ![self] = <<reqMsg_A'[self]>> \o __call_stack[self]]
                                /\ /\ name' = [name EXCEPT ![self] = self]
                                   /\ pID' = [pID EXCEPT ![self] = pID_A[self]]
                                   /\ stack' = [stack EXCEPT ![self] = << [ procedure |->  "__ASubscriber_Subscribe",
                                                                            pc        |->  "Label_171_5",
                                                                            respMsg   |->  respMsg[self],
                                                                            __Profile |->  __Profile[self],
                                                                            name      |->  name[self],
                                                                            pID       |->  pID[self] ] >>
                                                                        \o stack[self]]
                                /\ respMsg' = [respMsg EXCEPT ![self] = defaultInitValue]
                                /\ __Profile' = [__Profile EXCEPT ![self] = "__ASubscriber"]
                                /\ pc' = [pc EXCEPT ![self] = "L113"]
                                /\ net' = net
                     /\ UNCHANGED << QoS, instream, outstream, log, __path, APublisherIns, ASubscriberIns, ABrokerIns, name_, pID__, respMsg__, reqMsg, __Profile_, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_166_9(self) == /\ pc[self] = "Label_166_9"
                     /\ Len(net[((ASubscriberIns[pID_A[self]].me))][("connect_resp")]) > 0
                     /\ respMsg_A' = [respMsg_A EXCEPT ![self] = Head(net[((ASubscriberIns[pID_A[self]].me))][("connect_resp")])]
                     /\ net' = [net EXCEPT ![((ASubscriberIns[pID_A[self]].me))][("connect_resp")] = Tail(net[((ASubscriberIns[pID_A[self]].me))][("connect_resp")])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_164_5"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_171_5(self) == /\ pc[self] = "Label_171_5"
                     /\ msg' = [msg EXCEPT ![self] = [__reserved |-> 0]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_172_5"]
                     /\ UNCHANGED << net, QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_172_5(self) == /\ pc[self] = "Label_172_5"
                     /\ Len(net[((ASubscriberIns[pID_A[self]].me))][("publish")]) > 0
                     /\ msg' = [msg EXCEPT ![self] = Head(net[((ASubscriberIns[pID_A[self]].me))][("publish")])]
                     /\ net' = [net EXCEPT ![((ASubscriberIns[pID_A[self]].me))][("publish")] = Tail(net[((ASubscriberIns[pID_A[self]].me))][("publish")])]
                     /\ IF msg'[self].Type = "PUBLISH"
                           THEN /\ PrintT((<<"Subscriber", ASubscriberIns[pID_A[self]].me, "receive", msg'[self]>>))
                                /\ respMsg_A' = [respMsg_A EXCEPT ![self] = [Type |-> "PUBACK", Sender |-> ASubscriberIns[pID_A[self]].me]]
                                /\ pc' = [pc EXCEPT ![self] = "Label_177_13"]
                           ELSE /\ pc' = [pc EXCEPT ![self] = "Label_172_5"]
                                /\ UNCHANGED respMsg_A
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_177_13(self) == /\ pc[self] = "Label_177_13"
                      /\ net' = [net EXCEPT ![(BrokerID)][("publish_resp")] = Append(net[(BrokerID)][("publish_resp")], respMsg_A[self])]
                      /\ log' = Append(log, (msg[self].Content))
                      /\ pc' = [pc EXCEPT ![self] = "Label_172_5"]
                      /\ UNCHANGED << QoS, instream, outstream, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

ASubscriberMain(self) == Label_162_5(self) \/ Label_164_5(self)
                            \/ Label_166_9(self) \/ Label_171_5(self)
                            \/ Label_172_5(self) \/ Label_177_13(self)

Label_187_5(self) == /\ pc[self] = "Label_187_5"
                     /\ req_' = [req_ EXCEPT ![self] = [__reserved |-> 0]]
                     /\ resp_' = [resp_ EXCEPT ![self] = [Type |-> ""]]
                     /\ pc' = [pc EXCEPT ![self] = "p"]
                     /\ UNCHANGED << net, QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

p(self) == /\ pc[self] = "p"
           /\ Len(net[((ABrokerIns[pID_AB[self]].me))][("connect")]) > 0
           /\ req_' = [req_ EXCEPT ![self] = Head(net[((ABrokerIns[pID_AB[self]].me))][("connect")])]
           /\ net' = [net EXCEPT ![((ABrokerIns[pID_AB[self]].me))][("connect")] = Tail(net[((ABrokerIns[pID_AB[self]].me))][("connect")])]
           /\ resp_' = [resp_ EXCEPT ![self].Type = "CONNACK"]
           /\ pc' = [pc EXCEPT ![self] = "AtomAdd"]
           /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

AtomAdd(self) == /\ pc[self] = "AtomAdd"
                 /\ ABrokerIns' = [ABrokerIns EXCEPT ![pID_AB[self]].activeClients = AddElement(ABrokerIns[pID_AB[self]].activeClients, req_[self].Sender)]
                 /\ pc' = [pc EXCEPT ![self] = "AddEnd"]
                 /\ UNCHANGED << net, QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

AddEnd(self) == /\ pc[self] = "AddEnd"
                /\ net' = [net EXCEPT ![((req_[self].Sender))][("connect_resp")] = Append(net[((req_[self].Sender))][("connect_resp")], resp_[self])]
                /\ pc' = [pc EXCEPT ![self] = "p"]
                /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

ABrokerHandleConn(self) == Label_187_5(self) \/ p(self) \/ AtomAdd(self)
                              \/ AddEnd(self)

Label_204_5(self) == /\ pc[self] = "Label_204_5"
                     /\ req_A' = [req_A EXCEPT ![self] = [__reserved |-> 0]]
                     /\ resp_A' = [resp_A EXCEPT ![self] = [Sender |-> ABrokerIns[pID_ABr[self]].me, Type |-> ""]]
                     /\ pubMsg' = [pubMsg EXCEPT ![self] = [Type |-> "PUBLISH", Sender |-> ABrokerIns[pID_ABr[self]].me]]
                     /\ clients' = [clients EXCEPT ![self] = <<>>]
                     /\ pc' = [pc EXCEPT ![self] = "Label_208_5"]
                     /\ UNCHANGED << net, QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_208_5(self) == /\ pc[self] = "Label_208_5"
                     /\ Len(net[((ABrokerIns[pID_ABr[self]].me))][("publish")]) > 0
                     /\ req_A' = [req_A EXCEPT ![self] = Head(net[((ABrokerIns[pID_ABr[self]].me))][("publish")])]
                     /\ net' = [net EXCEPT ![((ABrokerIns[pID_ABr[self]].me))][("publish")] = Tail(net[((ABrokerIns[pID_ABr[self]].me))][("publish")])]
                     /\ clients' = [clients EXCEPT ![self] = GetSubscribers(ABrokerIns[pID_ABr[self]].TopicPool, req_A'[self].Topic)]
                     /\ pubMsg' = [pubMsg EXCEPT ![self] = [Type |-> "PUBLISH", Sender |-> ABrokerIns[pID_ABr[self]].me, Content |-> req_A'[self].Content, QoS |-> req_A'[self].QoS, Topic |-> req_A'[self].Topic]]
                     /\ i' = [i EXCEPT ![self] = 1]
                     /\ n' = [n EXCEPT ![self] = Len(clients'[self])]
                     /\ IF req_A'[self].QoS = 0
                           THEN /\ pc' = [pc EXCEPT ![self] = "Label_215_13"]
                                /\ UNCHANGED resp_A
                           ELSE /\ IF req_A'[self].QoS = 1
                                      THEN /\ resp_A' = [resp_A EXCEPT ![self] = [Sender |-> ABrokerIns[pID_ABr[self]].me, Type |-> "PUBACK", QoS |-> 1]]
                                           /\ pc' = [pc EXCEPT ![self] = "Label_221_13"]
                                      ELSE /\ IF req_A'[self].QoS = 2
                                                 THEN /\ resp_A' = [resp_A EXCEPT ![self].Type = "PUBREC"]
                                                      /\ pc' = [pc EXCEPT ![self] = "Label_228_13"]
                                                 ELSE /\ pc' = [pc EXCEPT ![self] = "Label_208_5"]
                                                      /\ UNCHANGED resp_A
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_215_13(self) == /\ pc[self] = "Label_215_13"
                      /\ IF i[self] <= n[self]
                            THEN /\ net' = [net EXCEPT ![((clients[self][(i[self])]))][("publish")] = Append(net[((clients[self][(i[self])]))][("publish")], pubMsg[self])]
                                 /\ i' = [i EXCEPT ![self] = i[self] + 1]
                                 /\ pc' = [pc EXCEPT ![self] = "Label_215_13"]
                            ELSE /\ pc' = [pc EXCEPT ![self] = "Label_208_5"]
                                 /\ UNCHANGED << net, i >>
                      /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_221_13(self) == /\ pc[self] = "Label_221_13"
                      /\ IF i[self] <= n[self]
                            THEN /\ net' = [net EXCEPT ![((clients[self][(i[self])]))][("publish")] = Append(net[((clients[self][(i[self])]))][("publish")], pubMsg[self])]
                                 /\ i' = [i EXCEPT ![self] = i[self] + 1]
                                 /\ pc' = [pc EXCEPT ![self] = "Label_221_13"]
                            ELSE /\ net' = [net EXCEPT ![((req_A[self].Sender))][("publish_resp")] = Append(net[((req_A[self].Sender))][("publish_resp")], resp_A[self])]
                                 /\ pc' = [pc EXCEPT ![self] = "Label_208_5"]
                                 /\ i' = i
                      /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_228_13(self) == /\ pc[self] = "Label_228_13"
                      /\ IF i[self] <= n[self]
                            THEN /\ net' = [net EXCEPT ![((clients[self][(i[self])]))][("publish")] = Append(net[((clients[self][(i[self])]))][("publish")], pubMsg[self])]
                                 /\ i' = [i EXCEPT ![self] = i[self] + 1]
                                 /\ pc' = [pc EXCEPT ![self] = "Label_228_13"]
                                 /\ UNCHANGED ABrokerIns
                            ELSE /\ net' = [net EXCEPT ![((req_A[self].Sender))][("publish_resp")] = Append(net[((req_A[self].Sender))][("publish_resp")], resp_A[self])]
                                 /\ ABrokerIns' = [ABrokerIns EXCEPT ![pID_ABr[self]].waitREL = AddElement(ABrokerIns[pID_ABr[self]].waitREL, req_A[self].Sender)]
                                 /\ pc' = [pc EXCEPT ![self] = "Label_208_5"]
                                 /\ i' = i
                      /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

ABrokerHandlePublish(self) == Label_204_5(self) \/ Label_208_5(self)
                                 \/ Label_215_13(self)
                                 \/ Label_221_13(self)
                                 \/ Label_228_13(self)

Label_242_5(self) == /\ pc[self] = "Label_242_5"
                     /\ req_AB' = [req_AB EXCEPT ![self] = [__reserved |-> 0]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_243_5"]
                     /\ UNCHANGED << net, QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_243_5(self) == /\ pc[self] = "Label_243_5"
                     /\ Len(net[((ABrokerIns[pID_ABro[self]].me))][("publish_resp")]) > 0
                     /\ req_AB' = [req_AB EXCEPT ![self] = Head(net[((ABrokerIns[pID_ABro[self]].me))][("publish_resp")])]
                     /\ net' = [net EXCEPT ![((ABrokerIns[pID_ABro[self]].me))][("publish_resp")] = Tail(net[((ABrokerIns[pID_ABro[self]].me))][("publish_resp")])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_243_5"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

ABrokerHandlePuback(self) == Label_242_5(self) \/ Label_243_5(self)

Label_252_5(self) == /\ pc[self] = "Label_252_5"
                     /\ req_ABr' = [req_ABr EXCEPT ![self] = [__reserved |-> 0]]
                     /\ resp_AB' = [resp_AB EXCEPT ![self] = [Sender |-> ABrokerIns[pID_ABrok[self]].me, Type |-> ""]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_254_5"]
                     /\ UNCHANGED << net, QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_254_5(self) == /\ pc[self] = "Label_254_5"
                     /\ Len(net[((ABrokerIns[pID_ABrok[self]].me))][("pubrel")]) > 0
                     /\ req_ABr' = [req_ABr EXCEPT ![self] = Head(net[((ABrokerIns[pID_ABrok[self]].me))][("pubrel")])]
                     /\ net' = [net EXCEPT ![((ABrokerIns[pID_ABrok[self]].me))][("pubrel")] = Tail(net[((ABrokerIns[pID_ABrok[self]].me))][("pubrel")])]
                     /\ ABrokerIns' = [ABrokerIns EXCEPT ![pID_ABrok[self]].waitREL = DelElement(ABrokerIns[pID_ABrok[self]].waitREL, req_ABr'[self].Sender)]
                     /\ resp_AB' = [resp_AB EXCEPT ![self].Type = "PUBCOMP"]
                     /\ pc' = [pc EXCEPT ![self] = "Label_258_9"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_258_9(self) == /\ pc[self] = "Label_258_9"
                     /\ net' = [net EXCEPT ![((req_ABr[self].Sender))][("pubrel_resp")] = Append(net[((req_ABr[self].Sender))][("pubrel_resp")], resp_AB[self])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_254_5"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

ABrokerHandlePubrel(self) == Label_252_5(self) \/ Label_254_5(self)
                                \/ Label_258_9(self)

Label_266_5(self) == /\ pc[self] = "Label_266_5"
                     /\ req_ABro' = [req_ABro EXCEPT ![self] = [__reserved |-> 0]]
                     /\ resp_ABr' = [resp_ABr EXCEPT ![self] = [Sender |-> ABrokerIns[pID_ABroke[self]].me, Type |-> ""]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_268_5"]
                     /\ UNCHANGED << net, QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_268_5(self) == /\ pc[self] = "Label_268_5"
                     /\ Len(net[((ABrokerIns[pID_ABroke[self]].me))][("subscribe")]) > 0
                     /\ req_ABro' = [req_ABro EXCEPT ![self] = Head(net[((ABrokerIns[pID_ABroke[self]].me))][("subscribe")])]
                     /\ net' = [net EXCEPT ![((ABrokerIns[pID_ABroke[self]].me))][("subscribe")] = Tail(net[((ABrokerIns[pID_ABroke[self]].me))][("subscribe")])]
                     /\ ABrokerIns' = [ABrokerIns EXCEPT ![pID_ABroke[self]].TopicPool = AddSubscriber(ABrokerIns[pID_ABroke[self]].TopicPool, req_ABro'[self].Topic, req_ABro'[self].Sender)]
                     /\ resp_ABr' = [resp_ABr EXCEPT ![self].Type = "SUBACK"]
                     /\ pc' = [pc EXCEPT ![self] = "Label_272_9"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

Label_272_9(self) == /\ pc[self] = "Label_272_9"
                     /\ net' = [net EXCEPT ![((req_ABro[self].Sender))][("subscribe_resp")] = Append(net[((req_ABro[self].Sender))][("subscribe_resp")], resp_ABr[self])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_268_5"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

ABrokerHandleSubscribe(self) == Label_266_5(self) \/ Label_268_5(self)
                                   \/ Label_272_9(self)

Label_280_5(self) == /\ pc[self] = "Label_280_5"
                     /\ req' = [req EXCEPT ![self] = [__reserved |-> 0]]
                     /\ resp' = [resp EXCEPT ![self] = [Sender |-> ABrokerIns[pID_ABroker[self]].me, Type |-> ""]]
                     /\ pc' = [pc EXCEPT ![self] = "Label_282_5"]
                     /\ UNCHANGED << net, QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, pMap, pID_ABroker >>

Label_282_5(self) == /\ pc[self] = "Label_282_5"
                     /\ Len(net[((ABrokerIns[pID_ABroker[self]].me))][("unsubscribe")]) > 0
                     /\ req' = [req EXCEPT ![self] = Head(net[((ABrokerIns[pID_ABroker[self]].me))][("unsubscribe")])]
                     /\ net' = [net EXCEPT ![((ABrokerIns[pID_ABroker[self]].me))][("unsubscribe")] = Tail(net[((ABrokerIns[pID_ABroker[self]].me))][("unsubscribe")])]
                     /\ ABrokerIns' = [ABrokerIns EXCEPT ![pID_ABroker[self]].TopicPool = RemoveSubscriber(ABrokerIns[pID_ABroker[self]].TopicPool, req'[self].Topic, req'[self].Sender)]
                     /\ resp' = [resp EXCEPT ![self].Type = "UNSUBACK"]
                     /\ pc' = [pc EXCEPT ![self] = "Label_286_9"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, pMap, pID_ABroker >>

Label_286_9(self) == /\ pc[self] = "Label_286_9"
                     /\ net' = [net EXCEPT ![((req[self].Sender))][("unsubscribe_resp")] = Append(net[((req[self].Sender))][("unsubscribe_resp")], resp[self])]
                     /\ pc' = [pc EXCEPT ![self] = "Label_282_5"]
                     /\ UNCHANGED << QoS, instream, outstream, log, __call_stack, __path, APublisherIns, ASubscriberIns, ABrokerIns, stack, name_, pID__, respMsg__, reqMsg, __Profile_, name, pID, respMsg, __Profile, qos, msgContent, reqMsg_, respMsg_, pMap_, pID_, reqMsg_A, respMsg_A, msg, pMap_A, pID_A, req_, resp_, pMap_AB, pID_AB, req_A, resp_A, pubMsg, clients, i, n, pMap_ABr, pID_ABr, req_AB, pMap_ABro, pID_ABro, req_ABr, resp_AB, pMap_ABrok, pID_ABrok, req_ABro, resp_ABr, pMap_ABroke, pID_ABroke, req, resp, pMap, pID_ABroker >>

ABrokerHandleUnsubscribe(self) == Label_280_5(self) \/ Label_282_5(self)
                                     \/ Label_286_9(self)

(* Allow infinite stuttering to prevent deadlock on termination. *)
Terminating == /\ \A self \in ProcSet: pc[self] = "Done"
               /\ UNCHANGED vars

Next == (\E self \in ProcSet:  \/ __APublisher_Publish(self)
                               \/ __ASubscriber_Subscribe(self))
           \/ (\E self \in {"2Main"}: APublisherMain(self))
           \/ (\E self \in {"4Main"}: ASubscriberMain(self))
           \/ (\E self \in {"1HandleConn"}: ABrokerHandleConn(self))
           \/ (\E self \in {"1HandlePublish"}: ABrokerHandlePublish(self))
           \/ (\E self \in {"1HandlePuback"}: ABrokerHandlePuback(self))
           \/ (\E self \in {"1HandlePubrel"}: ABrokerHandlePubrel(self))
           \/ (\E self \in {"1HandleSubscribe"}: ABrokerHandleSubscribe(self))
           \/ (\E self \in {"1HandleUnsubscribe"}: ABrokerHandleUnsubscribe(self))
           \/ Terminating

Spec == Init /\ [][Next]_vars

Termination == <>(\A self \in ProcSet: pc[self] = "Done")

\* END TRANSLATION 
=============================================================================
