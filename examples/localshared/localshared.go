package localshared

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
const CONSUMER = 1

type ReqMsg struct {
	Message_type int64
	Client_id    int64
	Path         string
	Content      string
}
type QAnswer struct {
	Answers []string
}
type AClientState struct {
	num       int
	stdAnswer QAnswer
}

func (AClientIns *AClientState) AClientNewInc(ienv stdp.PInterface, a int) (b int) {
	var err error
	_ = err
	ienv.Write("lock", "Acquire")
	b = AClientIns.num + a
	// fmt.Println("num = ", AClientIns.num)
	ienv.Write("lock", "Release")
	return
}

func (AClientIns *AClientState) AClientActorNewInc(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		output := []interface{}{}
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input
			a := input[0].(int)
			b := AClientIns.AClientNewInc(ienv, a)
			output = append(output, b)
			outputs <- output
			output = []interface{}{}
		}
	}
}
func (AClientIns *AClientState) AClientInc(ienv stdp.PInterface) (err error) {
	n := int(1)
	ienv.Write("lock", "Acquire")
	AClientIns.num = AClientIns.AClientNewInc(ienv, n)
	// fmt.Println("num = ", AClientIns.num)
	// fmt.Println(CONSUMER)
	ienv.Write("lock", "Release")
	return
}
func (AClientIns *AClientState) AClientInc2(ienv stdp.PInterface) (err error) {
	n := int(1)
	ienv.Write("lock", "Acquire")
	AClientIns.num = AClientIns.num + n
	// fmt.Println("num = ", AClientIns.num)
	ienv.Write("lock", "Release")
	return
}
func (AClientIns *AClientState) AClientMain(ienv stdp.PInterface) (err error) {
	path := string("")
	for true {
		globalInstream62, err := ienv.Read("instream")

		for i := 0; i < 10 && err != nil; i++ {
			globalInstream62, err = ienv.Read("instream")

			time.Sleep(1 * time.Second)
		}
		path = globalInstream62.AsString()
		err = ienv.Write("out", path)
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("out", path)
			time.Sleep(1 * time.Second)
		}
	}
	return
}

func AClient() stdp.Profile {
	var AClientIns *AClientState = &AClientState{}
	return stdp.Profile{
		Name:      "AClient",
		Main:      AClientIns.AClientMain,
		State:     AClientIns,
		Processes: []stdp.Proc{AClientIns.AClientInc, AClientIns.AClientInc2, AClientIns.AClientMain},
	}
}

func init() {
	tla.RegisterStruct(ReqMsg{})
	tla.RegisterStruct(QAnswer{})
}
