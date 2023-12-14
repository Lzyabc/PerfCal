package raft

import (
	"fmt"
	"stdp"
	"time"

	"github.com/UBC-NSS/pgo/distsys"
	"github.com/UBC-NSS/pgo/distsys/tla"
)

var _ = new(fmt.Stringer)
var _ = distsys.ErrDone
var _ = tla.TLAValue{}
var _ = stdp.ErrDone
var _ = time.Now

const Follower = 0
const Candidate = 1
const Leader = 2
const MaxServer = 3

type Command struct {
	Type  string
	Key   string
	Value string
	Idx   int
}
type ClientRequestArgs struct {
	Mcommand Command
	Msource  int
	Mdest    int
	Idx      int
}
type ClientRequestReply struct {
	Msuccess   bool
	Msource    int
	Mdest      int
	Idx        int
	LeaderHint int
	Value      string
}
type RequestVoteArgs struct {
	Mterm         int
	MlastLogTerm  int
	MlastLogIndex int
	Msource       int
	Mdest         int
}
type RequestVoteReply struct {
	Mterm   int
	Msource int
	Mgrant  bool
}
type AppendEntriesArgs struct {
	Mterm         int
	MprevLogIndex int
	MprevLogTerm  int
	Mlog          []LogEntry
	MleaderCommit int
	Msource       int
	Mdest         int
}
type AppendEntriesReply struct {
	Mterm       int
	Msource     int
	Msuccess    bool
	Mdest       int
	MmatchIndex int
}
type LogEntry struct {
	Mterm    int
	Mcommand Command
	Client   int
}
type ApplyMsg struct {
	McommandValid bool
	Mcommand      Command
	McommandIndex int
}
type AClientState struct {
	mleader int
	reqId   int
	me      int
}

type AServerState struct {
	currentTerm    int
	state          int
	votedFor       int
	commitIndex    int
	me             int
	mleader        int
	votesResponded *Set
	votesGranted   *Set
	logs           []LogEntry
	nextIndex      map[int]int
	matchIndex     map[int]int
	kvStore        map[string]string
}

func (AClientIns *AClientState) AClientInit(ienv stdp.PInterface) (err error) {
	globalSelf43, err := ienv.Read("self")
	for i := 0; i < 100 && err != nil; i++ {
		globalSelf43, err = ienv.Read("self")
		time.Sleep(10 * time.Second)
	}
	if err != nil {
		if err != nil {
			return err
		}

	}
	AClientIns.me = globalSelf43.AsNumber()
	AClientIns.mleader = 1
	globalSelf45, err := ienv.Read("self")
	for i := 0; i < 100 && err != nil; i++ {
		globalSelf45, err = ienv.Read("self")
		time.Sleep(10 * time.Second)
	}
	if err != nil {
		if err != nil {
			return err
		}

	}
	AClientIns.reqId = globalSelf45.AsNumber()
	// fmt.Println("in Client init", AClientIns.me)
	return
}

func (AClientIns *AClientState) AClientThreadpoolInit(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		output := []interface{}{}
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			err := AClientIns.AClientInit(ienv)
			output = append(output, err)
			outputs <- output
			output = []interface{}{}
		}
	}
}
func (AServerIns *AServerState) AServerSendRequestVote(ienv stdp.PInterface, req RequestVoteArgs, dest int) {
	var err error
	_ = err
	err = ienv.Write("net", tla.MakeTLAStruct(req), tla.MakeTLANumber(int(dest)), tla.MakeTLAString("RequestVote"))
	for i := 0; i < 100 && err != nil; i++ {
		err = ienv.Write("net", tla.MakeTLAStruct(req), tla.MakeTLANumber(int(dest)), tla.MakeTLAString("RequestVote"))
		time.Sleep(10 * time.Second)
	}
	if err != nil {

	}

}

func (AServerIns *AServerState) AServerThreadpoolSendRequestVote(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input
			req := input[0].(RequestVoteArgs)
			dest := input[1].(int)
			AServerIns.AServerSendRequestVote(ienv, req, dest)
		}
	}
}

func (AServerIns *AServerState) AServerResetElectionTimer(ienv stdp.PInterface) {
	var err error
	_ = err
	err = ienv.Write("electionTimeout", tla.MakeTLANumber(int(0.0)))
	for i := 0; i < 100 && err != nil; i++ {
		err = ienv.Write("electionTimeout", tla.MakeTLANumber(int(0.0)))
		time.Sleep(10 * time.Second)
	}
	if err != nil {

	}

}

func (AServerIns *AServerState) AServerThreadpoolResetElectionTimer(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			AServerIns.AServerResetElectionTimer(ienv)
		}
	}
}

func (AServerIns *AServerState) AServerResetHeartbeatTimer(ienv stdp.PInterface) {
	var err error
	_ = err
	err = ienv.Write("heartbeatTimeout", tla.MakeTLANumber(int(0.0)))
	for i := 0; i < 100 && err != nil; i++ {
		err = ienv.Write("heartbeatTimeout", tla.MakeTLANumber(int(0.0)))
		time.Sleep(10 * time.Second)
	}
	if err != nil {

	}

}

