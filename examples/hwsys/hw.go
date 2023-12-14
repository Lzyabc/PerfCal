package hw

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

const PRODUCER = 0

type ReqMsg struct {
	Message_type int
	Request_id   int
	Client_id    int
	Path         string
	Content      string
}
type QAnswer struct {
	Answers []string
	Score   int
}
type AClientState struct {
}

type AServerState struct {
	kvStore map[int]int
	kvFlag  map[int]int
}

func (AServerIns *AServerState) AServerSaveFS(ienv stdp.PInterface, clientID int, requestID int, value int) {
	var err error
	_ = err
	ienv.Write("lock", "Acquire")
	flag := int(StoreGet(AServerIns.kvFlag, clientID))
	if flag < requestID {
		StoreSet(AServerIns.kvStore, clientID, value)
		StoreSet(AServerIns.kvFlag, clientID, requestID)
	}

	ienv.Write("lock", "Release")
}

func (AServerIns *AServerState) AServerThreadpoolSaveFS(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input
			clientID := input[0].(int)
			requestID := input[1].(int)
			value := input[2].(int)
			AServerIns.AServerSaveFS(ienv, clientID, requestID, value)
		}
	}
}

func (AServerIns *AServerState) AServerComputeScore(ienv stdp.PInterface, studentResponse QAnswer, stdAnswer QAnswer, responseID int, requestID int) {
	var err error
	_ = err
	feedBack := QAnswer{}
	res := string("")
	score := int(0)
	if len(stdAnswer.Answers) == len(studentResponse.Answers) {
		i := int(0)
		for i < len(stdAnswer.Answers) {
			if stdAnswer.Answers[i] != studentResponse.Answers[i] {
				feedBack.Answers = append(feedBack.Answers, "False")
				score = score + 1
			} else {
				feedBack.Answers = append(feedBack.Answers, "True")
			}
			i = i + 1
		}
	}

	feedBack.Score = score
	globalJson111, err := ienv.Read("json", tla.MakeTLAString("dump"), tla.MakeTLAStruct(feedBack), res)

	for i := 0; i < 10 && err != nil; i++ {
		globalJson111, err = ienv.Read("json", tla.MakeTLAString("dump"), tla.MakeTLAStruct(feedBack), res)

		time.Sleep(1 * time.Second)
	}
	if err != nil {

	}

	res = globalJson111.AsString()
	AServerIns.AServerSaveFS(ienv, responseID, requestID, score)
	err = ienv.Write("net", res, tla.MakeTLANumber(int(responseID)), tla.MakeTLAString("resp"))
	for i := 0; i < 10 && err != nil; i++ {
		err = ienv.Write("net", res, tla.MakeTLANumber(int(responseID)), tla.MakeTLAString("resp"))
		time.Sleep(1 * time.Second)
	}
	if err != nil {

	}

	return
}

func (AServerIns *AServerState) AServerThreadpoolComputeScore(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input
			studentResponse := input[0].(QAnswer)
			stdAnswer := input[1].(QAnswer)
			responseID := input[2].(int)
			requestID := input[3].(int)
			AServerIns.AServerComputeScore(ienv, studentResponse, stdAnswer, responseID, requestID)
		}
	}
}

