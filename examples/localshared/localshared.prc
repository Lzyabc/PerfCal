
#@retry 10 1s {
#@type int64
const PRODUCER = 0
const CONSUMER = 1

#@new struct ReqMsg {"Message_type": "int64", "Client_id": "int64", "Path": "string", "Content": "string"}
#@new struct QAnswer {"Answers": "[]string"}

#@type {self: int64, net: int64, instream: int64, out: int64, fileSystem: int64}
profile AClient(self, instream, out) {
    #@type int
    num = 0
    #@type QAnswer
    stdAnswer = {}
    #@type {"input": {"a": "int"}, "output": {"b": "int"}}
    func newInc(a) {
        .AtomAdd
            b = num + a
            print("num = ", num)
        .End
        return b
    }

    proc inc() {
        #@type int
        n = 1
        .AtomAdd
            num = newInc(n)
            print("num = ", num)
            print(CONSUMER)
        .End
    }

    proc inc2() {
        #@type int
        n = 1
        .AtomAdd
            num = num + n
            print("num = ", num)
        .End
    }

    proc main() {
        #@type string
        path = ""
        #incActor = Actor(inc)
        .c
        while (True) {
            .req
            #@type string
            instream.read(path)
            #incActor.Send(1)
            out.write(path)
        }
    }
}

#}
