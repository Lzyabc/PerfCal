
#@retry 10 1s {
#@type int
const BrokerID = 0

#@new struct Message {"Type": "string", "Sender": "int", "Topic": "string", "QoS": "int", "Content": "string"}

#@type {self: int, net: int, instream: int, outstream: int, QoS: int}
profile APublisher(self, QoS, net, instream, outstream, log) {
    #@type int
    me = 0

    #@type {"input": {"reqMsg": "Message"}}
    func Publish(reqMsg) {
         #@type Message
        respMsg = {}
        

        if reqMsg.QoS == 0 {
            net.write(reqMsg, BrokerID, "publish")
        } elif reqMsg.QoS == 1 {
            print("Client", me, "publishing", reqMsg, "to", BrokerID)
            net.write(reqMsg, BrokerID, "publish")
            print("Client", me, "published", reqMsg, "to", BrokerID)
            net.read(respMsg, me, "publish_resp")
            print("Client", me, "recived", respMsg)
            while respMsg.Type != "PUBACK" {
                net.write(reqMsg, BrokerID, "publish")
                net.read(respMsg, me, "publish_resp")
                Sleep(10)
            }
        } else {
            net.write(reqMsg, BrokerID, "publish")
            net.read(respMsg, me, "publish_resp")
            while respMsg.Type != "PUBREC" {
                net.write(reqMsg, BrokerID, "publish")
                net.read(respMsg, me, "publish_resp")
                Sleep(10)
            }
            reqMsg.Type = "PUBREL"
            net.write(reqMsg, BrokerID, "pubrel")
            net.read(respMsg, me, "pubrel_resp")
            while respMsg.Type != "PUBCOMP" {
                net.write(reqMsg, BrokerID, "pubrel_resp")
                net.read(respMsg, me, "pubrel")
                Sleep(10)
            }
        }
        print("Client", me, "published", respMsg)
        outstream.write(respMsg)
    }

    #@type {"input":{}, "output":{"err": "error"}}
    func init() {
        me = self
        return
    }

    proc main() {
        #@type int {
            qos = QoS
            # t1 = 0
        #}
        #@type string {
            msgContent = ""
        #}
        
        # 建立连接
        #@type Message {
        reqMsg = {"Type": "CONNET", "Sender": me}
        respMsg = {"Type": ""}
        #}
        net.write(reqMsg, BrokerID, "connect")
        net.read(respMsg, me, "connect_resp");
        while respMsg.Type != "CONNACK" {
            net.write(reqMsg, BrokerID, "connect")
            net.read(respMsg, me, "connect_resp");
            Sleep(10)
        } 
        print("Client", me, "connected")
        .c
        while (True) {
            .req
            # t1 = Time()
            print("Client", me, "start publish")
            instream.read(msgContent)
            print("Client", me, "publish", msgContent)
            #@type Message
            reqMsg = {"Type": "PUBLISH", "Sender": me, "Content": msgContent, "QoS": qos, "Topic": "test"}
            Publish(reqMsg)
        }
    }
}

#@type {self: int, net: int, outstream: int}
profile ASubscriber(self, net, outstream, log) {
    #@type int
    me = 0

    #@type {"input":{}, "output":{"err": "error"}}
    func init() {
        me = self
        return
    }

    #@type {"input": {"reqMsg": "Message"}}
    func Subscribe(reqMsg) {
        #@type Message
        respMsg = {}
        print("Subscriber", me, "subscribing", reqMsg)
        net.write(reqMsg, BrokerID, "subscribe")
        print("Subscriber", me, "waiting sub resp")
        net.read(respMsg, me, "subscribe_resp")
        print("Subscriber", me, "recived", respMsg)
        while respMsg.Type != "SUBACK" {
            net.write(reqMsg, BrokerID, "subscribe")
            net.read(respMsg, me, "subscribe_resp")
            Sleep(10)
        }
        print("Client", me, "subscribe", respMsg)
        return
    }


    proc main() {
        #@type Message {
        reqMsg = {"Type": "CONNET", "Sender": me}
        respMsg = {"Type": ""}
        #}
        while respMsg.Type != "CONNACK" {
            net.write(reqMsg, BrokerID, "connect")
            net.read(respMsg, me, "connect_resp");
            Sleep(10)
        } 
        reqMsg = {"Type": "SUBSCRIBE", "Sender": me, "Topic": "test"}
        print("Subscriber", me, "sub to", reqMsg.Topic)
        Subscribe(reqMsg)
        print("Subscriber", me, "subed to", reqMsg.Topic)
        #@type Message {
            msg = {}
        #}
        while (True) {
            net.read(msg, me, "publish")
            if msg.Type == "PUBLISH" {
                print("Client", me, "receive", msg)
                respMsg = {"Type": "PUBACK", "Sender": me}
                net.write(respMsg, BrokerID, "publish_resp")
                log.write(msg.Content)
            }
        }
    }
}



