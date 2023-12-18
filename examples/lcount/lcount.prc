profile Counter(input, output) {
    proc main() {
        #@type int64 {
        sum = 0
        i = 1
        n = 0
        #}
        input.read(n)
        while (i <= n) {
            sum = sum + i
            i = i + 1
        }
        output.write(sum)
    }
}