func (AServerIns *AServerState) AServerThreadpoolResetHeartbeatTimer(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			AServerIns.AServerResetHeartbeatTimer(ienv)
		}
	}
}

func (AServerIns *AServerState) AServerLastTerm(ienv stdp.PInterface) (lastTerm int) {
	var err error
	_ = err
	lastTerm = 0
	if len(AServerIns.logs) > 0 {
		lastTerm = AServerIns.logs[len(AServerIns.logs)-1].Mterm
	}

	return
}

func (AServerIns *AServerState) AServerThreadpoolLastTerm(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		output := []interface{}{}
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			lastTerm := AServerIns.AServerLastTerm(ienv)
			output = append(output, lastTerm)
			outputs <- output
			output = []interface{}{}
		}
	}
}

func (AServerIns *AServerState) AServerHandleAppendEntriesRequestFunc(ienv stdp.PInterface, req AppendEntriesArgs) {
	var err error
	_ = err
	resp := AppendEntriesReply{}
	ienv.Write("lock", "Acquire")
	if req.Mterm > AServerIns.currentTerm {
		AServerIns.currentTerm = req.Mterm
		AServerIns.votedFor = (-1)
		AServerIns.AServerBecomeFollower(ienv)
		AServerIns.mleader = req.Msource
	}

	success := bool(false)
	logOk := bool(false)
	needReply := bool(false)
	mIndex := int((-1))
	index := int(0)
	if req.MprevLogIndex < 0 || (req.MprevLogIndex < len(AServerIns.logs) && req.MprevLogIndex >= 0 && AServerIns.logs[req.MprevLogIndex].Mterm == req.MprevLogTerm) {
		logOk = true
		// fmt.Println(AServerIns.me, "log ok", len(AServerIns.logs), req.MprevLogIndex, req.MprevLogTerm, AServerIns.currentTerm)
	} else {
		logOk = false
		// fmt.Println(AServerIns.me, "log not ok with log length is", len(AServerIns.logs), "and req last index is", req.MprevLogIndex, req.MprevLogTerm, AServerIns.currentTerm)
	}
	if req.Mterm <= AServerIns.currentTerm {
		if req.Mterm < AServerIns.currentTerm || (req.Mterm == AServerIns.currentTerm && !logOk && AServerIns.state == Follower) {
			needReply = true
		} else if req.Mterm == AServerIns.currentTerm && AServerIns.state == Candidate {
			AServerIns.AServerBecomeFollower(ienv)
			success = true
		} else if req.Mterm == AServerIns.currentTerm && AServerIns.state == Follower && logOk {
			index = req.MprevLogIndex + 1
			if len(req.Mlog) == 0 || (len(req.Mlog) > 0 && index >= 0 && index < len(AServerIns.logs) && req.Mlog[0].Mterm == AServerIns.logs[index].Mterm) || (len(req.Mlog) > 0 && index == len(AServerIns.logs)) {
				AServerIns.logs = SubSeq(AServerIns.logs, 0, req.MprevLogIndex+1)
				AServerIns.logs = LogAppend(AServerIns.logs, req.Mlog)
				AServerIns.commitIndex = req.MleaderCommit
				success = true
				mIndex = req.MprevLogIndex + len(req.Mlog)
				// fmt.Println(AServerIns.me, "update logs", mIndex, len(AServerIns.logs))
				needReply = true
				tmpi := int(0)
				for tmpi < len(req.Mlog) {
					if req.Mlog[tmpi].Mcommand.Type == "Put" {
						AServerIns.kvStore[req.Mlog[tmpi].Mcommand.Key] = req.Mlog[tmpi].Mcommand.Value
					} else {
						AServerIns.kvStore[req.Mlog[tmpi].Mcommand.Key] = ""
					}
					tmpi = tmpi + 1
				}
			} else if len(req.Mlog) > 0 && len(AServerIns.logs) > index && index >= 0 && req.Mlog[0].Mterm != AServerIns.logs[index].Mterm {
				AServerIns.logs = SubSeq(AServerIns.logs, 0, len(AServerIns.logs)-1)
			}

		}

		ienv.Write("lock", "Release")
		if needReply {
			needReply = false
			resp = AppendEntriesReply{
				Mterm:       AServerIns.currentTerm,
				Msource:     AServerIns.me,
				Msuccess:    success,
				Mdest:       req.Msource,
				MmatchIndex: mIndex,
			}
			err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Msource, tla.MakeTLAString("AppendEntriesResponse"))
			for i := 0; i < 100 && err != nil; i++ {
				err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Msource, tla.MakeTLAString("AppendEntriesResponse"))
				time.Sleep(10 * time.Second)
			}
			if err != nil {

			}

			// fmt.Println(AServerIns.me, "send AppendEntriesResponse to", req.Msource, resp)
		}

	}

	return
}

