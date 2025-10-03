import requests
from sage.all import GCD, CRT, GF
from sage.matrix.berlekamp_massey import berlekamp_massey
from lfsr import LFSR
from utils import check_sum_cards, check_double, next_card
from client import sign_in, set_bet, send_more, send_enough, send_sorendo, send_double, get_bankroll, get_flag, get_cards


DECK = ['2-h', '3-h', '4-h', '5-h', '6-h', '7-h', '8-h', '9-h', '10-h', 'J-h', 'Q-h', 'K-h', 'A-h',
        '2-d', '3-d', '4-d', '5-d', '6-d', '7-d', '8-d', '9-d', '10-d', 'J-d', 'Q-d', 'K-d', 'A-d',
        '2-c', '3-c', '4-c', '5-c', '6-c', '7-c', '8-c', '9-c', '10-c', 'J-c', 'Q-c', 'K-c', 'A-c',
        '2-s', '3-s', '4-s', '5-s', '6-s', '7-s', '8-s', '9-s', '10-s', 'J-s', 'Q-s', 'K-s', 'A-s']


def find_in_array_all(a: list, k: str):
    for i in range(len(a)):
        if a[i] == k:
            yield i


def get_new_modules(m: list):
    result = [0 for _ in range(len(m))]
    for i in range(len(m)):
        result[i] = m[i]
    for i in range(len(result)):
        for j in range(i+1, len(result)):
            gcd_ = GCD(result[i], result[j])
            if gcd_ != 1:
                result[j] = result[j] // gcd_
    return result


def crack_lfsr(states):
    F = GF(2)
    binary_stream = []
    for i in states:
        binary_stream.extend([F(int(k)) for k in "{:040b}".format(i)])
    g = berlekamp_massey(binary_stream)
    print(g)
    taps = []
    for i, degree in enumerate(g):
        if i != 40 and degree == 1:
            taps.append(i)
    return taps


def append_dictionaries(card, len_deck, dictionary_cards, state):
    a = {}
    a['card'] = card
    a['length_deck'] = len_deck
    a['state'] = state
    len_deck -= 1
    dictionary_cards.append(a)
    return len_deck


def game_to_win(states_true: list[int], taps: list[int], decks: list[str], session: requests.Session):
    bankroll = get_bankroll(session)
    number_of_games = 4
    state = states_true[-1]
    while bankroll < 1000000 and bankroll >= 50:
        if number_of_games % 2 == 0:
            state = LFSR(taps, state).gen_number()
        if number_of_games % 5 == 0:
            decks = DECK * 4
        number_of_games += 1
        on_hands = []
        dealer = []
        sorendo = False
        double = None
        more_card = 0
        bet = 50
        for _ in range(2):
            next_card(state, decks, on_hands)
        for _ in range(2):
            next_card(state, decks, dealer)
        print(number_of_games, state, len(decks), on_hands, dealer)
        if check_sum_cards(on_hands) == 21:
            bet = min(bankroll, 7500)
            while check_sum_cards(dealer) <= 16:
                next_card(state, decks, dealer)
        elif check_sum_cards(dealer) == 21:
            sorendo = True
        elif check_double(on_hands):
            decks_theoretically = [i for i in decks]
            on_hands_theoretically = [i for i in on_hands]
            dealer_theoretically = [i for i in dealer]
            next_card(state, decks_theoretically, on_hands_theoretically)
            while check_sum_cards(dealer_theoretically) <= 16:
                next_card(state, decks_theoretically, dealer_theoretically)
            sum_cards_on_hands = check_sum_cards(on_hands_theoretically)
            sum_cards_dealer = check_sum_cards(dealer_theoretically)
            if sum_cards_on_hands <= 21 and (sum_cards_on_hands > sum_cards_dealer or sum_cards_dealer > 21):
                bet = min(bankroll, 7500)
                double = bet
                decks = [i for i in decks_theoretically]
        if bet == 50 and not sorendo:
            decks_theoretically = [i for i in decks]
            on_hands_theoretically = [i for i in on_hands]
            dealer_theoretically = [i for i in dealer]
            while check_sum_cards(on_hands_theoretically) < 21:
                index_ = state % len(decks_theoretically)
                if check_sum_cards(on_hands_theoretically + [decks_theoretically[index_]]) > 21:
                    break
                else:
                    next_card(state, decks_theoretically, on_hands_theoretically)
                    more_card += 1
            sum_cards_on_hands = check_sum_cards(on_hands_theoretically)

            while check_sum_cards(dealer_theoretically) <= 16:
                next_card(state, decks_theoretically, dealer_theoretically)
            sum_cards_dealer = check_sum_cards(dealer_theoretically)
            if sum_cards_dealer > 21 or sum_cards_dealer < sum_cards_on_hands:
                bet = min(bankroll, 7500)
                decks = [i for i in decks_theoretically]
            elif sum_cards_dealer > sum_cards_on_hands:
                sorendo = True
                more_card = 0
            else:
                decks = [i for i in decks_theoretically]
        if sorendo:
            set_bet(session, bet)
            get_cards(session)
            send_sorendo(session)
        elif double:
            set_bet(session, bet)
            get_cards(session)
            send_double(session, double)
        else:
            set_bet(session, bet)
            get_cards(session)
            for _ in range(more_card):
                send_more(session)
            send_enough(session)
        try:
            bankroll = get_bankroll(session)
            print(bankroll)
        except Exception:
            break
    print(get_flag(session))


