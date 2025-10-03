import os
import random
import re
import time
from itertools import islice
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Constants
BASE = 3
SIDE = BASE * BASE
MAX_ATTEMPTS = 130
REGULAR_SUDOKU_PATTERN = r's\[([0-8])\]\[([0-8])\]=([1-9])'

# Load files
FLAG = open("flag.txt", "rb").read().strip()
BANNER = open("banner.txt", "r").read().strip()
WELCOME = open("welcome.txt", "r").read()
MENU = open("menu.txt", "r").read().strip()


class Sudoku:
    def __init__(self):
        self.base = BASE
        self.side = SIDE

    def pattern(self, row, column):
        return (self.base * (row % self.base) + row // self.base + column) % self.side

    def shuffle(self, sequence):
        return random.sample(sequence, len(sequence))

    def generate_solution(self):
        rBase = range(self.base)
        rows = [g * self.base + r for g in self.shuffle(rBase) for r in self.shuffle(rBase)]
        cols = [g * self.base + c for g in self.shuffle(rBase) for c in self.shuffle(rBase)]
        nums = self.shuffle(range(1, self.base * self.base + 1))
        solution = [[nums[self.pattern(row, column)] for column in cols] for row in rows]
        return solution

    def solve_sudoku(self, board):
        # There must be something here...🤔
        pass

    def get_board(self, solution, number_of_cells):
        while True:
            board = [[solution[i][j] for j in range(len(solution[i]))] for i in range(len(solution))]
            squares = self.side * self.side
            empties = squares - number_of_cells
            for p in random.sample(range(squares), empties):
                board[p // self.side][p % self.side] = 0
            # Sudoku must have only one solution!
            solved = [*islice(self.solve_sudoku(board), 2)]
            if len(solved) == 1:
                break
        return board

    def print_board(self, secrets):
        board = [[0 for _ in range(self.side)] for _ in range(self.side)]
        result = ''
        for secret in secrets:
            for entry in secret:
                index_i, index_j, k = map(int, re.findall(REGULAR_SUDOKU_PATTERN, entry)[0])
                board[index_i][index_j] = k

        for i in range(len(board)):
            if i % self.base == 0 and i != 0:
                result += "-" * 21 + "\n"
            for j in range(len(board[i])):
                if j % self.base == 0 and j != 0:
                    result += "| "
                result += str(board[i][j]) if board[i][j] else "*"
                result += " "
            result += "\n"
        return result


class SecretSharingScheme:
    def __init__(self, board, num_parts: int):
        self.secrets = self.secret_sharing(board, num_parts)
        self.sudoku_utils = Sudoku()

    def secret_sharing(self, board, num_parts: int):
        secret = []
        for i in range(len(board)):
            for j in range(len(board[0])):
                if board[i][j] != 0:
                    secret.append(f"s[{i}][{j}]={board[i][j]}")
        random.shuffle(secret)
        assert len(secret) % num_parts == 0
        result = []
        step = len(secret) // num_parts
        for i in range(0, len(secret), step):
            result.append(secret[i:i + step])
        return result

    def get_secret(self, secrets):
        board = [[0 for _ in range(self.sudoku_utils.side)] for _ in range(self.sudoku_utils.side)]
        for secret in secrets:
            for entry in secret:
                index_i, index_j, k = map(int, re.findall(REGULAR_SUDOKU_PATTERN, entry)[0])
                board[index_i][index_j] = k
        solved = [*islice(self.sudoku_utils.solve_sudoku(board), 2)]
        if len(solved) != 1:
            return None
        return solved[0]


class Challenge:
    def __init__(self):
        self.sudoku = Sudoku()
        self.attempts = MAX_ATTEMPTS

    def encrypt_flag(self):
        key = sha256(str(self.solution).encode()).digest()[:16]
        iv = os.urandom(16)
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        enc_flag = cipher.encrypt(pad(FLAG, 16))
        return iv.hex() + enc_flag.hex()

    def decrypt_flag(self, solution, enc_flag):
        key = sha256(str(solution).encode()).digest()[:16]
        iv = bytes.fromhex(enc_flag[:32])
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        enc_flag = bytes.fromhex(enc_flag[32:])
        decrypted_flag = cipher.decrypt(enc_flag)
        return unpad(decrypted_flag, 16).decode()

    def check_input_format_part_secret(self, part_secret: str):
        part_secret = part_secret.split("; ")
        if len(part_secret) > 6:
            print("Неправильная длина вашей части секрета!")
            return False
        for data in part_secret:
            try:
                i, j, partition = map(int, re.findall(REGULAR_SUDOKU_PATTERN, data)[0])
            except Exception:
                print("Неправильный формат входных данных!")
                return False
        return True

    def format_part_secret(self, part_secret: list):
        return "; ".join(part_secret)

    def challenge(self):
        print(BANNER)
        print(WELCOME)
        print("Подождите...")
        self.solution = self.sudoku.generate_solution()
        time.sleep(0.1)
        print("Формируется общий секрет...")
        self.board = self.sudoku.get_board(self.solution, 30)
        print("Секрет разделяется на 5 частей...\nЧасть 1: ...\nЧасть 2: ...\nЧасть 3: ...\nЧасть 4: ...\nЧасть 5 (это ваш секрет, запросите его в меню): ...\n")
        self.secret_sharing_scheme = SecretSharingScheme(self.board, 5)
        time.sleep(0.1)
        print("Шифруется информация на общем секрете...\n")
        self.enc_flag = self.encrypt_flag()
        time.sleep(0.1)

        while True:
            try:
                print(MENU)
                choice_options = input("> ")
                match choice_options:
                    case "1":
                        self.attempts -= 1
                        print("Подождите...")
                        for i in range(4):
                            print(f"Участник {i + 1} вводит свою часть секрета:...")
                        your_part = input("Введите свою часть секрета: ")
                        if not self.check_input_format_part_secret(your_part):
                            continue
                        your_part = your_part.split("; ")
                        print(self.sudoku.print_board([your_part]))
                        secrets = []
                        for i in range(4):
                            secrets.append(self.secret_sharing_scheme.secrets[i])
                        secrets.append(your_part)
                        solution = self.secret_sharing_scheme.get_secret(secrets)
                        if solution:
                            try:
                                print(f"Ваша часть флага: {self.decrypt_flag(solution, self.enc_flag)[:8]}")
                            except Exception:
                                print("Что-то пошло не так...")
                        else:
                            print("Ой, нет, кто-то передал неправильную часть секрета!")
                        if self.attempts == 0:
                            print("Ой, нет, до свидания!")
                            break
                    case "2":
                        print(f"Ваша часть секрета: {self.format_part_secret(self.secret_sharing_scheme.secrets[-1])}")
                        print(self.sudoku.print_board(self.secret_sharing_scheme.secrets[-1:]))
                    case "3":
                        print(f"Зашифрованная информация: {self.enc_flag}")
                    case "0":
                        print("До свидания!")
                        exit()
                    case _:
                        print("Ошибка выбора!")
            except Exception:
                exit("Возникла какая-то ошибка... До свидания!")


if __name__ == "__main__":
    challenge = Challenge()
    challenge.challenge()
