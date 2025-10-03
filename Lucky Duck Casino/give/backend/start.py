from backend.utils import check_sum_cards, check_double, next_card, check_and_load_cookie
from fastapi import Response, Request, status as status_code
from backend.challenge.lfsr import LFSR
from fastapi.responses import JSONResponse
from backend.secret import taps
from backend import app, SessionDep
from backend.models import User
from sqlmodel import select
from backend.config import settings


DECK = ['2-h', '3-h', '4-h', '5-h', '6-h', '7-h', '8-h', '9-h', '10-h', 'J-h', 'Q-h', 'K-h', 'A-h',
        '2-d', '3-d', '4-d', '5-d', '6-d', '7-d', '8-d', '9-d', '10-d', 'J-d', 'Q-d', 'K-d', 'A-d',
        '2-c', '3-c', '4-c', '5-c', '6-c', '7-c', '8-c', '9-c', '10-c', 'J-c', 'Q-c', 'K-c', 'A-c',
        '2-s', '3-s', '4-s', '5-s', '6-s', '7-s', '8-s', '9-s', '10-s', 'J-s', 'Q-s', 'K-s', 'A-s']


def get_flag():
    return settings.Config.FLAG


def load_user(session: SessionDep, request: Request):
    check_cookie, data = check_and_load_cookie(request.cookies)
    if not check_cookie:
        return False, None
    query = select(User).filter(User.id == data.get('id'))
    user = session.exec(query).first()
    if not user:
        return False, None
    return True, user


def end_game(deck: list, dealer: list, state: int, on_hands: list,
             bankroll: int, bet: int, user: User, session: SessionDep,
             bet_double: int = 0):
    while check_sum_cards(dealer) <= 16:
        next_card(state, deck, dealer)
    sum_cards_on_hands = check_sum_cards(on_hands)
    sum_cards_dealer = check_sum_cards(dealer)
    if len(on_hands) == 2 and sum_cards_on_hands == 21 and not (len(dealer) == 2 and sum_cards_dealer == 21):
        message = "Поздравляем! У вас блэкджек!"
        multiplier = 1.5
    elif sum_cards_on_hands > 21:
        message = "Вы проиграли! У вас перебор!"
        multiplier = -1
    elif sum_cards_dealer > 21:
        message = "Вы выиграли! У дилера перебор"
        multiplier = 1
    elif sum_cards_on_hands > sum_cards_dealer:
        message = "Вы выиграли!"
        multiplier = 1
    elif sum_cards_on_hands == sum_cards_dealer:
        message = "Ничья"
        multiplier = 0
    elif sum_cards_on_hands < sum_cards_dealer:
        message = "Вы проиграли!"
        multiplier = -1
    user.bankroll = bankroll + int(multiplier * (bet + bet_double))
    user.bet = 0
    user.on_hands = ""
    user.dealer = ""
    user.deck = "|".join(deck)
    session.add(user)
    session.commit()
    session.refresh(user)
    return message


@app.post("/api/bet")
def set_bet(bet: int, request: Request, session: SessionDep):
    check, user = load_user(session, request)
    if not check:
        return JSONResponse(status_code=status_code.HTTP_403_FORBIDDEN,
                            content={"msg": "Access denied!"})
    if user.bankroll < 50:
        return {"msg": "Lose!"}
    elif user.bankroll >= 1000000:
        return {"msg": "Win!"}
    if user.bet:
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Ставка уже сделана"}
        )
    if not (50 <= bet <= min(7500, user.bankroll)):
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Неправильная ставка!"}
        )
    user.bet = bet
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"msg": "Ok!"}


@app.get('/api/get_cards')
def get_cards(request: Request, session: SessionDep):
    check, user = load_user(session, request)
    if not check:
        return JSONResponse(status_code=status_code.HTTP_403_FORBIDDEN,
                            content={"msg": "Access denied!"})
    on_hands = user.on_hands.split("|") if user.on_hands else []
    deck = user.deck.split("|") if user.deck else []
    state = user.state
    dealer = user.dealer.split("|") if user.dealer else []
    if user.bankroll < 50:
        return {"msg": "Lose!"}
    elif user.bankroll >= 1000000:
        return {"msg": "Win!"}
    if user.bet == 0:
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Необходимо сделать ставку!"}
        )
    if user.bet != 0 and on_hands == []:
        if user.number_of_games % 2 == 0:
            state = LFSR(taps, state).gen_number()
        if user.number_of_games % 5 == 0:
            deck = DECK * 4
        for _ in range(2):
            next_card(state, deck, on_hands)
        for _ in range(2):
            next_card(state, deck, dealer)
        user.number_of_games += 1
        user.dealer = "|".join(dealer)
        user.deck = "|".join(deck)
        user.on_hands = "|".join(on_hands)
        user.state = state
        session.add(user)
        session.commit()
        session.refresh(user)
    return {
        "msg": "Ok!",
        "bankroll": user.bankroll,
        "bet": user.bet,
        "on_hands": on_hands,
        "dealer": dealer[:1]
        }


