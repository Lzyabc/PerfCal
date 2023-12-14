package hw

import (
	"fmt"
	"log"
	"sort"

	// "io/ioutil"
	"os"
	// "path"
	"math/rand"
	"stdp"
	"time"

	// "github.com/UBC-NSS/pgo/distsys"
	"github.com/UBC-NSS/pgo/distsys/resources"
	"github.com/UBC-NSS/pgo/distsys/tla"
)

func NewClient(clientNum int, requestNum int, valueSize int, clientIP, serverIP string) {
	// requestNum = 10
	flagFile, _ := os.Create("/tmp/program_running.flag")
	flagFile.Close()
	defer func() {
		os.Remove("/tmp/program_running.flag")
	}()

	responseChannel := make(chan tla.TLAValue, requestNum*clientNum)
	logCh := make(chan tla.TLAValue, requestNum*clientNum)
	logResource := resources.NewOutputCChan(logCh)

	curDir, err := os.Getwd()
	if err != nil {
		panic(err)
	}

	routeTable := GetRouteTable(serverIP, clientIP)

	chNames := []string{"Default", "req", "resp"}

	clients := make(map[int]*stdp.ProfileEnv)
	rand.Seed(time.Now().UnixNano())
	tStart := time.Now().UnixNano()
	for i := 1; i < clientNum+1; i++ {
		port := GenPort(i)
		requestCh := make(chan tla.TLAValue, requestNum)
		answerPathCh := make(chan tla.TLAValue, requestNum)
		envClient := stdp.NewEnv(
			tla.MakeTLANumber(i),
			AClient(),
			stdp.BindVars("net", resources.NewMultiRPCConn(&routeTable, true, port, i, chNames)),
			stdp.BindVars("instream", resources.NewInputChan(requestCh)),
			stdp.BindVars("stdPath", resources.NewInputChan(answerPathCh)),
			stdp.BindVars("fileSystem", resources.NewFileSystem(curDir)),
			stdp.BindVars("out", resources.NewOutputChan(responseChannel)),
			stdp.BindVars("log", logResource),
		)
		clients[i] = envClient
		go func(c *stdp.ProfileEnv) {
			defer c.Stop()
			go c.Start()

			startTime := time.Now()
			totalDuration := 30 * time.Second
			endTime := startTime.Add(totalDuration)

			for i := 0; i < requestNum; i++ {
				// 发送请求
				answerPath, submitPath := GetHW(valueSize)
				requestCh <- tla.MakeTLAString(submitPath)
				answerPathCh <- tla.MakeTLAString(answerPath)
				if i < requestNum-1 {
					remainingTime := endTime.Sub(time.Now())
					remainingRequests := requestNum - (i + 1)
					if remainingRequests > 0 && remainingTime > 0 {
						maxWait := remainingTime / time.Duration(remainingRequests)
						randomWait := time.Duration(rand.Int63n(int64(maxWait)))
						time.Sleep(randomWait)
					}
				}
			}
		}(envClient)
	}
	tSendEnd := time.Now().UnixNano()

	latencyAll := make([]int, requestNum*clientNum)
	for i := 0; i < requestNum*clientNum; i++ {
		latency := <-logCh
		latencyAll[i] = int(latency.AsNumber() / 1000)
		// if i%100 == 0 {
		// fmt.Println("receive i:", i)
		// }
	}
	tRecvEnd := time.Now().UnixNano()
	sort.Ints(latencyAll)
	latency := float64(latencyAll[int(0.9*float64(requestNum*clientNum))])
	throughput := float64(requestNum*clientNum) / (float64(tRecvEnd-tStart) / 1000000000)
	fmt.Println(clientNum, throughput, latency)

	fmt.Println("send time", (tSendEnd-tStart)/1000000, "ms", "recv time", (tRecvEnd-tStart)/1000000, "ms")
	close(responseChannel)
	time.Sleep(100 * time.Millisecond)

	output := fmt.Sprintf("%d %d %d %f %f\n", requestNum*clientNum, clientNum, valueSize, latency, throughput)
	saveToFile("./overview.log", output)
	output = ""
	for i := 0; i < 10; i++ {
		// output tail latency (10 points)
		idx := int(float64(requestNum*clientNum) * (float64(i+1) / 10))
		if idx >= requestNum*clientNum {
			idx = requestNum*clientNum - 1
		}
		output += fmt.Sprintf("%d ", latencyAll[idx])
	}
	output += "\n"
	saveToFile("./details.log", output)
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
