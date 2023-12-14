package mqtt

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

const BrokerID = 0

type Message struct {
	Type    string
	Sender  int
	Topic   string
	QoS     int
	Content string
}
type APublisherState struct {
	me int
}

type ASubscriberState struct {
	me int
}

type ABrokerState struct {
	waitREL       *Set
	activeClients *Set
	TopicPool     *Pool
	me            int
}

func (APublisherIns *APublisherState) APublisherPublish(ienv stdp.PInterface, reqMsg Message) {
	var err error
	_ = err
	respMsg := Message{}
	if reqMsg.QoS == 0 {
		err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

	} else if reqMsg.QoS == 1 {
		// fmt.Println("Client", APublisherIns.me, "publishing", reqMsg, "to", BrokerID)
		err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		// fmt.Println("Client", APublisherIns.me, "published", reqMsg, "to", BrokerID)
		globalNet31, err := ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("publish_resp"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet31, err = ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("publish_resp"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		respMsg = globalNet31.AsStruct().(Message)
		// fmt.Println("Client", APublisherIns.me, "recived", respMsg)
		for respMsg.Type != "PUBACK" {
			err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish"))
			for i := 0; i < 10 && err != nil; i++ {
				err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish"))
				time.Sleep(1 * time.Second)
			}
			if err != nil {

			}

			globalNet35, err := ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("publish_resp"))

			for i := 0; i < 10 && err != nil; i++ {
				globalNet35, err = ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("publish_resp"))

				time.Sleep(1 * time.Second)
			}
			if err != nil {

			}

			respMsg = globalNet35.AsStruct().(Message)
			Sleep(10)
		}
	} else {
		err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		globalNet40, err := ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("publish_resp"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet40, err = ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("publish_resp"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		respMsg = globalNet40.AsStruct().(Message)
		for respMsg.Type != "PUBREC" {
			err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish"))
			for i := 0; i < 10 && err != nil; i++ {
				err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish"))
				time.Sleep(1 * time.Second)
			}
			if err != nil {

			}

			globalNet43, err := ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("publish_resp"))

			for i := 0; i < 10 && err != nil; i++ {
				globalNet43, err = ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("publish_resp"))

				time.Sleep(1 * time.Second)
			}
			if err != nil {

			}

			respMsg = globalNet43.AsStruct().(Message)
			Sleep(10)
		}
		reqMsg.Type = "PUBREL"
		err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("pubrel"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("pubrel"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		globalNet48, err := ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("pubrel_resp"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet48, err = ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("pubrel_resp"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		respMsg = globalNet48.AsStruct().(Message)
		for respMsg.Type != "PUBCOMP" {
			err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("pubrel_resp"))
			for i := 0; i < 10 && err != nil; i++ {
				err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("pubrel_resp"))
				time.Sleep(1 * time.Second)
			}
			if err != nil {

			}

			globalNet51, err := ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("pubrel"))

			for i := 0; i < 10 && err != nil; i++ {
				globalNet51, err = ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("pubrel"))

				time.Sleep(1 * time.Second)
			}
			if err != nil {

			}

			respMsg = globalNet51.AsStruct().(Message)
			Sleep(10)
		}
	}
	// fmt.Println("Client", APublisherIns.me, "published", respMsg)
	err = ienv.Write("outstream", tla.MakeTLAStruct(respMsg))
	for i := 0; i < 10 && err != nil; i++ {
		err = ienv.Write("outstream", tla.MakeTLAStruct(respMsg))
		time.Sleep(1 * time.Second)
	}
	if err != nil {

	}

}

func (APublisherIns *APublisherState) APublisherActorPublish(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input
			reqMsg := input[0].(Message)
			APublisherIns.APublisherPublish(ienv, reqMsg)
		}
	}
}

func (APublisherIns *APublisherState) APublisherInit(ienv stdp.PInterface) (err error) {
	globalSelf62, err := ienv.Read("self")
	for i := 0; i < 10 && err != nil; i++ {
		globalSelf62, err = ienv.Read("self")
		time.Sleep(1 * time.Second)
	}
	if err != nil {
		if err != nil {
			return err
		}

	}
	APublisherIns.me = globalSelf62.AsNumber()
	return
}