func (AServerIns *AServerState) AServerInit(ienv stdp.PInterface) (err error) {
	AServerIns.kvFlag = NewStore()
	AServerIns.kvStore = NewStore()
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
	globalSelf17, err := ienv.Read("self")
	for i := 0; i < 10 && err != nil; i++ {
		globalSelf17, err = ienv.Read("self")
		time.Sleep(1 * time.Second)
	}
	if err != nil {

	}
	id := int(globalSelf17.AsNumber())
	path := string("")
	submit := string("")
	for true {
		submit = ""
		res := string("")
		globalInstream30, err := ienv.Read("instream")

		for i := 0; i < 10 && err != nil; i++ {
			globalInstream30, err = ienv.Read("instream")

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		path = globalInstream30.AsString()
		t1 := Time()
		globalFileSystem32, err := ienv.Read("fileSystem", path)

		for i := 0; i < 10 && err != nil; i++ {
			globalFileSystem32, err = ienv.Read("fileSystem", path)

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		submit = globalFileSystem32.AsString()
		reqMsg := ReqMsg{
			Message_type: 0.0,
			Request_id:   id,
			Client_id:    id,
			Path:         path,
			Content:      submit,
		}
		err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(PRODUCER)), tla.MakeTLAString("req"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(PRODUCER)), tla.MakeTLAString("req"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		globalNet38, err := ienv.Read("net", tla.MakeTLANumber(int(id)), tla.MakeTLAString("resp"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet38, err = ienv.Read("net", tla.MakeTLANumber(int(id)), tla.MakeTLAString("resp"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		res = globalNet38.AsString()
		latency := Time() - t1
		err = ienv.Write("log", latency)
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("log", latency)
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		err = ienv.Write("out", res)
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("out", res)
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

	}
	return
}

func (AServerIns *AServerState) AServerMain(ienv stdp.PInterface) (err error) {
	globalSelf120, err := ienv.Read("self")
	for i := 0; i < 10 && err != nil; i++ {
		globalSelf120, err = ienv.Read("self")
		time.Sleep(1 * time.Second)
	}
	if err != nil {

	}
	id := int(globalSelf120.AsNumber())
	answer := string("")
	computeScoreThreadpool := stdp.Threadpool(ienv, AServerIns.AServerThreadpoolComputeScore)
	req := ReqMsg{}
	studentResponse := QAnswer{}
	stdAnswer := QAnswer{}
	for true {
		globalNet137, err := ienv.Read("net", tla.MakeTLANumber(int(id)), tla.MakeTLAString("req"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet137, err = ienv.Read("net", tla.MakeTLANumber(int(id)), tla.MakeTLAString("req"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		req = globalNet137.AsStruct().(ReqMsg)
		globalJson139, err := ienv.Read("json", tla.MakeTLAString("load"), req.Content, tla.MakeTLAStruct(studentResponse))

		for i := 0; i < 10 && err != nil; i++ {
			globalJson139, err = ienv.Read("json", tla.MakeTLAString("load"), req.Content, tla.MakeTLAStruct(studentResponse))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		studentResponse = globalJson139.AsStruct().(QAnswer)
		globalFileSystem141, err := ienv.Read("fileSystem", req.Path)

		for i := 0; i < 10 && err != nil; i++ {
			globalFileSystem141, err = ienv.Read("fileSystem", req.Path)

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		answer = globalFileSystem141.AsString()
		globalJson142, err := ienv.Read("json", tla.MakeTLAString("load"), answer, tla.MakeTLAStruct(stdAnswer))

		for i := 0; i < 10 && err != nil; i++ {
			globalJson142, err = ienv.Read("json", tla.MakeTLAString("load"), answer, tla.MakeTLAStruct(stdAnswer))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		stdAnswer = globalJson142.AsStruct().(QAnswer)
		computeScoreThreadpool.Send(studentResponse, stdAnswer, req.Client_id, req.Request_id)
	}
	return
}

func AClient() stdp.Profile {
	var AClientIns *AClientState = &AClientState{}
	return stdp.Profile{
		Name:      "AClient",
		Main:      AClientIns.AClientMain,
		State:     AClientIns,
		Processes: []stdp.Proc{AClientIns.AClientMain},
	}
}
func AServer() stdp.Profile {
	var AServerIns *AServerState = &AServerState{}
	return stdp.Profile{
		Name:      "AServer",
		Main:      AServerIns.AServerMain,
		State:     AServerIns,
		Processes: []stdp.Proc{AServerIns.AServerMain},
		Init:      AServerIns.AServerInit,
	}
}

func init() {
	tla.RegisterStruct(ReqMsg{})
	tla.RegisterStruct(QAnswer{})
}
