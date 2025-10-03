from Crypto.Util.number import getPrime, isPrime, inverse
from Crypto.PublicKey import RSA
import argparse
import os


class RSA_new():
    def __init__(self, bitlength: int, diff: int):
        self.diff = diff
        self.__gen_params(bitlength)
        self.e = 0x10001
        self.phi = (self.p - 1) * (self.q - 1)
        self.d = inverse(self.e, self.phi)

    def __gen_params(self, bitlength: int):
        while True:
            self.p = getPrime((bitlength - self.diff) // 2)
            a = getPrime(self.diff + 1)
            self.q = a * self.p + 2
            while not isPrime(self.q):
                self.q += 2
            self.N = self.p * self.q
            print(len(bin(self.N)[2:]))
            if len(bin(self.N)[2:]) == bitlength:
                print(a)
                break

    def import_params(self, output_directory: str):
        rsa_construct = RSA.construct((self.N, self.e, self.d, self.p, self.q))
        private_key = rsa_construct.export_key(pkcs=8)
        public_key = rsa_construct.public_key().export_key(pkcs=8)
        try:
            with open(f"{output_directory}/id_rsa.pub", "wb") as file:
                file.write(public_key)
            with open(f"{output_directory}/id_rsa", "wb") as file:
                file.write(private_key)
            return True
        except Exception as err:
            print(f"Error: {err}")
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output_dir", default=None, type=str,
                        help="Название выходной директории")
    parser.add_argument("-bl", "--bitlength", default=None, type=int,
                        help="Битность модуля N для RSA")
    parser.add_argument("-d", "--diff", default=None, type=int)
    args = parser.parse_args()
    if not args.output_dir:
        exit("Аргумент output_dir отсутствует!")
    if not args.bitlength:
        exit("Аргумент bitlength отсутствует!")
    if not args.diff:
        exit("Аргумент diff отсутствует!")
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    rsa = RSA_new(args.bitlength, args.diff)
    if rsa.import_params(args.output_dir):
        print("Good!")
    else:
        print("Bad :(")
