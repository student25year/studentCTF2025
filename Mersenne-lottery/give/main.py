import random


# Чтобы лучше понять, что здесь происходит, просто на тестах зафиксируйте любой seed
# На сервере же seed отсутствует!!!!
# random.seed(123456)
FLAG = open("flag.txt", "r").read().strip()
BANNER = open("banner.txt", "r").read()
WELCOME = open("welcome.txt", "r").read()
ONE_CELL = open("ticket.txt", "r").read()
HINT = f"{'-' * 67}Секция ХИНТ{'-' * 67}"
LOTTERY = f"{'-' * 65}Секция ЛОТЕРЕЯ!{'-' * 65}"


class Challenge:
    def __init__(self):
        self.attemps = 2025

    def __check_input__(self, msg: str, lower_limit: int, high_limit: int):
        result = None
        try:
            result = int(input(msg))
            assert lower_limit <= result <= high_limit
        except Exception:
            print("Ошибка ввода числа! До свидания!")
            exit(0)
        return result

    def section_hint(self):
        number_of_indices = self.__check_input__("Введите количество индексов от 0 до 32, которые вы хотите узнать: ", 0, 32)
        array_hint_index = []
        for i in range(number_of_indices):
            hint_index = self.__check_input__(f"{i+1}) Введите индекс от 0 до {self.attemps - 1}, который вы хотите узнать: ", 0, self.attemps-1)
            array_hint_index.append(hint_index)

        array_hint_index = list(set(array_hint_index))
        array_hint_index.sort()

        array_rand_numbers = []
        for i in range(self.attemps):
            rand_number = random.getrandbits(32)
            array_rand_numbers.append(rand_number)
        for index_ in array_hint_index:
            print(f"rand[{index_}] = {array_rand_numbers[index_]}")

    def challenge(self):
        try:
            print("\n".join([BANNER, WELCOME, HINT]))
            self.section_hint()
            print("\n".join(["-" * 145, LOTTERY, "Ваш билет:", ONE_CELL]))
            gen_rand_number = random.choices([i for i in range(256)], k=16)
            print("Теперь введите свой выбор (мы даём вам 2 попытки на каждое число):")
            number_of_matches = 0
            for i in range(16):
                input_number_1 = self.__check_input__(f"Число {i+1} (попытка 1): ", 0, 255)
                input_number_2 = self.__check_input__(f"Число {i+1} (попытка 2): ", 0, 255)
                if input_number_1 == gen_rand_number[i] or input_number_2 == gen_rand_number[i]:
                    number_of_matches += 1
            if number_of_matches == 0:
                print("Вы ничего не выиграли(")
            elif 1 <= number_of_matches <= 15:
                print(f"Вы выиграли: {number_of_matches * 4}$")
            else:
                print(f"Вы выиграли наш главный приз: {FLAG}")
            print("Спасибо, что поучаствовали в нашей лотерее!")
        except KeyboardInterrupt:
            print("До свидания! Спасибо, что поучаствовали в нашей лотерее!")


if __name__ == "__main__":
    Challenge().challenge()
