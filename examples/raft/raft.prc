
#@retry 100 10s {
#@type int
const Follower = 0
const Candidate = 1
const Leader = 2
const MaxServer = 3


#@new struct Command {"Type": "string", "Key": "string", "Value": "string", "Idx": "int"}

#@new struct ClientRequestArgs {"Mcommand": "Command", "Msource": "int", "Mdest": "int", "Idx": "int"}
#@new struct ClientRequestReply {"Msuccess": "bool", "Msource": "int", "Mdest": "int", "Idx": "int", "LeaderHint": "int", "Value": "string"}

#@new struct RequestVoteArgs {"Mterm": "int", "MlastLogTerm": "int", "MlastLogIndex": "int", "Msource": "int", "Mdest": "int"}
#@new struct RequestVoteReply {"Mterm": "int", "Msource": "int", "Mgrant": "bool"}
#@new struct AppendEntriesArgs {"Mterm": "int", "MprevLogIndex": "int", "MprevLogTerm": "int", "Mlog": "[]LogEntry", "MleaderCommit": "int", "Msource": "int", "Mdest": "int"}
#@new struct AppendEntriesReply {"Mterm": "int", "Msource": "int", "Msuccess": "bool", "Mdest": "int", "MmatchIndex": "int"}
#@new struct LogEntry {"Mterm": "int", "Mcommand": "Command", "Client": "int"}

#@new struct ApplyMsg {"McommandValid": "bool", "Mcommand": "Command", "McommandIndex": "int"}

profile AClient(self, net, reqCh, respCh, clientNum, log) {
    #@type int { 
    mleader = 1
    reqId = 0
    me = 0
    #}

    #@type {"input":{}, "output":{"err": "error"}}
    func init() {
        me = self
        mleader = 1
        reqId = self
        print("in Client init", me)
        return 
    }

    proc main() {
        #@type Command 
        cmd = {}
        #@type bool
        ok = False
        #@type int {
        nClient = 0
        t1 = 0
        latency = 0
        #}
        clientNum.read(nClient)
        while True {
            reqCh.read(cmd)
            reqId = reqId + nClient
            t1 = Time()
            while !ok {
                #@type int 
                dest = mleader
                cmd.Idx = reqId
                #@type ClientRequestArgs
                req = {"Mcommand": cmd, "Msource": me, "Mdest": dest}
                net.write(req, dest, "ClientRequest")
                print(me, "send ClientRequest to", dest, req)
                #@type ClientRequestReply
                resp = {}
                net.read(resp, me, "ClientRequestResponse")
                print(me, "recv ClientRequestResponse from", resp.Msource, resp)
                while resp.Idx != reqId {
                    net.read(resp, me, "ClientRequestResponse")
                    print(me, "recv ClientRequestResponse from", resp.Msource, resp)
                }           
                if resp.Msuccess {
                    respCh.write(resp)
                    latency = Time()-t1
                    log.write(latency)
                    ok = True
                    print(me, "resp success", resp)
                } else {
                    if resp.LeaderHint != -1 {
                        mleader = resp.LeaderHint
                    } 
                    print(me, "resp fail", resp, "new leader", mleader)
                }
                # Sleep(1000)
            }
            ok = False
        }
    }

}


