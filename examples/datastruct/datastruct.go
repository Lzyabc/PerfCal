package datastruct

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

type Person struct {
	id        int64
	name      string
	relatives struct {
		father   string
		mother   string
		children struct {
			number int
		}
	}
}
type CounterState struct {
	input  int64
	output int64
}

func (CounterIns *CounterState) CounterMain(ienv stdp.PInterface) (err error) {
	// fmt.Println("hello")
	sum := int64(0)
	i := int64(1)
	n := int64(CounterIns.input)
	xiaoming := Person{
		id:   1.0,
		name: "xiaoming",
		relatives: struct {
			father   string
			mother   string
			children struct {
				number int
			}
		}{
			father: "xiaoming's father",
			mother: "xiaoming's mother",
			children: struct {
				number int
			}{
				number: 1.0,
			},
		},
	}
	partialSum := []int64{1, 2, 3}
	for i <= n {
		sum = sum + i
		i = i + 1
		partialSum = append(partialSum, sum)
	}
	// fmt.Println(xiaoming.name)
	// fmt.Println("id", xiaoming.id)
	n = partialSum[0]
	partialSum = []int64{2, 1}
	CounterIns.output = sum
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
	tla.RegisterStruct(Person{})
}
