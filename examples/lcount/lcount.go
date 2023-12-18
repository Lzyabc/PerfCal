package lcount

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

type CounterState struct {
}

func (CounterIns *CounterState) CounterMain(ienv stdp.PInterface) (err error) {
	sum := int64(0)
	i := int64(1)
	n := int64(0)
	globalInput8, err := ienv.Read("input")

	n = globalInput8.AsNumber()
	for i <= n {
		sum = sum + i
		i = i + 1
	}
	err = ienv.Write("output", tla.MakeTLANumber(int(sum)))
	return
}

func Counter() stdp.Profile {
	var CounterIns *CounterState = &CounterState{}
	return stdp.Profile{
		Name:      "Counter",
		Main:      CounterIns.CounterMain,
		State:     CounterIns,
		Processes: []stdp.Proc{CounterIns.CounterMain},
	}
}

func init() {
}
