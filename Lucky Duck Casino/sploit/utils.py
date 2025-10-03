def decomp(cards: list):
    value_all, value_ace = [], []
    for carte in cards:
        value = carte.split("-")[0]
        try:
            value = int(value)
            value_all.append(value)
        except Exception:
            if value in ["J", "Q", "K"]:
                value = 10
                value_all.append(value)
            elif value == "A":
                value_ace.append((1, 11))
            else:
                continue
    value_all.extend(value_ace)
    return value_all


def check_sum_cards(cards: list, criterion: int = 21):
    value_cards = decomp(cards)
    sum_card = 0
    for i, value in enumerate(value_cards):
        if isinstance(value, int):
            sum_card += value
        else:
            if sum_card + value[1] <= criterion and i == len(value_cards) - 1:
                sum_card += value[1]
            else:
                sum_card += value[0]
    return sum_card


def check_double(cards: list):
    if len(cards) != 2:
        return False
    if 9 <= check_sum_cards(cards, 21) <= 11:
        return True
    value_cards = decomp(cards)
    if (1, 11) in value_cards:
        for value in value_cards:
            if isinstance(value, int):
                if 2 <= value <= 7:
                    return True
    return False


def next_card(state: int, deck: list, cards: list):
    index_ = state % len(deck)
    cards.append(deck[index_])
    deck.pop(index_)
    return