func (AServerIns *AServerState) AServerThreadpoolHandleAppendEntriesRequestFunc(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input
			req := input[0].(AppendEntriesArgs)
			AServerIns.AServerHandleAppendEntriesRequestFunc(ienv, req)
		}
	}
}

func (AServerIns *AServerState) AServerApplyAndResponseClient(ienv stdp.PInterface, id int) {
	var err error
	_ = err
	success := bool(true)
	dest := int(AServerIns.logs[id].Client)
	idx := int(AServerIns.logs[id].Mcommand.Idx)
	resp := ClientRequestReply{}
	value := string("")
	if AServerIns.logs[id].Mcommand.Type == "Get" {
		value = AServerIns.kvStore[AServerIns.logs[id].Mcommand.Key]
	} else {
		AServerIns.kvStore[AServerIns.logs[id].Mcommand.Key] = AServerIns.logs[id].Mcommand.Value
	}
	resp = ClientRequestReply{
		Msuccess:   success,
		Msource:    AServerIns.me,
		Mdest:      dest,
		Idx:        idx,
		LeaderHint: AServerIns.me,
		Value:      value,
	}
	err = ienv.Write("net", tla.MakeTLAStruct(resp), tla.MakeTLANumber(int(dest)), tla.MakeTLAString("ClientRequestResponse"))
	for i := 0; i < 100 && err != nil; i++ {
		err = ienv.Write("net", tla.MakeTLAStruct(resp), tla.MakeTLANumber(int(dest)), tla.MakeTLAString("ClientRequestResponse"))
		time.Sleep(10 * time.Second)
	}
	if err != nil {

	}

	// fmt.Println(AServerIns.me, "send ClientRequestResponse to", dest, resp)
}

func (AServerIns *AServerState) AServerThreadpoolApplyAndResponseClient(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input
			id := input[0].(int)
			AServerIns.AServerApplyAndResponseClient(ienv, id)
		}
	}
}

func (AServerIns *AServerState) AServerAdvanceCommitIndex(ienv stdp.PInterface) (hasCommit bool) {
	var err error
	_ = err
	hasCommit = false
	i := int(AServerIns.commitIndex + 1)
	tmpCommitIndex := int(i)
	for i < len(AServerIns.logs) {
		if tmpCommitIndex == i {
			count := int(0)
			j := int(1)
			hasCommit = false
			for j <= MaxServer && !hasCommit {
				if AServerIns.matchIndex[j] >= i {
					count = count + 1
					if count > MaxServer/2 {
						AServerIns.commitIndex = i
						tmpCommitIndex = i
						hasCommit = true
						AServerIns.AServerApplyAndResponseClient(ienv, AServerIns.commitIndex)
						// fmt.Println(AServerIns.me, "update commitIndex", AServerIns.commitIndex)
					}

				}

				j = j + 1
			}
		}

		i = i + 1
	}
	return
}

func (AServerIns *AServerState) AServerThreadpoolAdvanceCommitIndex(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		output := []interface{}{}
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			hasCommit := AServerIns.AServerAdvanceCommitIndex(ienv)
			output = append(output, hasCommit)
			outputs <- output
			output = []interface{}{}
		}
	}
}

func (AServerIns *AServerState) AServerSendAppendEntry(ienv stdp.PInterface, req AppendEntriesArgs, dest int) {
	var err error
	_ = err
	err = ienv.Write("net", tla.MakeTLAStruct(req), tla.MakeTLANumber(int(dest)), tla.MakeTLAString("AppendEntries"))
	for i := 0; i < 100 && err != nil; i++ {
		err = ienv.Write("net", tla.MakeTLAStruct(req), tla.MakeTLANumber(int(dest)), tla.MakeTLAString("AppendEntries"))
		time.Sleep(10 * time.Second)
	}
	if err != nil {

	}

}

func (AServerIns *AServerState) AServerThreadpoolSendAppendEntry(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input
			req := input[0].(AppendEntriesArgs)
			dest := input[1].(int)
			AServerIns.AServerSendAppendEntry(ienv, req, dest)
		}
	}
}

func (AServerIns *AServerState) AServerHandleAppendEntriesResponseFunc(ienv stdp.PInterface, resp AppendEntriesReply) {
	var err error
	_ = err
	ienv.Write("lock", "Acquire")
	if resp.Mterm > AServerIns.currentTerm {
		AServerIns.currentTerm = resp.Mterm
		AServerIns.AServerBecomeFollower(ienv)
		AServerIns.mleader = resp.Msource
		AServerIns.votedFor = (-1)
		AServerIns.AServerResetElectionTimer(ienv)
	} else if resp.Mterm == AServerIns.currentTerm {
		AServerIns.mleader = resp.Msource
		if resp.Msuccess {
			AServerIns.nextIndex[resp.Msource] = resp.MmatchIndex + 1
			AServerIns.matchIndex[resp.Msource] = resp.MmatchIndex
			// fmt.Println(AServerIns.me, "As leader update nextIndex when succ", AServerIns.nextIndex, AServerIns.matchIndex)
		} else {
			AServerIns.nextIndex[resp.Msource] = Max(0, AServerIns.nextIndex[resp.Msource]-1)
			// fmt.Println(AServerIns.me, "As leader update nextIndex when", resp.Msource, "failed", AServerIns.nextIndex, AServerIns.matchIndex)
		}
	}

	ienv.Write("lock", "Release")
}

