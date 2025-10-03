import re
from pwn import remote
from random import choices
from itertools import islice
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

IP = "127.0.0.1"
PORT = 20003
REGULAR_SUDOKU_PATTERN = r's\[([0-8])\]\[([0-8])\]=([1-9])'
MAX_ATTEMPTS = 130
FLAG_FORMAT = b"stctf"


# Как раз алгоритм, который позволяет последовательно находить все решения судоку, он же используется в main.py
def shortSudokuSolve(board):
    side = len(board)
    base = int(side**0.5)
    flat_board = [n for row in board for n in row]
    blanks = [i for i, n in enumerate(flat_board) if n == 0]
    cover = {(n, p): {*zip([2*side+r, side+c, r//base*base+c//base], [n]*(n and 3))}
             for p in range(side*side) for r, c in [divmod(p, side)] for n in range(side+1)}
    used = set().union(*(cover[n, p] for p, n in enumerate(flat_board) if n))
    placed = 0
    while placed >= 0 and placed < len(blanks):
        pos = blanks[placed]
        used -= cover[flat_board[pos], pos]
        flat_board[pos] = next((n for n in range(flat_board[pos]+1, side+1)
                                if not cover[n, pos] & used), 0)
        used |= cover[flat_board[pos], pos]
        placed += 1 if flat_board[pos] else -1
        if placed == len(blanks):
            solution = [flat_board[r:r+side] for r in range(0, side*side, side)]
            yield solution
            placed -= 1


def get_secret(secrets):
    board = [[0 for __ in range(9)] for _ in range(9)]
    for i in range(len(secrets)):
        index_i, index_j, k = map(int, re.findall(REGULAR_SUDOKU_PATTERN, secrets[i])[0])
        board[index_i][index_j] = k
    solved = [*islice(shortSudokuSolve(board), 10000)]
    return solved


def decrypt_flag(solution: list, enc_flag: str):
    key = sha256(str(solution).encode()).digest()[:16]
    iv = bytes.fromhex(enc_flag[:32])
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    enc_flag = bytes.fromhex(enc_flag[32:])
    decrypt_flag = cipher.decrypt(enc_flag)
    return decrypt_flag


def get_random_index(board: list):
    all_index = [f"s[{i}][{j}]" for i in range(9) for j in range(9)]
    for data_ in board:
        index_i, index_j, _ = map(int, re.findall(REGULAR_SUDOKU_PATTERN, data_)[0])
        all_index.remove(f"s[{index_i}][{index_j}]")
    choices_random_index = choices(all_index, k=25)
    return choices_random_index


def send_main_part(remote_client: remote, new_part: list):
    remote_client.sendline(b"1")
    remote_client.recvuntil("Введите свою часть секрета:")
    remote_client.sendline("; ".join(new_part).encode())
    answer = remote_client.recvuntil(b"> ")
    return answer


def send_choice(remote_client: remote, choice: int):
    remote_client.sendline(str(choice).encode())
    answer = remote_client.recvline().strip().split(b": ")[-1]
    remote_client.recvuntil(b"> ")
    return answer.decode()


if __name__ == "__main__":
    remote_client = remote(IP, PORT)
    remote_client.recvuntil(b"> ")
    main_part = send_choice(remote_client, 2)
    enc_flag = send_choice(remote_client, 3)
    print(f"{enc_flag = }")
    print(f"{main_part= }")
    attemps = 0
    new_part = []
    for _ in range(6):
        new_part = main_part.split("; ")
        new_part.pop(_)
        attemps += 1
        answer = send_main_part(remote_client, new_part)
        print(new_part)
        if FLAG_FORMAT in answer:
            break
        elif _ == 5:
            # Если мы не можем исключить ни одну из наших ячеек, можно смело перезапускать код
            exit("Not solution!")
    board = []
    board.extend(main_part.split("; "))
    choices_random_index = get_random_index(board)
    exit_ = False
    for i_j in choices_random_index:
        for k in range(1, 10):
            answer = send_main_part(remote_client, new_part + [f"{i_j}={k}"])
            attemps += 1
            print(attemps, new_part + [f"{i_j}={k}"])
            if FLAG_FORMAT in answer:
                board.append(f"{i_j}={k}")
                print(f"{len(board) = }, {board = }")
                break
            if attemps == MAX_ATTEMPTS - 1:
                exit_ = True
                break
        if exit_:
            break
    print(f"{attemps = }")
    solved = get_secret(board)
    for solve in solved:
        flag = decrypt_flag(solve, enc_flag)
        if flag.startswith(FLAG_FORMAT):
            print(f"flag: {unpad(flag, 16).decode()}")
            break