profile AServer(self, net, commandCh, applyCh, electionTimeout, heartbeatTimeout, stateMonitor) {
    #@type int {
        currentTerm = 0
        state = 0 # 0: follower, 1: candidate, 2: leader
        votedFor = -1
        commitIndex = -1
        me = 0
        mleader = -1
    #}
    #@type *Set {
        votesResponded = NewSet()
        votesGranted = NewSet()
    #}

    #@type []LogEntry {
    logs = NewLogEntry()
    #}

    #@type map[int]int {
    nextIndex = NewMap()
    matchIndex = NewMap()
    #}

    #@type map[string]string {
    kvStore = NewStore()
    #}

    #@type {"input": {"req": "RequestVoteArgs", "dest": "int"}}
    func SendRequestVote(req, dest) {
        #print(me, "send RequestVote to", dest)
        #@type RequestVoteArgs
        net.write(req, dest, "RequestVote")
    }

    func ResetElectionTimer() {
        electionTimeout.write(0)
    }

    #@type {}
    func ResetHeartbeatTimer() {
        heartbeatTimeout.write(0)
    }

    #@type {"output": {"lastTerm": "int"}}
    func LastTerm() {
        #@type int
        lastTerm = 0
        if Len(logs) > 0 {
            lastTerm = logs[Len(logs)-1].Mterm
        }
        return lastTerm
    }

    #@type {"input": {"req": "AppendEntriesArgs"}}
    func HandleAppendEntriesRequestFunc(req) {
        # print(me, "HandleAppendEntriesRequestFunc", req)
        #@type AppendEntriesReply
        resp = {}
        .AtomCheckTerm
        if req.Mterm > currentTerm {
            currentTerm = req.Mterm
            votedFor = -1
            BecomeFollower()
            mleader = req.Msource
        }

        #@type bool {
        success = False
        logOk = False
        needReply = False
        #}

        #@type int {
        mIndex = -1
        index = 0
        #}

        if req.MprevLogIndex < 0 || (req.MprevLogIndex < Len(logs) && req.MprevLogIndex >= 0 && logs[req.MprevLogIndex].Mterm == req.MprevLogTerm) {
            logOk = True
            print(me, "log ok", len(logs), req.MprevLogIndex, req.MprevLogTerm, currentTerm)
        } else {
            logOk = False
            print(me, "log not ok with log length is", len(logs), "and req last index is", req.MprevLogIndex, req.MprevLogTerm, currentTerm)
        }
        if req.Mterm <= currentTerm {
            if req.Mterm < currentTerm || (req.Mterm == currentTerm && !logOk && state == Follower) {
                needReply = True
            } elif req.Mterm == currentTerm && state == Candidate {
                BecomeFollower()
                success = True 
            } elif req.Mterm == currentTerm && state == Follower && logOk {
                index = req.MprevLogIndex + 1
                if Len(req.Mlog) == 0 || (Len(req.Mlog) > 0 && index >= 0 && index < Len(logs) && req.Mlog[0].Mterm == logs[index].Mterm) || (Len(req.Mlog) > 0 && index == Len(logs)) {
                    logs = SubSeq(logs, 0, req.MprevLogIndex+1)
                    logs = LogAppend(logs, req.Mlog)
                    #@type []LogEntry
                    commitIndex = req.MleaderCommit
                    # print(me, "update commitIndex", commitIndex)
                    success = True
                    mIndex = req.MprevLogIndex + Len(req.Mlog)
                    print(me, "update logs", mIndex, len(logs))
                    needReply = True
                    #@type int 
                    tmpi = 0
                    while tmpi < Len(req.Mlog) {
                        if req.Mlog[tmpi].Mcommand.Type == "Put" {
                            kvStore[req.Mlog[tmpi].Mcommand.Key] = req.Mlog[tmpi].Mcommand.Value
                        } else {
                            kvStore[req.Mlog[tmpi].Mcommand.Key] = ""
                        }
                        tmpi = tmpi + 1
                    }
                } elif Len(req.Mlog) > 0 && Len(logs) > index && index >= 0 && req.Mlog[0].Mterm != logs[index].Mterm {
                    logs = SubSeq(logs, 0, Len(logs)-1)
                }
            }
            .EndAtomCheckState
            if needReply {
                needReply = False
                resp = {"Mterm": currentTerm, "Msource": me, "Msuccess": success, "Mdest": req.Msource, "MmatchIndex": mIndex}
                net.write(resp, req.Msource, "AppendEntriesResponse")
                print(me, "send AppendEntriesResponse to", req.Msource, resp)
            }
        }
        return
    }


    proc HandleAppendEntriesRequest() {
        #@type AppendEntriesArgs
        req = {}
        # HandleAppendEntriesRequestFuncThreadpool = Threadpool(HandleAppendEntriesRequestFunc)        
        while True {
            net.read(req, me, "AppendEntries")
            # print(me, "recv AppendEntries from", req.Msource, req, req.MprevLogIndex)
            if req.Mterm > currentTerm {
                currentTerm = req.Mterm
                votedFor = -1
                BecomeFollower()
                mleader = req.Msource
            }
            if req.Mterm == currentTerm && state == Follower {
                ResetElectionTimer()
                mleader = req.Msource
            }
            if req.Mterm == currentTerm {
                # HandleAppendEntriesRequestFuncThreadpool.Send(req)
                HandleAppendEntriesRequestFunc(req)
            }
        }
    }

    #@type {"input":{"id": "int"}}
    func ApplyAndResponseClient(id) {
        #@type bool 
        success = True
        #@type int {
        dest = logs[id].Client
        idx = logs[id].Mcommand.Idx
        #}
        #@type ClientRequestReply {
        resp = {}
        #}

        #@type string 
        value = ""
        if logs[id].Mcommand.Type == "Get" {
            value = kvStore[logs[id].Mcommand.Key]
        } else {
            kvStore[logs[id].Mcommand.Key] = logs[id].Mcommand.Value
        }

        resp = {"Msuccess": success, "Msource": me, "Mdest": dest, "Idx": idx, "LeaderHint": me, "Value": value}
        net.write(resp, dest, "ClientRequestResponse")
        print(me, "send ClientRequestResponse to", dest, resp)
    }

    proc AdvanceCommitIndexProc() {
        while True {
            .AtomAdvance
            AdvanceCommitIndex()
            # Sleep(2)
            .EndAtomAdvance
        }
    }

    #@type {"output": {"hasCommit": "bool"}}
    func AdvanceCommitIndex() {
        #@type bool
        hasCommit = False 
        #@type int {
        i = commitIndex + 1
        tmpCommitIndex = i
        #}
        # print(me, "AdvanceCommitIndex", i, Len(logs), commitIndex)
        while i < Len(logs) {
            if tmpCommitIndex == i {
                #@type int {
                count = 0
                j = 1
                #}
                hasCommit = False
                while j <= MaxServer && !hasCommit {
                    if matchIndex[j] >= i {
                        count = count + 1
                        if count > MaxServer / 2 {
                            commitIndex = i
                            tmpCommitIndex = i
                            hasCommit = True
                            ApplyAndResponseClient(commitIndex)
                            print(me, "update commitIndex", commitIndex)
                        }
                    }
                    j = j + 1
                }
            }
            i = i + 1
        }
        return hasCommit
    }




    #@type {"input": {"req": "AppendEntriesArgs", "dest": "int"}}
    func SendAppendEntry(req, dest) {
        # print(me, "send AppendEntry to", dest, req)
        net.write(req, dest, "AppendEntries")
    }

    proc HandleAppendEntriesResponse() {
        HandleAppendEntriesResponseFuncThreadpool = Threadpool(HandleAppendEntriesResponseFunc)
        #@type AppendEntriesReply
        resp = {}
        while True {
            print(me, "waitting recv AppendEntriesResponse.")
            net.read(resp, me, "AppendEntriesResponse")
            print(me, "recv AppendEntriesResponse from", resp.Msource)
            HandleAppendEntriesResponseFuncThreadpool.Send(resp)
            # HandleAppendEntriesResponseFunc(resp)
        }
    }


    #@type {"input": {"resp": "AppendEntriesReply"}}
    func HandleAppendEntriesResponseFunc(resp) {
        .AtomCheckTerm
        if resp.Mterm > currentTerm {
            currentTerm = resp.Mterm
            BecomeFollower()
            mleader = resp.Msource
            votedFor = -1
            ResetElectionTimer()
        } elif resp.Mterm == currentTerm {
            mleader = resp.Msource
            if resp.Msuccess {
                nextIndex[resp.Msource] = resp.MmatchIndex + 1
                matchIndex[resp.Msource] = resp.MmatchIndex
                print(me, "As leader update nextIndex when succ", nextIndex, matchIndex)
                # AdvanceCommitIndex()
            } else {
                nextIndex[resp.Msource] = Max(0, nextIndex[resp.Msource]-1)
                print(me, "As leader update nextIndex when", resp.Msource, "failed", nextIndex, matchIndex)
            }
        }
        .EndAtomCheckTerm 
    }



    proc HandleClientRequest() {
        #@type ClientRequestArgs
        req = {}
        HandleClientRequestFuncThreadpool = Threadpool(HandleClientRequestFunc)

        while True {
            net.read(req, me, "ClientRequest")
            print(me, "recv ClientRequest from", req.Msource, req.Mcommand)
            HandleClientRequestFuncThreadpool.Send(req)
            # HandleClientRequestFunc(req)
        }
    }

    func HandleClientRequest1() {
        #@type ClientRequestArgs
        req = {}
        #@type LogEntry
        entry = {}
        while True {
            net.read(req, me, "ClientRequest")
            print(me, "recv ClientRequest from", req.Msource, req.Mcommand)
            if state == Leader {
                .AtomAddLog
                entry = {"Mterm": currentTerm, "Mcommand": req.Mcommand, "Client": req.Msource}
                logs = Append(logs, entry)
                matchIndex[me] = Len(logs) - 1
                nextIndex[me] = Len(logs)
                .Heartbeat
                heartbeat()
            } else {
                #@type bool 
                success = False
                print(me, "not leader", "mleader", mleader)
                #@type ClientRequestReply
                resp = {"Msuccess": success, "Msource": me, "Mdest": req.Msource, "Idx": req.Mcommand.Idx, "LeaderHint": mleader}
                print(me, "sending ClientRequestResponse to", req.Msource, resp)
                net.write(resp, req.Msource, "ClientRequestResponse")
                print(me, "send ClientRequestResponse to", req.Msource, resp)
            }
        }
    }

    #@type {"input": {"req": "ClientRequestArgs"}}
    func HandleClientRequestFunc(req) {
        #@type LogEntry
        entry = {}
        if state == Leader {
            .AtomAddLog
            entry = {"Mterm": currentTerm, "Mcommand": req.Mcommand, "Client": req.Msource}
            logs = Append(logs, entry)
            matchIndex[me] = Len(logs) - 1
            nextIndex[me] = Len(logs)
            .Heartbeat
            heartbeat()
        } else {
            #@type bool 
            success = False
            print(me, "not leader", "mleader", mleader)
            #@type ClientRequestReply
            resp = {"Msuccess": success, "Msource": me, "Mdest": req.Msource, "Idx": req.Mcommand.Idx, "LeaderHint": mleader}
            print(me, "sending ClientRequestResponse to", req.Msource, resp)
            net.write(resp, req.Msource, "ClientRequestResponse")
            print(me, "send ClientRequestResponse to", req.Msource, resp)
        }
    }


    #@type {}
    func heartbeat() {
        SendAppendEntryThreadpool = Threadpool(SendAppendEntry)
        ResetHeartbeatTimer()
        if state == Leader {
            #@type int
            i = 1
            .AtomCheckTerm
            while i <= MaxServer && state == Leader {
                if i != me {
                    #@type int {
                    # lastEntry = Min(Len(logs)-1, nextIndex[i])
                    lastEntry = Len(logs)-1
                    prevLogIndex = nextIndex[i]- 1
                    prevLogTerm = 0 
                    #}
                    #@type []LogEntry
                    entries = SubSeq(logs, nextIndex[i], lastEntry+1)
                    if prevLogIndex >= 0 {
                        prevLogTerm = logs[prevLogIndex].Mterm
                    }
                    print(me, "send AppendEntry to", i, "in term", currentTerm, "with lastEntry", lastEntry, "with prevLogIndex", prevLogIndex, nextIndex, len(logs))
                    #@type AppendEntriesArgs
                    req = {"Mterm": currentTerm, "MprevLogIndex": prevLogIndex, "MprevLogTerm": prevLogTerm,"Mlog": entries, "MleaderCommit": Min(commitIndex, lastEntry), "Msource": me, "Mdest": i}
                    # SendAppendEntry(req, i)

                    SendAppendEntryThreadpool.Send(req, i)
                }
                i = i + 1
            }
            i = 1
            .EndAtomCheck
        }
    }


    proc PHeartbeat() {
        #@type bool
        needHeartbeat = False
        while True {
            heartbeatTimeout.read(needHeartbeat)
            nop(needHeartbeat)
            heartbeat()
        }
    }

    proc RequestVote() {
        #@type int
        i = 1
        #@type bool {
        needVotes = True 
        election = False
        #}
        # SendRequestVoteThreadpool = Threadpool(SendRequestVote)
        #@type RequestVoteArgs
        req = {}
        print("In RequestVote", me)
        while True {
            electionTimeout.read(election)
            nop(election)
            ResetElectionTimer()
            .AtomCheck
            if state != Leader {
                print(me, "electionTimeout")
                needVotes = True
                BecomeCandidate()
                req = {"Mterm": currentTerm, "MlastLogTerm": 0, "MlastLogIndex": 0, "Msource": votedFor, "Mdest": 0}
            }
            # print("In RequestVote", me, "needVotes", needVotes)
            .CheckandVotes
            if (needVotes) {
                needVotes = False
                while i <= MaxServer {
                    if i != me {
                        # SendRequestVoteThreadpool.Send(req, i)
                        SendRequestVote(req, i)
                    }
                    i = i + 1
                }
                i = 1
            }
        }
    }

    proc HandleRequestVoteRequest() {
        #@type RequestVoteArgs
        req = {}
        #@type RequestVoteReply
        resp = {}        
        #@type bool  {
        grant = False
        needResp = False
        #}
        while True {
            net.read(req, me, "RequestVote")
            .AtomHandle
            # print(me, "reciv RequestVote from", req.Msource)
            if req.Mterm > currentTerm {
                currentTerm = req.Mterm
                BecomeFollower()
                votedFor = -1
                ResetElectionTimer()
            }
            if req.Mterm == currentTerm {
                grant = req.Mterm <= currentTerm && (votedFor == -1 || votedFor == req.Msource)
                #@type RequestVoteReply
                resp = {"Mterm": currentTerm, "Msource": me, "Mgrant": grant}
                needResp = True
                votedFor = req.Msource
            }
            .EndAtomHandle
            if needResp {
                needResp = False
                net.write(resp, req.Msource, "RequestVoteResponse")
                #print(me, "send RequestVoteResponse to", req.Msource, resp.Mgrant)
            }
        }
    }
    

    proc HandleRequestVoteResponse() {
        #@type RequestVoteReply
        resp = {}
        while True {
            net.read(resp, me, "RequestVoteResponse")
            print(me, "recv RequestVoteResponse from", resp.Msource, resp.Mterm, currentTerm)
            if resp.Mterm > currentTerm {
                currentTerm = resp.Mterm
                BecomeFollower()
            }
            if resp.Mterm == currentTerm && state == Candidate {
                if resp.Mgrant && !Contains(votesGranted, resp.Msource) {
                    votesGranted = Add(votesGranted, resp.Msource)
                }
                if !Contains(votesResponded, resp.Msource) {
                    votesResponded = Add(votesResponded, resp.Msource)
                }
                #print("current Cardinality", Cardinality(votesGranted))
                .AtomCheck
                if Cardinality(votesGranted) > MaxServer / 2  && state == Candidate && currentTerm == resp.Mterm {
                    BecomeLeader()
                } 
                .CheckandVotes
                if Cardinality(votesResponded) - Cardinality(votesGranted) > MaxServer / 2 {
                    BecomeFollower()
                }
            }
        }
    }

    func BecomeLeader() {
        state = Leader
        mleader = me
        print(me, "become leader")

        nextIndex = NewMap()
        matchIndex = NewMap()
        
        #@type int
        i = 1
        while i <= MaxServer {
            if i != me {
                nextIndex[i] = Len(logs)
                matchIndex[i] = -1
            } else {
                nextIndex[i] = Len(logs)
                matchIndex[i] = Len(logs) - 1
            }
            i = i + 1
        }
    }

    func BecomeFollower() {
        state = Follower
        votedFor = -1
        mleader = -1
    }

    func BecomeCandidate() {
        state = Candidate
        votedFor = me
        votesResponded = NewSet(me)
        votesGranted = NewSet(me)
        currentTerm = currentTerm + 1
        mleader = -1
    }

    #@type {"input":{}, "output":{"err": "error"}}
    func init() {
        me = self
        currentTerm = 0
        state = 0 # 0: follower, 1: candidate, 2: leader
        votedFor = -1
        commitIndex = -1
        mleader = -1
        kvStore = NewStore()

        #print(me, "init done")
        BecomeFollower()
        return
    }
}
#}
