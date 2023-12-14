// An example of MQTT client
package mqtt

import (
	"fmt"
	"log"
	"os"
	"sort"
	"stdp"
	"strconv"
	"sync"
	"time"

	"github.com/UBC-NSS/pgo/distsys"
	"github.com/UBC-NSS/pgo/distsys/resources"
	"github.com/UBC-NSS/pgo/distsys/tla"
)

func NewClient(requestNum int, pubNum int, subNum int, QoS int, valueSize int, brokerIP string, clientIP string) {
	flagFile, _ := os.Create("/tmp/program_running.flag")
	flagFile.Close()
	defer func() {
		os.Remove("/tmp/program_running.flag")
	}()

	routeTable := GetRouteTable(brokerIP, clientIP)
	chNames := []string{"publish", "publish_resp", "pushback", "connect", "connect_resp", "pubrel", "pubrel_resp", "subscribe", "subscribe_resp", "unsubscribe", "unsubscribe_resp"}
	inStreamCh := make(chan tla.TLAValue, requestNum)
	outStreamCh := make(chan tla.TLAValue, requestNum)
	logCh := make(chan tla.TLAValue, requestNum*subNum)
	inStreamRes := resources.NewInputChan(inStreamCh)
	outStreamRes := resources.NewOutputCChan(outStreamCh)
	logRes := resources.NewOutputCChan(logCh)

	// start sub
	for i := 1 + pubNum; i <= pubNum+subNum; i++ {
		sub := stdp.NewEnv(
			tla.MakeTLANumber(i),
			ASubscriber(),
			stdp.BindVars("net", resources.NewMultiRPCConn(&routeTable, true, GenPort(i), i, chNames)),
			// stdp.BindVars("outstream", outStreamRes),
			stdp.BindVars("log", logRes),
			stdp.BindVars("QoS", distsys.NewLocalArchetypeResource(tla.MakeTLANumber(QoS))),
			stdp.BindVars("lock", resources.NewMuxLock()),
		)
		defer sub.Stop()
		go sub.Start()
	}

	time.Sleep(1 * time.Second)

	// start pub
	for i := 1; i <= pubNum; i++ {
		pub := stdp.NewEnv(
			tla.MakeTLANumber(i),
			APublisher(),
			stdp.BindVars("net", resources.NewMultiRPCConn(&routeTable, true, GenPort(i), i, chNames)),
			stdp.BindVars("instream", inStreamRes),
			stdp.BindVars("outstream", outStreamRes),
			stdp.BindVars("log", logRes),
			stdp.BindVars("QoS", distsys.NewLocalArchetypeResource(tla.MakeTLANumber(QoS))),
			stdp.BindVars("lock", resources.NewMuxLock()),
		)
		defer pub.Stop()
		go pub.Start()
	}

	time.Sleep(2 * time.Second)
	// latencyAll := make([]int, requestNum*subNum)
	latencyAllCh := make(chan []int, 1)
	var wg sync.WaitGroup
	go func(lCh chan []int) {
		latencyAll := make([]int, requestNum*subNum)
		for i := 0; i < requestNum*subNum; i++ {
			resp := <-logCh
			timeStampStr := resp.AsString()[:19]
			// fmt.Println("i", i)
			go func(i int, timeStampStr string) {
				defer wg.Done()
				wg.Add(1)
				sentTime, _ := strconv.ParseInt(timeStampStr, 10, 64)
				latency := time.Now().UnixNano() - sentTime
				latencyAll[i] = int(latency / 1000)
			}(i, timeStampStr)
		}
		lCh <- latencyAll

	}(latencyAllCh)

	rawMsg := RandomString(valueSize - 20)
	start := time.Now()
	// go func(inStreamCh chan tla.TLAValue) {
	for i := 0; i < requestNum; i++ {
		msg := fmt.Sprintf("%d %s", time.Now().UnixNano(), rawMsg)
		inStreamCh <- tla.MakeTLAString(msg)
		time.Sleep(10 * time.Millisecond)
	}
	// }(inStreamCh)

	endCh := make(chan time.Time, 1)
	go func(endCh chan time.Time) {
		for len(inStreamCh) > 0 {
			time.Sleep(10 * time.Microsecond)
			fmt.Println("len(inStreamCh)", len(inStreamCh))
		}
		endCh <- time.Now()
	}(endCh)
	end := <-endCh
	fmt.Println("Test finished", end.Sub(start))
	// create a wait group to wait for all the goroutines to finish
	wg.Wait()
	latencyAll := <-latencyAllCh
	// 启动测试
	// 排序并计算90%尾延迟
	sort.Ints(latencyAll)
	tailLatency := latencyAll[int(0.9*float64(len(latencyAll)))] // 90%尾延迟

	// 计算吞吐量
	throughput := float64(requestNum) / end.Sub(start).Seconds()
	output := fmt.Sprintf("%d,%d,%d,%d,%d\n", valueSize, pubNum, subNum, QoS, tailLatency)
	saveToFile("./latency.log", output)
	output = fmt.Sprintf("%d %d %d %d %d %f\n", requestNum, pubNum, subNum, valueSize, QoS, throughput)
	saveToFile("./throughput.log", output)
}

func saveToFile(fName string, output string) {
	file, err := os.OpenFile(fName, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()
	fmt.Println(output)
	if _, err := file.WriteString(output); err != nil {
		log.Fatal(err)
	}
}
