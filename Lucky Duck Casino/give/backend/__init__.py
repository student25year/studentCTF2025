from fastapi import FastAPI, Depends, status as status_code, HTTPException
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Annotated
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, SQLModel, create_engine
from fastapi.templating import Jinja2Templates
from backend.utils import check_and_load_cookie
from backend.config import settings
from backend.models import Endpoints


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")
engine = create_engine(settings.Config.SQLALCHEMY_DATABASE_URI)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@app.on_event("startup")
async def on_startup():
    create_db_and_tables()


@app.get("/", response_class=HTMLResponse)
async def html_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/auth", response_class=HTMLResponse)
async def auth_html(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


@app.get("/{endpoints}", response_class=HTMLResponse)
async def endpoint_with_html(endpoints: str, request: Request):
    if endpoints not in Endpoints._value2member_map_:
        raise HTTPException(status_code=404)
    check_cookie, _ = check_and_load_cookie(request.cookies)
    if not check_cookie:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(f"{endpoints}.html",
                                      {"request": request})


@app.middleware("http")
async def custom_http_exception_handler(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 404:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=status_code.HTTP_404_NOT_FOUND)
    return response


import backend.auth
import backend.start
