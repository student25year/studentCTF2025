import requests
from string import ascii_letters, digits
from random import choices
import json


# Изменить URL перед запуском
URL = "http://127.0.0.1:8000"


def gen(length: int, alph: str):
    return "".join(choices(alph, k=length))


def sign_in():
    '''Функция для регистрации'''
    username = gen(10, ascii_letters)
    password = gen(15, ascii_letters + digits)
    data = {"username": username,
            "password": password}
    session = requests.Session()
    responce = session.post(f"{URL}/api/sign_in", json=data)
    if responce.status_code != 200:
        exit("None auth!")
    return (username, password), session


def log_in(username, password):
    '''Функция для авторизации'''
    data = {"username": username,
            "password": password}
    session = requests.Session()
    responce = session.post(f"{URL}/api/log_in", json=data)
    if responce.status_code != 200:
        exit("None auth!")
    return session


def set_bet(session: requests.Session, bet: int):
    '''Функция для установления ставки'''
    responce = session.post(f"{URL}/api/bet?bet={bet}")
    if responce.status_code != 200:
        return False
    return True


def get_cards(session: requests.Session):
    '''Функция для получения карт'''
    responce = session.get(f"{URL}/api/get_cards")
    data = json.loads(responce.text)
    dealer_cards = data.get("dealer")
    on_hands_cards = data.get("on_hands")
    return dealer_cards, on_hands_cards


def send_more(session: requests.Session):
    '''Функция для отправки команды "Ещё" '''
    responce = session.put(f"{URL}/api/more_button")
    if responce.status_code == 200:
        return True
    return False


def send_enough(session: requests.Session):
    '''Функция для отправки команды "Хватит" '''
    responce = session.put(f"{URL}/api/enough_button")
    data = json.loads(responce.text)
    dealer_cards = data.get("dealer")
    on_hands_cards = data.get("on_hands")
    return dealer_cards, on_hands_cards


def send_sorendo(session: requests.Session):
    '''Функция для отправки команды "Сорендо" '''
    responce = session.put(f"{URL}/api/sorendo_button")
    if responce.status_code == 200:
        data = json.loads(responce.text)
        dealer_cards = data.get("dealer")
        on_hands_cards = data.get("on_hands")
        return dealer_cards, on_hands_cards
    return None, None


def send_double(session: requests.Session, bet_double: int):
    '''Функция для отправки доп ставки для команды "Дабл" '''
    responce = session.post(f"{URL}/api/bet_double?bet_double={bet_double}")
    if responce.status_code == 200:
        data = json.loads(responce.text)
        dealer_cards = data.get("dealer")
        on_hands_cards = data.get("on_hands")
        return dealer_cards, on_hands_cards
    return None, None


def get_bankroll(session: requests.Session):
    '''Функция для получения актуального банкролла'''
    responce = session.get(f"{URL}/api/get_bankroll")
    bankroll = json.loads(responce.text)["bankroll"]
    return bankroll


def get_flag(session: requests.Session):
    '''Функция для получения флага'''
    responce = session.get(f"{URL}/api/flag")
    return json.loads(responce.text)