#@type {self: int, net: int}
profile ABroker(self, net) {
    #@type *Set {
    waitREL = NewSet()
    activeClients = NewSet()
    #}

    #@type *Pool {
        TopicPool = NewPool()
    #}

    #@type int 
    me = 0

    #@type {"input":{}, "output":{"err": "error"}}
    func init() {
        waitREL = NewSet()
        activeClients = NewSet()
        TopicPool = NewPool()
        me = self
        return
    }


    proc main() {
        print("Broker start")
    }

    proc HandleConn() {
        #@type Message {
            req = {}
            resp = {}
        #}
        .p
        while(True) {
            .req
            net.read(req, me, "connect");
            resp.Type = "CONNACK"
            print("Broker receive", req)
            .AtomAdd
            # activeClients = Add(activeClients, req.Sender)
            activeClients.Add(req.Sender)
            .AddEnd
            print("Broker send", resp)
            net.write(resp, req.Sender, "connect_resp")
            print("Broker send", resp)
        }
    }

    proc HandlePublish() {
        #@type Message {
            req = {}
            resp = {"Sender": me}
            pubMsg = {"Type": "PUBLISH", "Sender": me}
        #}
        #@type []int {
            clients = []
        #}
        .p
        while(True) {
            .req
            print("broker waitting published")
            net.read(req, me, "publish");
            clients = GetSubscribers(TopicPool, req.Topic)
            print("broker need published to", clients, "for", req)
            pubMsg = {"Type": "PUBLISH", "Sender": me, "Content": req.Content, "QoS": req.QoS, "Topic": req.Topic}

            #@type int {
            i = 0
            n = len(clients)
            #}
            if req.QoS == 0 {
                while i < n {
                    net.write(pubMsg, clients[i], "publish")
                    i = i + 1
                }
            } elif req.QoS == 1 {
                resp = {"Sender": me, "Type": "PUBACK", "QoS": 1}
                print("broker waitting published to", clients, "for", req, "with n = ", n)
                while i < n {
                    net.write(pubMsg, clients[i], "publish")
                    i = i + 1
                }
                print("broker published to", clients)
                net.write(resp, req.Sender, "publish_resp")
                print("broker resp to", req.Sender)
            } elif req.QoS == 2 {
                resp.Type = "PUBREC"
                while i < n {
                    net.write(pubMsg, clients[i], "publish")
                    i = i + 1
                }
                net.write(resp, req.Sender, "publish_resp")
                waitREL.Add(req.Sender)
            }
        }
    }
    proc HandlePuback() {
        #@type Message {
            req = {}
        #}
        .p
        while(True) {
            .req
            net.read(req, me, "publish_resp");
            nop(req)
        }
    }

    proc HandlePubrel() {
        #@type Message {
            req = {}
            resp = {"Sender": me}
        #}
        .p
        while(True) {
            .req
            net.read(req, me, "pubrel");
            waitREL.Remove(req.Sender)
            resp.Type = "PUBCOMP"
            net.write(resp, req.Sender, "pubrel_resp")
        }
    }

    proc HandleSubscribe() {
        #@type Message {
            req = {}
            resp = {"Sender": me}
        #}
        .p
        while(True) {
            print("broker waitting subscribe")
            net.read(req, me, "subscribe");
            print("broker recived", req)
            AddSubscriber(TopicPool, req.Topic, req.Sender)
            print("broker add", req.Sender, "to", req.Topic)
            resp.Type = "SUBACK"
            net.write(resp, req.Sender, "subscribe_resp")
            print("broker resp", req.Sender)
        }
    }

    proc HandleUnsubscribe() {
        #@type Message {
            req = {}
            resp = {"Sender": me}
        #}
        .p
        while(True) {
            .req
            net.read(req, me, "unsubscribe");
            RemoveSubscriber(TopicPool, req.Topic, req.Sender)
            resp.Type = "UNSUBACK"
            net.write(resp, req.Sender, "unsubscribe_resp")
        }
    }
}
#}
