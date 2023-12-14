package raft

import (
	"fmt"
	"stdp"

	"github.com/UBC-NSS/pgo/distsys"
	"github.com/UBC-NSS/pgo/distsys/resources"
	"github.com/UBC-NSS/pgo/distsys/tla"
)

func GetPort(i int) string {
	port := ""
	if i < 10 {
		port = fmt.Sprintf("800%d", i)
	} else if i < 100 {
		port = fmt.Sprintf("80%d", i)
	} else if i < 1000 {
		port = fmt.Sprintf("8%d", i)
	} else {
		port = fmt.Sprintf("%d", i+8000)
	}
	return port
}

// The following is an example of configuring a server.
// A user need configure the server according to the real environment.
func NewServer(id int, c Root) {
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

	stateMonitorCh := []chan tla.TLAValue{
		make(chan tla.TLAValue, 10),
		make(chan tla.TLAValue, 10),
		make(chan tla.TLAValue, 10),
		make(chan tla.TLAValue, 10),
	}

	stateMonitor := []distsys.ArchetypeResource{
		resources.NewOutputChan(stateMonitorCh[0]),
		resources.NewOutputChan(stateMonitorCh[1]),
		resources.NewOutputChan(stateMonitorCh[2]),
		resources.NewOutputChan(stateMonitorCh[3]),
	}

	LeaderTimeout := NewTimerResource(c.LeaderElection.Timeout, c.LeaderElection.TimeoutOffset)
	HeartbeatTimeout := NewTimerResource(c.AppendEntriesSendInterval, c.AppendEntriesSendInterval)
	server := stdp.NewEnv(
		tla.MakeTLANumber(int(id)),
		AServer(),
		stdp.BindVars("net", resources.NewMultiRPCConn(&routeTable, true, GetPort(id), id, chNames)),
		stdp.BindVars("electionTimeout", LeaderTimeout),
		stdp.BindVars("heartbeatTimeout", HeartbeatTimeout),
		stdp.BindVars("stateMonitor", stateMonitor[id]),
		stdp.BindVars("lock", resources.NewMuxLock()),
	)

	defer server.Stop()
	server.Start()
}