func (AServerIns *AServerState) AServerThreadpoolHandleAppendEntriesResponseFunc(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input
			resp := input[0].(AppendEntriesReply)
			AServerIns.AServerHandleAppendEntriesResponseFunc(ienv, resp)
		}
	}
}

func (AServerIns *AServerState) AServerHandleClientRequest1(ienv stdp.PInterface) {
	var err error
	_ = err
	req := ClientRequestArgs{}
	entry := LogEntry{}
	for true {
		globalNet417, err := ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("ClientRequest"))

		for i := 0; i < 100 && err != nil; i++ {
			globalNet417, err = ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("ClientRequest"))

			time.Sleep(10 * time.Second)
		}
		if err != nil {

		}

		req = globalNet417.AsStruct().(ClientRequestArgs)
		// fmt.Println(AServerIns.me, "recv ClientRequest from", req.Msource, req.Mcommand)
		if AServerIns.state == Leader {
			ienv.Write("lock", "Acquire")
			entry = LogEntry{
				Mterm:    AServerIns.currentTerm,
				Mcommand: req.Mcommand,
				Client:   req.Msource,
			}
			AServerIns.logs = append(AServerIns.logs, entry)
			AServerIns.matchIndex[AServerIns.me] = len(AServerIns.logs) - 1
			AServerIns.nextIndex[AServerIns.me] = len(AServerIns.logs)
			ienv.Write("lock", "Release")
			AServerIns.AServerHeartbeat(ienv)
		} else {
			success := bool(false)
			// fmt.Println(AServerIns.me, "not leader", "mleader", AServerIns.mleader)
			resp := ClientRequestReply{
				Msuccess:   success,
				Msource:    AServerIns.me,
				Mdest:      req.Msource,
				Idx:        req.Mcommand.Idx,
				LeaderHint: AServerIns.mleader,
			}
			// fmt.Println(AServerIns.me, "sending ClientRequestResponse to", req.Msource, resp)
			err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Msource, tla.MakeTLAString("ClientRequestResponse"))
			for i := 0; i < 100 && err != nil; i++ {
				err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Msource, tla.MakeTLAString("ClientRequestResponse"))
				time.Sleep(10 * time.Second)
			}
			if err != nil {

			}

			// fmt.Println(AServerIns.me, "send ClientRequestResponse to", req.Msource, resp)
		}
	}
}

func (AServerIns *AServerState) AServerThreadpoolHandleClientRequest1(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			AServerIns.AServerHandleClientRequest1(ienv)
		}
	}
}

func (AServerIns *AServerState) AServerHandleClientRequestFunc(ienv stdp.PInterface, req ClientRequestArgs) {
	var err error
	_ = err
	entry := LogEntry{}
	if AServerIns.state == Leader {
		ienv.Write("lock", "Acquire")
		entry = LogEntry{
			Mterm:    AServerIns.currentTerm,
			Mcommand: req.Mcommand,
			Client:   req.Msource,
		}
		AServerIns.logs = append(AServerIns.logs, entry)
		AServerIns.matchIndex[AServerIns.me] = len(AServerIns.logs) - 1
		AServerIns.nextIndex[AServerIns.me] = len(AServerIns.logs)
		ienv.Write("lock", "Release")
		AServerIns.AServerHeartbeat(ienv)
	} else {
		success := bool(false)
		// fmt.Println(AServerIns.me, "not leader", "mleader", AServerIns.mleader)
		resp := ClientRequestReply{
			Msuccess:   success,
			Msource:    AServerIns.me,
			Mdest:      req.Msource,
			Idx:        req.Mcommand.Idx,
			LeaderHint: AServerIns.mleader,
		}
		// fmt.Println(AServerIns.me, "sending ClientRequestResponse to", req.Msource, resp)
		err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Msource, tla.MakeTLAString("ClientRequestResponse"))
		for i := 0; i < 100 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Msource, tla.MakeTLAString("ClientRequestResponse"))
			time.Sleep(10 * time.Second)
		}
		if err != nil {

		}

		// fmt.Println(AServerIns.me, "send ClientRequestResponse to", req.Msource, resp)
	}
}

func (AServerIns *AServerState) AServerThreadpoolHandleClientRequestFunc(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input
			req := input[0].(ClientRequestArgs)
			AServerIns.AServerHandleClientRequestFunc(ienv, req)
		}
	}
}

