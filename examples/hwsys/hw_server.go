package hw

import (
	"os"
	"stdp"
	"time"

	"github.com/UBC-NSS/pgo/distsys/resources"
	"github.com/UBC-NSS/pgo/distsys/tla"
)

func NewServer(clientIP, serverIP string) {
	curDir, err := os.Getwd()
	if err != nil {
		panic(err)
	}
	routeTable := GetRouteTable(serverIP, clientIP)
	chNames := []string{"Default", "req", "resp"}
	envServer := stdp.NewEnv(
		tla.MakeTLANumber(0),
		AServer(),
		stdp.BindVars("net", resources.NewMultiRPCConn(&routeTable, true, GenPort(0), 0, chNames)),
		stdp.BindVars("fileSystem", resources.NewFileSystem(curDir)),
		stdp.BindVars("json", NewJson()),
		stdp.BindVars("lock", resources.NewMuxLock()),
	)
	defer envServer.Stop()
	err = envServer.Start()
	if err != nil {
		panic(err)
		return
	}
	for {
		time.Sleep(1 * time.Second)
	}
}