@app.get("/api/get_bankroll")
def get_bankroll(request: Request, session: SessionDep):
    check, user = load_user(session, request)
    if not check:
        return JSONResponse(status_code=status_code.HTTP_403_FORBIDDEN,
                            content={"msg": "Access denied!"})
    return {"msg": "Ok!", "bankroll": user.bankroll}


@app.get("/api/check_double")
def get_check_double(request: Request, session: SessionDep):
    check, user = load_user(session, request)
    if not check:
        return JSONResponse(status_code=status_code.HTTP_403_FORBIDDEN,
                            content={"msg": "Access denied!"})
    on_hands = user.on_hands.split("|") if user.on_hands else []
    if not on_hands:
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Вы еще не в игре!"}
        )
    return {"msg": check_double(on_hands)}


@app.put("/api/more_button")
def more_button(request: Request, session: SessionDep):
    check, user = load_user(session, request)
    if not check:
        return JSONResponse(status_code=status_code.HTTP_403_FORBIDDEN,
                            content={"msg": "Access denied!"})
    on_hands = user.on_hands.split("|") if user.on_hands else []
    deck = user.deck.split("|") if user.deck else []
    state = user.state
    if not on_hands:
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Вы еще не в игре!"}
        )
    if check_sum_cards(on_hands) > 21:
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "У вас перебор!"}
        )
    next_card(state, deck, on_hands)
    user.deck = "|".join(deck)
    user.on_hands = "|".join(on_hands)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"msg": "Ok!"}


@app.put("/api/enough_button")
def enough_button(request: Request, session: SessionDep):
    check, user = load_user(session, request)
    if not check:
        return JSONResponse(status_code=status_code.HTTP_403_FORBIDDEN,
                            content={"msg": "Access denied!"})
    on_hands = user.on_hands.split("|") if user.on_hands else []
    deck = user.deck.split("|") if user.deck else []
    state = user.state
    dealer = user.dealer.split("|") if user.dealer else []
    if not on_hands:
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Вы еще не в игре!"}
        )
    message = end_game(deck, dealer, state, on_hands,
                       user.bankroll, user.bet, user, session)
    return {"msg": message,
            "bankroll": user.bankroll,
            "on_hands": on_hands,
            "dealer": dealer}


@app.post("/api/bet_double")
def bet_double(bet_double: int, request: Request, session: SessionDep):
    check, user = load_user(session, request)
    if not check:
        return JSONResponse(status_code=status_code.HTTP_403_FORBIDDEN,
                            content={"msg": "Access denied!"})
    on_hands = user.on_hands.split("|") if user.on_hands else []
    deck = user.deck.split("|") if user.deck else []
    state = user.state
    dealer = user.dealer.split("|") if user.dealer else []
    if not on_hands:
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Вы еще не в игре!"}
        )
    if not check_double(on_hands):
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Не выполнены условия для дабл!"}
        )
    if not (50 <= bet_double <= user.bet):
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Неправильная ставка!"}
        )
    next_card(state, deck, on_hands)
    message = end_game(deck, dealer, state, on_hands,
                       user.bankroll, user.bet, user, session, bet_double)
    return {"msg": message,
            "bankroll": user.bankroll,
            "on_hands": on_hands,
            "dealer": dealer}


@app.put("/api/sorendo_button")
def sorendo_button(request: Request, session: SessionDep):
    check, user = load_user(session, request)
    if not check:
        return JSONResponse(status_code=status_code.HTTP_403_FORBIDDEN,
                            content={"msg": "Access denied!"})
    on_hands = user.on_hands.split("|") if user.on_hands else []
    dealer = user.dealer.split("|") if user.dealer else []
    if not on_hands:
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Вы еще не в игре!"}
        )
    if len(on_hands) != 2:
        return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Нельзя делать сорендо!"}
        )
    if len(dealer) == 2 and check_sum_cards(dealer) == 21:
        message = "У дилера блэкджек, сорендо невозможно! Вы проиграли!"
        multiplier = -1
    else:
        message = "Сорендо!"
        multiplier = -0.5
    user.bankroll = user.bankroll + int(multiplier * (user.bet))
    user.bet = 0
    user.on_hands = ""
    user.dealer = ""
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"msg": message,
            "bankroll": user.bankroll,
            "on_hands": on_hands,
            "dealer": dealer}


@app.delete('/api/lose')
def lose(request: Request, session: SessionDep, response: Response):
    check, user = load_user(session, request)
    if not check:
        return JSONResponse(status_code=status_code.HTTP_403_FORBIDDEN,
                            content={"msg": "Access denied!"})
    session.delete(user)
    session.commit()
    response.set_cookie(key="session", value="", max_age=0)
    return {"msg": "Ok!"}


@app.get("/api/flag")
def print_flag(request: Request, session: SessionDep):
    check, user = load_user(session, request)
    if not check:
        return JSONResponse(status_code=status_code.HTTP_403_FORBIDDEN,
                            content={"msg": "Access denied!"})
    if user.bankroll >= 1000000:
        return {"msg": get_flag()}
    return JSONResponse(
            status_code=status_code.HTTP_424_FAILED_DEPENDENCY,
            content={"msg": "Недостаточно денег!"}
        )