func (AServerIns *AServerState) AServerHeartbeat(ienv stdp.PInterface) {
	var err error
	_ = err
	SendAppendEntryThreadpool := stdp.Threadpool(ienv, AServerIns.AServerThreadpoolSendAppendEntry)
	AServerIns.AServerResetHeartbeatTimer(ienv)
	if AServerIns.state == Leader {
		i := int(1)
		ienv.Write("lock", "Acquire")
		for i <= MaxServer && AServerIns.state == Leader {
			if i != AServerIns.me {
				lastEntry := int(len(AServerIns.logs) - 1)
				prevLogIndex := int(AServerIns.nextIndex[i] - 1)
				prevLogTerm := int(0)
				entries := SubSeq(AServerIns.logs, AServerIns.nextIndex[i], lastEntry+1)
				if prevLogIndex >= 0 {
					prevLogTerm = AServerIns.logs[prevLogIndex].Mterm
				}

				// fmt.Println(AServerIns.me, "send AppendEntry to", i, "in term", AServerIns.currentTerm, "with lastEntry", lastEntry, "with prevLogIndex", prevLogIndex, AServerIns.nextIndex, len(AServerIns.logs))
				req := AppendEntriesArgs{
					Mterm:         AServerIns.currentTerm,
					MprevLogIndex: prevLogIndex,
					MprevLogTerm:  prevLogTerm,
					Mlog:          entries,
					MleaderCommit: Min(AServerIns.commitIndex, lastEntry),
					Msource:       AServerIns.me,
					Mdest:         i,
				}
				SendAppendEntryThreadpool.Send(req, i)
			}

			i = i + 1
		}
		i = 1
		ienv.Write("lock", "Release")
	}

}

func (AServerIns *AServerState) AServerThreadpoolHeartbeat(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			AServerIns.AServerHeartbeat(ienv)
		}
	}
}

func (AServerIns *AServerState) AServerBecomeLeader(ienv stdp.PInterface) {
	var err error
	_ = err
	AServerIns.state = Leader
	AServerIns.mleader = AServerIns.me
	// fmt.Println(AServerIns.me, "become leader")
	AServerIns.nextIndex = NewMap()
	AServerIns.matchIndex = NewMap()
	i := int(1)
	for i <= MaxServer {
		if i != AServerIns.me {
			AServerIns.nextIndex[i] = len(AServerIns.logs)
			AServerIns.matchIndex[i] = (-1)
		} else {
			AServerIns.nextIndex[i] = len(AServerIns.logs)
			AServerIns.matchIndex[i] = len(AServerIns.logs) - 1
		}
		i = i + 1
	}
}

func (AServerIns *AServerState) AServerThreadpoolBecomeLeader(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			AServerIns.AServerBecomeLeader(ienv)
		}
	}
}

func (AServerIns *AServerState) AServerBecomeFollower(ienv stdp.PInterface) {
	var err error
	_ = err
	AServerIns.state = Follower
	AServerIns.votedFor = (-1)
	AServerIns.mleader = (-1)
}

func (AServerIns *AServerState) AServerThreadpoolBecomeFollower(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			AServerIns.AServerBecomeFollower(ienv)
		}
	}
}

func (AServerIns *AServerState) AServerBecomeCandidate(ienv stdp.PInterface) {
	var err error
	_ = err
	AServerIns.state = Candidate
	AServerIns.votedFor = AServerIns.me
	AServerIns.votesResponded = NewSet(AServerIns.me)
	AServerIns.votesGranted = NewSet(AServerIns.me)
	AServerIns.currentTerm = AServerIns.currentTerm + 1
	AServerIns.mleader = (-1)
}

func (AServerIns *AServerState) AServerThreadpoolBecomeCandidate(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			AServerIns.AServerBecomeCandidate(ienv)
		}
	}
}

func (AServerIns *AServerState) AServerInit(ienv stdp.PInterface) (err error) {
	globalSelf673, err := ienv.Read("self")
	for i := 0; i < 100 && err != nil; i++ {
		globalSelf673, err = ienv.Read("self")
		time.Sleep(10 * time.Second)
	}
	if err != nil {
		if err != nil {
			return err
		}

	}
	AServerIns.me = globalSelf673.AsNumber()
	AServerIns.currentTerm = 0
	AServerIns.state = 0
	AServerIns.votedFor = (-1)
	AServerIns.commitIndex = (-1)
	AServerIns.mleader = (-1)
	AServerIns.kvStore = NewStore()
	AServerIns.AServerBecomeFollower(ienv)
	return
}