auth, session = sign_in()
print(auth)
dictionary_cards = []
len_deck = 0
state = 0
number_of_games = 4
for i in range(number_of_games):
    if i % 5 == 0:
        len_deck = len(DECK) * 4
    if i % 2 == 0:
        state += 1
    set_bet(session, 50)
    get_cards(session)
    send_more(session)
    dealer_cards, on_hands_cards = send_enough(session)
    print(on_hands_cards, dealer_cards)
    for j in range(2):
        len_deck = append_dictionaries(on_hands_cards[j], len_deck, dictionary_cards, state)
    for j in range(2):
        len_deck = append_dictionaries(dealer_cards[j], len_deck, dictionary_cards, state)
    for j in range(2, len(on_hands_cards)):
        len_deck = append_dictionaries(on_hands_cards[j], len_deck, dictionary_cards, state)
    for j in range(2, len(dealer_cards)):
        len_deck = append_dictionaries(dealer_cards[j], len_deck, dictionary_cards, state)
    
states_true = []
i = 0

decks = DECK * 4
for state in range(1, 3):
    modules = []
    indexes_ = []
    supposed_states = []
    cards = []
    while len(modules) != 7:
        modules.append(dictionary_cards[i]['length_deck'])
        indexes_.append([i for i in find_in_array_all(decks, dictionary_cards[i]['card'])])
        cards.append(dictionary_cards[i]['card'])
        i += 1
    new_modules = get_new_modules(modules)
    print(indexes_)
    for k in range(0, 2**14):
        try:
            remainders = []
            k = "{:014b}".format(k)
            k = [int(k[l:l+2], 2) for l in range(0, len(k), 2)]
            for j, numb in enumerate(k):
                if len(remainders) == 0:
                    remainders.append(indexes_[j][numb])
                else:
                    count = 0
                    for l in range(len(remainders)):
                        if remainders[l] < indexes_[j][numb]:
                            count += 1
                    remainders.append((indexes_[j][numb] - count))
        except Exception:
            continue
        try:
            supposed_states.append(CRT(remainders, new_modules))
        except Exception:
            continue

    while i < len(dictionary_cards) and dictionary_cards[i]['state'] == state:
        modules.append(dictionary_cards[i]['length_deck'])
        cards.append(dictionary_cards[i]['card'])
        i += 1
    print(modules, cards)
    for k in supposed_states:
        check = True
        decks_new = ["" for _ in range(len(decks))]
        for j in range(len(decks)):
            decks_new[j] = decks[j]
        for l in range(len(cards)):
            index_ = k % modules[l]
            if decks_new[index_] != cards[l]:
                check = False
                break
            decks_new.pop(index_)
        if check:
            states_true.append(k)
            break
    print(states_true)
    if state == 2:
        if len(states_true) != 2:
            exit("None states_true!")
    for m in modules:
        index_ = states_true[state - 1] % m
        decks.pop(index_)

print(decks, len(decks))
taps = crack_lfsr(states_true)
print(taps)
game_to_win(states_true, taps, decks, session)
