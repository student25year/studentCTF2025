from pwn import remote


def unshiftRight(x, shift):
    res = x
    for i in range(32):
        res = x ^ res >> shift
    return res


def unshiftLeft(x, shift, mask):
    res = x
    for i in range(32):
        res = x ^ (res << shift & mask)
    return res


def untemper(v):
    """ Convert output to MT[i] """
    v = unshiftRight(v, 18)
    v = unshiftLeft(v, 15, 0xefc60000)
    v = unshiftLeft(v, 7, 0x9d2c5680)
    v = unshiftRight(v, 11)
    return v


def temper(y):
    """ Convert MT[i] to output """
    y = y ^ (y >> 11)
    y = y ^ ((y << 7) & (0x9d2c5680))
    y = y ^ ((y << 15) & (0xefc60000))
    y = y ^ (y >> 18)
    return y


def solve(a, b):
    res = []
    mt_i1, mt_i397 = untemper(a), untemper(b)  # MT[i], MT[i+397]
    for msb in range(2):
        y = (msb * 0x80000000) + (mt_i1 & 0x7fffffff)
        mt_i = mt_i397 ^ (y >> 1)
        if (y % 2) != 0:
            mt_i = mt_i ^ 0x9908b0df
        res.append(temper(mt_i))
    return res


remote_client = remote("127.1", 20003)  # Указать актуальный адрес

remote_client.recvuntil(b": ")
remote_client.sendline(b"32")
array_rand_number = [[], []]
attempts = 2025
start_index = (attempts // 624 - 1) * 624 + (attempts % 624) + 1
displacement_index = (attempts // 624 - 1) * 624 + (attempts % 624) + 397
for i in range(16):
    remote_client.recvuntil(b": ")
    remote_client.sendline(f"{start_index + 2 * i}".encode())
    remote_client.recvuntil(b": ")
    remote_client.sendline(f"{displacement_index + 2 * i}".encode())

for i in range(32):
    answer = remote_client.recvline().strip().split(b" = ")[-1]
    array_rand_number[i // 16].append(int(answer))

print(array_rand_number)
array_numbers_in_choices = []

for i in range(len(array_rand_number[0])):
    t = solve(array_rand_number[0][i], array_rand_number[1][i])
    print(t, (start_index + 2 * i, displacement_index + 2 * i))
    array_numbers_in_choices.append(t)

result = [(i >> 24, j >> 24) for i, j in array_numbers_in_choices]
print(result)
remote_client.recvuntil(b"):")

for i in range(len(result)):
    for j in range(len(result[i])):
        remote_client.recvuntil(b": ")
        remote_client.sendline(str(result[i][j]).encode())
print(remote_client.recvline().decode())