func (AServerIns *AServerState) AServerThreadpoolInit(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		output := []interface{}{}
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			err := AServerIns.AServerInit(ienv)
			output = append(output, err)
			outputs <- output
			output = []interface{}{}
		}
	}
}
func (AClientIns *AClientState) AClientMain(ienv stdp.PInterface) (err error) {
	cmd := Command{}
	ok := bool(false)
	nClient := int(0)
	t1 := int(0)
	latency := int(0)
	globalClientNum62, err := ienv.Read("clientNum")

	for i := 0; i < 100 && err != nil; i++ {
		globalClientNum62, err = ienv.Read("clientNum")

		time.Sleep(10 * time.Second)
	}
	if err != nil {

	}

	nClient = globalClientNum62.AsNumber()
	for true {
		globalReqCh64, err := ienv.Read("reqCh")

		for i := 0; i < 100 && err != nil; i++ {
			globalReqCh64, err = ienv.Read("reqCh")

			time.Sleep(10 * time.Second)
		}
		if err != nil {

		}

		cmd = globalReqCh64.AsStruct().(Command)
		AClientIns.reqId = AClientIns.reqId + nClient
		t1 = Time()
		for !ok {
			dest := int(AClientIns.mleader)
			cmd.Idx = AClientIns.reqId
			req := ClientRequestArgs{
				Mcommand: cmd,
				Msource:  AClientIns.me,
				Mdest:    dest,
			}
			err = ienv.Write("net", tla.MakeTLAStruct(req), tla.MakeTLANumber(int(dest)), tla.MakeTLAString("ClientRequest"))
			for i := 0; i < 100 && err != nil; i++ {
				err = ienv.Write("net", tla.MakeTLAStruct(req), tla.MakeTLANumber(int(dest)), tla.MakeTLAString("ClientRequest"))
				time.Sleep(10 * time.Second)
			}
			if err != nil {

			}

			// fmt.Println(AClientIns.me, "send ClientRequest to", dest, req)
			resp := ClientRequestReply{}
			globalNet80, err := ienv.Read("net", tla.MakeTLANumber(int(AClientIns.me)), tla.MakeTLAString("ClientRequestResponse"))

			for i := 0; i < 100 && err != nil; i++ {
				globalNet80, err = ienv.Read("net", tla.MakeTLANumber(int(AClientIns.me)), tla.MakeTLAString("ClientRequestResponse"))

				time.Sleep(10 * time.Second)
			}
			if err != nil {

			}

			resp = globalNet80.AsStruct().(ClientRequestReply)
			// fmt.Println(AClientIns.me, "recv ClientRequestResponse from", resp.Msource, resp)
			for resp.Idx != AClientIns.reqId {
				globalNet83, err := ienv.Read("net", tla.MakeTLANumber(int(AClientIns.me)), tla.MakeTLAString("ClientRequestResponse"))

				for i := 0; i < 100 && err != nil; i++ {
					globalNet83, err = ienv.Read("net", tla.MakeTLANumber(int(AClientIns.me)), tla.MakeTLAString("ClientRequestResponse"))

					time.Sleep(10 * time.Second)
				}
				if err != nil {

				}

				resp = globalNet83.AsStruct().(ClientRequestReply)
				// fmt.Println(AClientIns.me, "recv ClientRequestResponse from", resp.Msource, resp)
			}
			if resp.Msuccess {
				err = ienv.Write("respCh", tla.MakeTLAStruct(resp))
				for i := 0; i < 100 && err != nil; i++ {
					err = ienv.Write("respCh", tla.MakeTLAStruct(resp))
					time.Sleep(10 * time.Second)
				}
				if err != nil {

				}

				latency = Time() - t1
				err = ienv.Write("log", tla.MakeTLANumber(int(latency)))
				for i := 0; i < 100 && err != nil; i++ {
					err = ienv.Write("log", tla.MakeTLANumber(int(latency)))
					time.Sleep(10 * time.Second)
				}
				if err != nil {

				}

				ok = true
				// fmt.Println(AClientIns.me, "resp success", resp)
			} else {
				if resp.LeaderHint != (-1) {
					AClientIns.mleader = resp.LeaderHint
				}

				// fmt.Println(AClientIns.me, "resp fail", resp, "new leader", AClientIns.mleader)
			}
		}
		ok = false
	}
	return
}