func (APublisherIns *APublisherState) APublisherActorInit(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		output := []interface{}{}
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			err := APublisherIns.APublisherInit(ienv)
			output = append(output, err)
			outputs <- output
			output = []interface{}{}
		}
	}
}
func (ASubscriberIns *ASubscriberState) ASubscriberInit(ienv stdp.PInterface) (err error) {
	globalSelf113, err := ienv.Read("self")
	for i := 0; i < 10 && err != nil; i++ {
		globalSelf113, err = ienv.Read("self")
		time.Sleep(1 * time.Second)
	}
	if err != nil {
		if err != nil {
			return err
		}

	}
	ASubscriberIns.me = globalSelf113.AsNumber()
	return
}

func (ASubscriberIns *ASubscriberState) ASubscriberActorInit(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		output := []interface{}{}
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			err := ASubscriberIns.ASubscriberInit(ienv)
			output = append(output, err)
			outputs <- output
			output = []interface{}{}
		}
	}
}

func (ASubscriberIns *ASubscriberState) ASubscriberSubscribe(ienv stdp.PInterface, reqMsg Message) {
	var err error
	_ = err
	respMsg := Message{}
	// fmt.Println("Subscriber", ASubscriberIns.me, "subscribing", reqMsg)
	err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("subscribe"))
	for i := 0; i < 10 && err != nil; i++ {
		err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("subscribe"))
		time.Sleep(1 * time.Second)
	}
	if err != nil {

	}

	// fmt.Println("Subscriber", ASubscriberIns.me, "waiting sub resp")
	globalNet126, err := ienv.Read("net", tla.MakeTLANumber(int(ASubscriberIns.me)), tla.MakeTLAString("subscribe_resp"))

	for i := 0; i < 10 && err != nil; i++ {
		globalNet126, err = ienv.Read("net", tla.MakeTLANumber(int(ASubscriberIns.me)), tla.MakeTLAString("subscribe_resp"))

		time.Sleep(1 * time.Second)
	}
	if err != nil {

	}

	respMsg = globalNet126.AsStruct().(Message)
	// fmt.Println("Subscriber", ASubscriberIns.me, "recived", respMsg)
	for respMsg.Type != "SUBACK" {
		err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("subscribe"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("subscribe"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		globalNet130, err := ienv.Read("net", tla.MakeTLANumber(int(ASubscriberIns.me)), tla.MakeTLAString("subscribe_resp"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet130, err = ienv.Read("net", tla.MakeTLANumber(int(ASubscriberIns.me)), tla.MakeTLAString("subscribe_resp"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		respMsg = globalNet130.AsStruct().(Message)
		Sleep(10)
	}
	// fmt.Println("Client", ASubscriberIns.me, "subscribe", respMsg)
	return
}

func (ASubscriberIns *ASubscriberState) ASubscriberActorSubscribe(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input
			reqMsg := input[0].(Message)
			ASubscriberIns.ASubscriberSubscribe(ienv, reqMsg)
		}
	}
}
func (ABrokerIns *ABrokerState) ABrokerInit(ienv stdp.PInterface) (err error) {
	ABrokerIns.waitREL = NewSet()
	ABrokerIns.activeClients = NewSet()
	ABrokerIns.TopicPool = NewPool()
	globalSelf191, err := ienv.Read("self")
	for i := 0; i < 10 && err != nil; i++ {
		globalSelf191, err = ienv.Read("self")
		time.Sleep(1 * time.Second)
	}
	if err != nil {
		if err != nil {
			return err
		}

	}
	ABrokerIns.me = globalSelf191.AsNumber()
	return
}

func (ABrokerIns *ABrokerState) ABrokerActorInit(ienv stdp.PInterface, ctrl chan int, inputs chan []interface{}, outputs chan []interface{}) {
	for {
		output := []interface{}{}
		select {
		case <-ctrl:
			return
		case input := <-inputs:
			_ = input

			err := ABrokerIns.ABrokerInit(ienv)
			output = append(output, err)
			outputs <- output
			output = []interface{}{}
		}
	}
}
func (APublisherIns *APublisherState) APublisherMain(ienv stdp.PInterface) (err error) {
	globalQoS68, err := ienv.Read("QoS")
	for i := 0; i < 10 && err != nil; i++ {
		globalQoS68, err = ienv.Read("QoS")
		time.Sleep(1 * time.Second)
	}
	if err != nil {

	}
	qos := int(globalQoS68.AsNumber())
	msgContent := string("")
	reqMsg := Message{
		Type:   "CONNET",
		Sender: APublisherIns.me,
	}
	respMsg := Message{
		Type: "",
	}
	err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("connect"))
	for i := 0; i < 10 && err != nil; i++ {
		err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("connect"))
		time.Sleep(1 * time.Second)
	}
	if err != nil {

	}

	globalNet81, err := ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("connect_resp"))

	for i := 0; i < 10 && err != nil; i++ {
		globalNet81, err = ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("connect_resp"))

		time.Sleep(1 * time.Second)
	}
	if err != nil {

	}

	respMsg = globalNet81.AsStruct().(Message)
	for respMsg.Type != "CONNACK" {
		err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("connect"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("connect"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		globalNet84, err := ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("connect_resp"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet84, err = ienv.Read("net", tla.MakeTLANumber(int(APublisherIns.me)), tla.MakeTLAString("connect_resp"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		respMsg = globalNet84.AsStruct().(Message)
		Sleep(10)
	}
	// fmt.Println("Client", APublisherIns.me, "connected")
	for true {
		// fmt.Println("Client", APublisherIns.me, "start publish")
		globalInstream93, err := ienv.Read("instream")

		for i := 0; i < 10 && err != nil; i++ {
			globalInstream93, err = ienv.Read("instream")

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		msgContent = globalInstream93.AsString()
		// fmt.Println("Client", APublisherIns.me, "publish", msgContent)
		reqMsg = Message{
			Type:    "PUBLISH",
			Sender:  APublisherIns.me,
			Content: msgContent,
			QoS:     qos,
			Topic:   "test",
		}
		APublisherIns.APublisherPublish(ienv, reqMsg)
	}
	return
}

func (ASubscriberIns *ASubscriberState) ASubscriberMain(ienv stdp.PInterface) (err error) {
	reqMsg := Message{
		Type:   "CONNET",
		Sender: ASubscriberIns.me,
	}
	respMsg := Message{
		Type: "",
	}
	for respMsg.Type != "CONNACK" {
		err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("connect"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(reqMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("connect"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		globalNet145, err := ienv.Read("net", tla.MakeTLANumber(int(ASubscriberIns.me)), tla.MakeTLAString("connect_resp"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet145, err = ienv.Read("net", tla.MakeTLANumber(int(ASubscriberIns.me)), tla.MakeTLAString("connect_resp"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		respMsg = globalNet145.AsStruct().(Message)
		Sleep(10)
	}
	reqMsg = Message{
		Type:   "SUBSCRIBE",
		Sender: ASubscriberIns.me,
		Topic:  "test",
	}
	// fmt.Println("Subscriber", ASubscriberIns.me, "sub to", reqMsg.Topic)
	ASubscriberIns.ASubscriberSubscribe(ienv, reqMsg)
	// fmt.Println("Subscriber", ASubscriberIns.me, "subed to", reqMsg.Topic)
	msg := Message{}
	for true {
		globalNet156, err := ienv.Read("net", tla.MakeTLANumber(int(ASubscriberIns.me)), tla.MakeTLAString("publish"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet156, err = ienv.Read("net", tla.MakeTLANumber(int(ASubscriberIns.me)), tla.MakeTLAString("publish"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		msg = globalNet156.AsStruct().(Message)
		if msg.Type == "PUBLISH" {
			// fmt.Println("Client", ASubscriberIns.me, "receive", msg)
			respMsg = Message{
				Type:   "PUBACK",
				Sender: ASubscriberIns.me,
			}
			err = ienv.Write("net", tla.MakeTLAStruct(respMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish_resp"))
			for i := 0; i < 10 && err != nil; i++ {
				err = ienv.Write("net", tla.MakeTLAStruct(respMsg), tla.MakeTLANumber(int(BrokerID)), tla.MakeTLAString("publish_resp"))
				time.Sleep(1 * time.Second)
			}
			if err != nil {

			}

			err = ienv.Write("log", msg.Content)
			for i := 0; i < 10 && err != nil; i++ {
				err = ienv.Write("log", msg.Content)
				time.Sleep(1 * time.Second)
			}
			if err != nil {

			}

		}

	}
	return
}

func (ABrokerIns *ABrokerState) ABrokerMain(ienv stdp.PInterface) (err error) {
	// fmt.Println("Broker start")
	return
}
func (ABrokerIns *ABrokerState) ABrokerHandleConn(ienv stdp.PInterface) (err error) {
	req := Message{}
	resp := Message{}
	for true {
		globalNet208, err := ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("connect"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet208, err = ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("connect"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		req = globalNet208.AsStruct().(Message)
		resp.Type = "CONNACK"
		// fmt.Println("Broker receive", req)
		ienv.Write("lock", "Acquire")
		ABrokerIns.activeClients.Add(req.Sender)
		ienv.Write("lock", "Release")
		// fmt.Println("Broker send", resp)
		err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("connect_resp"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("connect_resp"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		// fmt.Println("Broker send", resp)
	}
	return
}
func (ABrokerIns *ABrokerState) ABrokerHandlePublish(ienv stdp.PInterface) (err error) {
	req := Message{}
	resp := Message{
		Sender: ABrokerIns.me,
	}
	pubMsg := Message{
		Type:   "PUBLISH",
		Sender: ABrokerIns.me,
	}
	clients := []int{}
	for true {
		// fmt.Println("broker waitting published")
		globalNet234, err := ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("publish"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet234, err = ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("publish"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		req = globalNet234.AsStruct().(Message)
		clients = GetSubscribers(ABrokerIns.TopicPool, req.Topic)
		// fmt.Println("broker need published to", clients, "for", req)
		pubMsg = Message{
			Type:    "PUBLISH",
			Sender:  ABrokerIns.me,
			Content: req.Content,
			QoS:     req.QoS,
			Topic:   req.Topic,
		}
		i := int(0)
		n := int(len(clients))
		if req.QoS == 0 {
			for i < n {
				err = ienv.Write("net", tla.MakeTLAStruct(pubMsg), clients[i], tla.MakeTLAString("publish"))
				for i := 0; i < 10 && err != nil; i++ {
					err = ienv.Write("net", tla.MakeTLAStruct(pubMsg), clients[i], tla.MakeTLAString("publish"))
					time.Sleep(1 * time.Second)
				}
				if err != nil {

				}

				i = i + 1
			}
		} else if req.QoS == 1 {
			resp = Message{
				Sender: ABrokerIns.me,
				Type:   "PUBACK",
				QoS:    1.0,
			}
			// fmt.Println("broker waitting published to", clients, "for", req, "with n = ", n)
			for i < n {
				err = ienv.Write("net", tla.MakeTLAStruct(pubMsg), clients[i], tla.MakeTLAString("publish"))
				for i := 0; i < 10 && err != nil; i++ {
					err = ienv.Write("net", tla.MakeTLAStruct(pubMsg), clients[i], tla.MakeTLAString("publish"))
					time.Sleep(1 * time.Second)
				}
				if err != nil {

				}

				i = i + 1
			}
			// fmt.Println("broker published to", clients)
			err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("publish_resp"))
			for i := 0; i < 10 && err != nil; i++ {
				err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("publish_resp"))
				time.Sleep(1 * time.Second)
			}
			if err != nil {

			}

			// fmt.Println("broker resp to", req.Sender)
		} else if req.QoS == 2 {
			resp.Type = "PUBREC"
			for i < n {
				err = ienv.Write("net", tla.MakeTLAStruct(pubMsg), clients[i], tla.MakeTLAString("publish"))
				for i := 0; i < 10 && err != nil; i++ {
					err = ienv.Write("net", tla.MakeTLAStruct(pubMsg), clients[i], tla.MakeTLAString("publish"))
					time.Sleep(1 * time.Second)
				}
				if err != nil {

				}

				i = i + 1
			}
			err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("publish_resp"))
			for i := 0; i < 10 && err != nil; i++ {
				err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("publish_resp"))
				time.Sleep(1 * time.Second)
			}
			if err != nil {

			}

			ABrokerIns.waitREL.Add(req.Sender)
		}

	}
	return
}
func (ABrokerIns *ABrokerState) ABrokerHandlePuback(ienv stdp.PInterface) (err error) {
	req := Message{}
	for true {
		globalNet276, err := ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("publish_resp"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet276, err = ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("publish_resp"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		req = globalNet276.AsStruct().(Message)
		_ = req
	}
	return
}
func (ABrokerIns *ABrokerState) ABrokerHandlePubrel(ienv stdp.PInterface) (err error) {
	req := Message{}
	resp := Message{
		Sender: ABrokerIns.me,
	}
	for true {
		globalNet289, err := ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("pubrel"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet289, err = ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("pubrel"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		req = globalNet289.AsStruct().(Message)
		ABrokerIns.waitREL.Remove(req.Sender)
		resp.Type = "PUBCOMP"
		err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("pubrel_resp"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("pubrel_resp"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

	}
	return
}
func (ABrokerIns *ABrokerState) ABrokerHandleSubscribe(ienv stdp.PInterface) (err error) {
	req := Message{}
	resp := Message{
		Sender: ABrokerIns.me,
	}
	for true {
		// fmt.Println("broker waitting subscribe")
		globalNet304, err := ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("subscribe"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet304, err = ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("subscribe"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		req = globalNet304.AsStruct().(Message)
		// fmt.Println("broker recived", req)
		AddSubscriber(ABrokerIns.TopicPool, req.Topic, req.Sender)
		// fmt.Println("broker add", req.Sender, "to", req.Topic)
		resp.Type = "SUBACK"
		err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("subscribe_resp"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("subscribe_resp"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		// fmt.Println("broker resp", req.Sender)
	}
	return
}
func (ABrokerIns *ABrokerState) ABrokerHandleUnsubscribe(ienv stdp.PInterface) (err error) {
	req := Message{}
	resp := Message{
		Sender: ABrokerIns.me,
	}
	for true {
		globalNet322, err := ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("unsubscribe"))

		for i := 0; i < 10 && err != nil; i++ {
			globalNet322, err = ienv.Read("net", tla.MakeTLANumber(int(ABrokerIns.me)), tla.MakeTLAString("unsubscribe"))

			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

		req = globalNet322.AsStruct().(Message)
		RemoveSubscriber(ABrokerIns.TopicPool, req.Topic, req.Sender)
		resp.Type = "UNSUBACK"
		err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("unsubscribe_resp"))
		for i := 0; i < 10 && err != nil; i++ {
			err = ienv.Write("net", tla.MakeTLAStruct(resp), req.Sender, tla.MakeTLAString("unsubscribe_resp"))
			time.Sleep(1 * time.Second)
		}
		if err != nil {

		}

	}
	return
}

func APublisher() stdp.Profile {
	var APublisherIns *APublisherState = &APublisherState{}
	return stdp.Profile{
		Name:      "APublisher",
		Main:      APublisherIns.APublisherMain,
		State:     APublisherIns,
		Processes: []stdp.Proc{APublisherIns.APublisherMain},
		Init:      APublisherIns.APublisherInit,
	}
}
func ASubscriber() stdp.Profile {
	var ASubscriberIns *ASubscriberState = &ASubscriberState{}
	return stdp.Profile{
		Name:      "ASubscriber",
		Main:      ASubscriberIns.ASubscriberMain,
		State:     ASubscriberIns,
		Processes: []stdp.Proc{ASubscriberIns.ASubscriberMain},
		Init:      ASubscriberIns.ASubscriberInit,
	}
}
func ABroker() stdp.Profile {
	var ABrokerIns *ABrokerState = &ABrokerState{}
	return stdp.Profile{
		Name:      "ABroker",
		Main:      ABrokerIns.ABrokerMain,
		State:     ABrokerIns,
		Processes: []stdp.Proc{ABrokerIns.ABrokerMain, ABrokerIns.ABrokerHandleConn, ABrokerIns.ABrokerHandlePublish, ABrokerIns.ABrokerHandlePuback, ABrokerIns.ABrokerHandlePubrel, ABrokerIns.ABrokerHandleSubscribe, ABrokerIns.ABrokerHandleUnsubscribe},
		Init:      ABrokerIns.ABrokerInit,
	}
}

func init() {
	tla.RegisterStruct(Message{})
}
