#@new struct Person {"id": "int64", "name": "string", "relatives": {"father": "string", "mother": "string", "children": {"number": "int"}}}

profile Counter() {
    #@type int64 {
    input = 0
    output = 0
    #}
    proc main() {
        print("hello")
        #@type int64 {
            sum = 0
            i = 1
            n = input 
        #}
        #@type Person
        xiaoming = {"id" : 1, "name" : "xiaoming", "relatives" : {"father" : "xiaoming's father", "mother" : "xiaoming's mother", "children" : {"number" : 1}}}
        #@type []int64 {
            partialSum = [1, 2, 3]
        #}
        while (i <= n) {
            sum = sum + i
            i = i + 1
            partialSum = Append(partialSum, sum)
        }
        print(xiaoming.name)
        print("id", xiaoming.id)

        n = partialSum[0]
        partialSum = [2, 1]
        output = sum
    }
}