func (AServerIns *AServerState) AServerHandleAppendEntriesRequest(ienv stdp.PInterface) (err error) {
	req := AppendEntriesArgs{}
	for true {
		globalNet250, err := ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("AppendEntries"))

		for i := 0; i < 100 && err != nil; i++ {
			globalNet250, err = ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("AppendEntries"))

			time.Sleep(10 * time.Second)
		}
		if err != nil {

		}

		req = globalNet250.AsStruct().(AppendEntriesArgs)
		if req.Mterm > AServerIns.currentTerm {
			AServerIns.currentTerm = req.Mterm
			AServerIns.votedFor = (-1)
			AServerIns.AServerBecomeFollower(ienv)
			AServerIns.mleader = req.Msource
		}

		if req.Mterm == AServerIns.currentTerm && AServerIns.state == Follower {
			AServerIns.AServerResetElectionTimer(ienv)
			AServerIns.mleader = req.Msource
		}

		if req.Mterm == AServerIns.currentTerm {
			AServerIns.AServerHandleAppendEntriesRequestFunc(ienv, req)
		}

	}
	return
}
func (AServerIns *AServerState) AServerAdvanceCommitIndexProc(ienv stdp.PInterface) (err error) {
	for true {
		ienv.Write("lock", "Acquire")
		AServerIns.AServerAdvanceCommitIndex(ienv)
		ienv.Write("lock", "Release")
	}
	return
}
func (AServerIns *AServerState) AServerHandleAppendEntriesResponse(ienv stdp.PInterface) (err error) {
	HandleAppendEntriesResponseFuncThreadpool := stdp.Threadpool(ienv, AServerIns.AServerThreadpoolHandleAppendEntriesResponseFunc)
	resp := AppendEntriesReply{}
	for true {
		// fmt.Println(AServerIns.me, "waitting recv AppendEntriesResponse.")
		globalNet360, err := ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("AppendEntriesResponse"))

		for i := 0; i < 100 && err != nil; i++ {
			globalNet360, err = ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("AppendEntriesResponse"))

			time.Sleep(10 * time.Second)
		}
		if err != nil {

		}

		resp = globalNet360.AsStruct().(AppendEntriesReply)
		// fmt.Println(AServerIns.me, "recv AppendEntriesResponse from", resp.Msource)
		HandleAppendEntriesResponseFuncThreadpool.Send(resp)
	}
	return
}
func (AServerIns *AServerState) AServerHandleClientRequest(ienv stdp.PInterface) (err error) {
	req := ClientRequestArgs{}
	HandleClientRequestFuncThreadpool := stdp.Threadpool(ienv, AServerIns.AServerThreadpoolHandleClientRequestFunc)
	for true {
		globalNet402, err := ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("ClientRequest"))

		for i := 0; i < 100 && err != nil; i++ {
			globalNet402, err = ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("ClientRequest"))

			time.Sleep(10 * time.Second)
		}
		if err != nil {

		}

		req = globalNet402.AsStruct().(ClientRequestArgs)
		// fmt.Println(AServerIns.me, "recv ClientRequest from", req.Msource, req.Mcommand)
		HandleClientRequestFuncThreadpool.Send(req)
	}
	return
}
func (AServerIns *AServerState) AServerPHeartbeat(ienv stdp.PInterface) (err error) {
	needHeartbeat := bool(false)
	for true {
		globalHeartbeatTimeout516, err := ienv.Read("heartbeatTimeout")

		for i := 0; i < 100 && err != nil; i++ {
			globalHeartbeatTimeout516, err = ienv.Read("heartbeatTimeout")

			time.Sleep(10 * time.Second)
		}
		if err != nil {

		}

		needHeartbeat = globalHeartbeatTimeout516.AsBool()
		_ = needHeartbeat
		AServerIns.AServerHeartbeat(ienv)
	}
	return
}
func (AServerIns *AServerState) AServerRequestVote(ienv stdp.PInterface) (err error) {
	i := int(1)
	needVotes := bool(true)
	election := bool(false)
	req := RequestVoteArgs{}
	// fmt.Println("In RequestVote", AServerIns.me)
	for true {
		globalElectionTimeout536, err := ienv.Read("electionTimeout")

		for i := 0; i < 100 && err != nil; i++ {
			globalElectionTimeout536, err = ienv.Read("electionTimeout")

			time.Sleep(10 * time.Second)
		}
		if err != nil {

		}

		election = globalElectionTimeout536.AsBool()
		_ = election
		AServerIns.AServerResetElectionTimer(ienv)
		ienv.Write("lock", "Acquire")
		if AServerIns.state != Leader {
			// fmt.Println(AServerIns.me, "electionTimeout")
			needVotes = true
			AServerIns.AServerBecomeCandidate(ienv)
			req = RequestVoteArgs{
				Mterm:         AServerIns.currentTerm,
				MlastLogTerm:  0.0,
				MlastLogIndex: 0.0,
				Msource:       AServerIns.votedFor,
				Mdest:         0.0,
			}
		}

		ienv.Write("lock", "Release")
		if needVotes {
			needVotes = false
			for i <= MaxServer {
				if i != AServerIns.me {
					AServerIns.AServerSendRequestVote(ienv, req, i)
				}

				i = i + 1
			}
			i = 1
		}

	}
	return
}
func (AServerIns *AServerState) AServerHandleRequestVoteRequest(ienv stdp.PInterface) (err error) {
	req := RequestVoteArgs{}
	resp := RequestVoteReply{}
	grant := bool(false)
	needResp := bool(false)
	for true {
		globalNet574, err := ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("RequestVote"))

		for i := 0; i < 100 && err != nil; i++ {
			globalNet574, err = ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("RequestVote"))

			time.Sleep(10 * time.Second)
		}
		if err != nil {

		}

		req = globalNet574.AsStruct().(RequestVoteArgs)
		ienv.Write("lock", "Acquire")
		if req.Mterm > AServerIns.currentTerm {
			AServerIns.currentTerm = req.Mterm
			AServerIns.AServerBecomeFollower(ienv)
			AServerIns.votedFor = (-1)
			AServerIns.AServerResetElectionTimer(ienv)
		}

		if req.Mterm == AServerIns.currentTerm {
			grant = (req.Mterm <= AServerIns.currentTerm && (AServerIns.votedFor == (-1) || AServerIns.votedFor == req.Msource))
			resp = RequestVoteReply{
				Mterm:   AServerIns.currentTerm,
				Msource: AServerIns.me,
				Mgrant:  grant,
			}
			needResp = true
			AServerIns.votedFor = req.Msource
		}

		ienv.Write("lock", "Release")
		if needResp {
			needResp = false
			err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Msource, tla.MakeTLAString("RequestVoteResponse"))
			for i := 0; i < 100 && err != nil; i++ {
				err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Msource, tla.MakeTLAString("RequestVoteResponse"))
				time.Sleep(10 * time.Second)
			}
			if err != nil {

			}

		}

	}
	return
}
func (AServerIns *AServerState) AServerHandleRequestVoteResponse(ienv stdp.PInterface) (err error) {
	resp := RequestVoteReply{}
	for true {
		globalNet606, err := ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("RequestVoteResponse"))

		for i := 0; i < 100 && err != nil; i++ {
			globalNet606, err = ienv.Read("net", tla.MakeTLANumber(int(AServerIns.me)), tla.MakeTLAString("RequestVoteResponse"))

			time.Sleep(10 * time.Second)
		}
		if err != nil {

		}

		resp = globalNet606.AsStruct().(RequestVoteReply)
		// fmt.Println(AServerIns.me, "recv RequestVoteResponse from", resp.Msource, resp.Mterm, AServerIns.currentTerm)
		if resp.Mterm > AServerIns.currentTerm {
			AServerIns.currentTerm = resp.Mterm
			AServerIns.AServerBecomeFollower(ienv)
		}

		if resp.Mterm == AServerIns.currentTerm && AServerIns.state == Candidate {
			if resp.Mgrant && !Contains(AServerIns.votesGranted, resp.Msource) {
				AServerIns.votesGranted = Add(AServerIns.votesGranted, resp.Msource)
			}

			if !Contains(AServerIns.votesResponded, resp.Msource) {
				AServerIns.votesResponded = Add(AServerIns.votesResponded, resp.Msource)
			}

			ienv.Write("lock", "Acquire")
			if Cardinality(AServerIns.votesGranted) > MaxServer/2 && AServerIns.state == Candidate && AServerIns.currentTerm == resp.Mterm {
				AServerIns.AServerBecomeLeader(ienv)
			}

			ienv.Write("lock", "Release")
			if Cardinality(AServerIns.votesResponded)-Cardinality(AServerIns.votesGranted) > MaxServer/2 {
				AServerIns.AServerBecomeFollower(ienv)
			}

		}

	}
	return
}
func (AServerIns *AServerState) AServerMain(ienv stdp.PInterface) (err error) {
	// fmt.Println(AServerIns.me, "loop")
	return
}

