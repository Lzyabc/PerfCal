package raft

import (
	"fmt"
	"stdp"

	"github.com/UBC-NSS/pgo/distsys"
	"github.com/UBC-NSS/pgo/distsys/resources"
	"github.com/UBC-NSS/pgo/distsys/tla"
)

// The following is an example of configuring a server.
// A user need configure the server according to the real environment.
func NewClient(clientNum int, requestNum int, initID int, c Root) (chan tla.TLAValue, chan tla.TLAValue, chan tla.TLAValue) {
	routeTable := resources.RouteMap{}
	for i := 1; i < 1000; i++ {
		if i < 10 {
			routeTable[i] = fmt.Sprintf("192.168.3.20:800%d", i)
		} else if i < 100 {
			routeTable[i] = fmt.Sprintf("192.168.3.20:80%d", i)
		} else if i < 1000 {
			routeTable[i] = fmt.Sprintf("192.168.3.20:8%d", i)
		} else {
			routeTable[i] = fmt.Sprintf("192.168.3.20:%d", i+8000)
		}
	}
	chNames := []string{"Default", "RequestVote", "RequestVoteResponse", "AppendEntries", "AppendEntriesResponse", "ClientRequest", "ClientRequestResponse"}

	clients := make(map[int]*stdp.ProfileEnv)

	NumClients := clientNum
	RequestNum := requestNum
	reqCh := make(chan tla.TLAValue, RequestNum)
	reqResource := resources.NewInputChan(reqCh)
	respCh := make(chan tla.TLAValue, RequestNum)
	respResource := resources.NewOutputCChan(respCh)
	logCh := make(chan tla.TLAValue, RequestNum)
	logResource := resources.NewOutputCChan(logCh)
	for i := initID; i < NumClients+initID; i++ {
		client := stdp.NewEnv(
			tla.MakeTLANumber(int(i)),
			AClient(),
			stdp.BindVars("net", resources.NewMultiRPCConn(&routeTable, true, GetPort(i), i, chNames)),
			stdp.BindVars("lock", resources.NewMuxLock()),
			stdp.BindVars("reqCh", reqResource),
			stdp.BindVars("respCh", respResource),
			stdp.BindVars("log", logResource),
			stdp.BindVars("clientNum", distsys.NewLocalArchetypeResource(tla.MakeTLANumber(NumClients))),
		)
		clients[i] = client
	}

	for _, client := range clients {
		defer client.Stop()
		go client.Start()
	}
	return reqCh, respCh, logCh
}
