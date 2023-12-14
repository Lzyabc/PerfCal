package mqtt

import (
	"fmt"
	"stdp"
	"time"

	"github.com/UBC-NSS/pgo/distsys/resources"
	"github.com/UBC-NSS/pgo/distsys/tla"
)

func NewBroker(brokerIP string, clientIP string) {
	chNames := []string{"publish", "publish_resp", "pushback", "connect", "connect_resp", "pubrel", "pubrel_resp", "subscribe", "subscribe_resp", "unsubscribe", "unsubscribe_resp"}
	routeTable := GetRouteTable(brokerIP, clientIP)
	fmt.Println("Starting Broker")

	broker := stdp.NewEnv(
		tla.MakeTLANumber(0),
		ABroker(),
		stdp.BindVars("net", resources.NewMultiRPCConn(&routeTable, true, "6000", 0, chNames)),
		stdp.BindVars("lock", resources.NewMuxLock()),
	)
	defer broker.Stop()
	broker.Start()
	for {
		time.Sleep(10 * time.Second)
	}
}
