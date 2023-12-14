
#@retry 10 1s {
#@type int
const PRODUCER = 0

#@new struct ReqMsg {"Message_type": "int", "Request_id": "int", "Client_id": "int", "Path": "string", "Content": "string"}
#@new struct QAnswer {"Answers": "[]string", "Score": "int"}

#@type {self: int, net: int, instream: int, out: int, fileSystem: int}
profile AClient(self, net, instream, out, fileSystem, log, stdPath) {
    proc main() {
        #@type int
        id = self
        #@type string {
            path = ""
            submit = "" 
            stdPath = ""
        #}
        .c
        while (True) {
            .req
            #@type string {
            submit = "" 
            res = ""
            #}
            instream.read(path)
            stdPath.read(stdPath)
            t1 = Time()
            fileSystem.read(submit, path)
            #@type ReqMsg
            reqMsg = {"Message_type": 0, "Request_id": id, "Client_id": id, "Path": stdPath, "Content": submit}
            net.write(reqMsg, PRODUCER, "req")
            net.read(res, id, "resp");
            latency = Time()-t1
            log.write(latency)
            out.write(res);
        }
    }

    ## proc recv() {
    ##     #@type int
    ##     id = self
    ##     #@type string {
    ##         res = ""
    ##     #}
    ##     .c
    ##     while (True) {
    ##         net.read(res, id, "resp");
    ##         out.write(res);
    ##         # print(res)
    ##     }
    ## }
}


#@type {self: int, net: int, s: int, json: int, fileSystem: int}
profile AServer(self, net, json, fileSystem) {
    #@type map[int]int {
    kvStore = NewStore()
    kvFlag = NewStore()
    #}

    #@type {"input": {"clientID": "int", "requestID": "int", "value": "int"}}
    func saveFS(clientID, requestID, value) {
        .AtomSave
        #@type int 
        flag = StoreGet(kvFlag, clientID)
        if (flag < requestID) {
            StoreSet(kvStore, clientID, value)
            StoreSet(kvFlag, clientID, requestID)
        }
        .EndAtom 
    }


    #@type {"input": {"studentResponse": "QAnswer", "stdAnswer": "QAnswer", "responseID": "int", "requestID": "int"}}
    func computeScore(studentResponse, stdAnswer, responseID, requestID) {
        #@type QAnswer
        feedBack = {}
        #@type string
        res = ""
        #@type int
        score = 0
        if (len(stdAnswer.Answers) == len(studentResponse.Answers)) {
            #@type int
            i = 0
            while (i < len(stdAnswer.Answers)) {
                if (stdAnswer.Answers[i] != studentResponse.Answers[i]) {
                    feedBack.Answers = Append(feedBack.Answers, "False")
                    score = score + 1
                } else {
                    feedBack.Answers = Append(feedBack.Answers, "True")
                }
                i = i + 1
            }
        }
        feedBack.Score = score
        json.read(res, "dump", feedBack, res)
        saveFS(responseID, requestID, score)
        .resp
        net.write(res, responseID, "resp");
        return
    }

    proc main() {
        #@type int
        id = self;
        #@type string {
            answer = ""
        #}
        computeScoreActor = Actor(computeScore)
        #@type ReqMsg
        req = {}
        #@type QAnswer {
            studentResponse = {}
            stdAnswer = {}
        #}
        
        .p
        while(True) {
            .req
            net.read(req, id, "req");
            #@type QAnswer
            json.read(studentResponse, "load", req.Content, studentResponse)
            fileSystem.read(answer, req.Path)
            json.read(stdAnswer, "load", answer, stdAnswer)
            .computeScore
            computeScoreActor.Send(studentResponse, stdAnswer, req.Client_id, req.Request_id)
        }
    }

    #@type {"input":{}, "output":{"err": "error"}}
    func init() {
        kvFlag = NewStore()
        kvStore = NewStore()
        return
    }
}
#}
