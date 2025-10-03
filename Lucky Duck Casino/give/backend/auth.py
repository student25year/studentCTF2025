from werkzeug.security import generate_password_hash, check_password_hash
from Crypto.Util.number import bytes_to_long
from fastapi import Response, status as status_code
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend import app, SessionDep
from backend.models import User
from backend.config import settings
from sqlmodel import select
import os
import jwt


class Register_login_user(BaseModel):
    username: str
    password: str


@app.post("/api/sign_in")
def sign_in(user: Register_login_user, response: Response, session: SessionDep):
    if session.exec(select(User).filter_by(username=user.username)).first():
        return JSONResponse(status_code=status_code.HTTP_409_CONFLICT,
                            content={
                                "msg": "Такой пользователь уже существует"})
    password_hash = generate_password_hash(user.password)
    new_user = User(username=user.username,
                    password_hash=password_hash)
    new_user.state = bytes_to_long(os.urandom(5))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    response.set_cookie(key="session",
                        value=jwt.encode({"username": user.username,
                                          "id": new_user.id},
                                         settings.Config.SECRET_KEY),
                        max_age=24*60*60)
    return {"id": new_user.id, "msg": "Ok!"}


@app.post('/api/log_in')
def log_in(user: Register_login_user, response: Response, session: SessionDep):
    user_load = session.exec(select(User).filter_by(username=user.username)).first()
    if user_load:
        if check_password_hash(user_load.password_hash, user.password):
            response.set_cookie(key="session",
                                value=jwt.encode({
                                    "username": user_load.username,
                                    "id": user_load.id},
                                    settings.Config.SECRET_KEY),
                                max_age=24*60*60)
            return {"id": user_load.id, "msg": "Ok!"}
    return JSONResponse(status_code=status_code.HTTP_409_CONFLICT,
                        content={"msg": "Неверный пароль/имя пользователя"})


@app.post("/api/log_out")
def log_out(response: Response):
    response.set_cookie(key="session", value="", max_age=0)
    return {"msg": "Ok!"}