func AClient() stdp.Profile {
	var AClientIns *AClientState = &AClientState{}
	return stdp.Profile{
		Name:      "AClient",
		Main:      AClientIns.AClientMain,
		State:     AClientIns,
		Processes: []stdp.Proc{AClientIns.AClientMain},
		Init:      AClientIns.AClientInit,
	}
}
func AServer() stdp.Profile {
	var AServerIns *AServerState = &AServerState{}
	return stdp.Profile{
		Name:      "AServer",
		Main:      AServerIns.AServerMain,
		State:     AServerIns,
		Processes: []stdp.Proc{AServerIns.AServerHandleAppendEntriesRequest, AServerIns.AServerAdvanceCommitIndexProc, AServerIns.AServerHandleAppendEntriesResponse, AServerIns.AServerHandleClientRequest, AServerIns.AServerPHeartbeat, AServerIns.AServerRequestVote, AServerIns.AServerHandleRequestVoteRequest, AServerIns.AServerHandleRequestVoteResponse, AServerIns.AServerMain},
		Init:      AServerIns.AServerInit,
	}
}

func init() {
	tla.RegisterStruct(Command{})
	tla.RegisterStruct(ClientRequestArgs{})
	tla.RegisterStruct(ClientRequestReply{})
	tla.RegisterStruct(RequestVoteArgs{})
	tla.RegisterStruct(RequestVoteReply{})
	tla.RegisterStruct(AppendEntriesArgs{})
	tla.RegisterStruct(AppendEntriesReply{})
	tla.RegisterStruct(LogEntry{})
	tla.RegisterStruct(ApplyMsg{})
}
