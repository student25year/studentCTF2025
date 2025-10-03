class LFSR():
    def __init__(self, taps: list[int], seed: int):
        self.taps = taps
        self.state = [int(i) for i in list("{:040b}".format(seed))]

    def sum(self, m):
        res = 0
        for i in m:
            res ^= i
        return res

    def clock(self):
        x = self.state[0]
        self.state = self.state[1:] + [self.sum([self.state[i] for i in self.taps])]
        return x

    def gen_number(self):
        for _ in range(len(self.state)):
            self.clock()
        number = "".join(list(map(str, self.state)))
        number = int(number, 2)
        return number
