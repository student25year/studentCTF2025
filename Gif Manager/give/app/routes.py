from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import schemas
import utils
import magic
import os
from models import get_db, create_tables
from jose import JWTError, jwt

create_tables()

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

MAX_FILE_SIZE = 5 * 1024 * 1024


async def validate_gif_file(file: UploadFile = File(...)):
    content = await file.read(2048)
    await file.seek(0)

    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ["image/gif"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format. Only GIF files are allowed. Detected: {mime_type}",
        )

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    await file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE} bytes",
        )

    if not file.filename.lower().endswith(".gif"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File must have .gif extension",
        )

    return file


def get_user_by_username(db: Session, username: str):
    query = text("SELECT * from users WHERE username = :username")
    return db.execute(query, {"username": username}).first()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not utils.verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        id = payload.get("id")
        username = payload.get("sub")

        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.execute(
        text(f"SELECT * FROM users WHERE id = {id} and username = '{username}'")
    ).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: schemas.UserResponse = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/api/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = utils.get_password_hash(user.password)

    query = text(
        """
            INSERT INTO users (username, hashed_password, is_active, created_at, gifs_count)
            VALUES (:username, :hashed_password, :is_active, :created_at,:gifs_count)
            RETURNING *
        """
    )

    params = {
        "username": user.username,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "gifs_count": 0,
    }

    result = db.execute(query, params)
    db.commit()

    db_user = result.first()
    return db_user


@app.post("/api/login", response_model=schemas.Token)
def login_for_access_token(form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"id": user.id, "sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/profile/", response_model=schemas.UserResponse)
async def read_users_me(
    current_user: schemas.UserResponse = Depends(get_current_active_user),
):
    return current_user


@app.get("/api/gifs/random/")
def get_random_gif(
    gif_dir: str = "gifs",
    current_user: schemas.UserResponse = Depends(get_current_active_user),
):
    try:
        import random

        base_path = Path(gif_dir)

        if not base_path.exists() or not base_path.is_dir():
            raise HTTPException(status_code=404, detail="Directory not found")

        gif_files = list(base_path.rglob("*.gif"))

        if not gif_files:
            raise HTTPException(status_code=404, detail="No GIF files found")

        random_gif = random.choice(gif_files)

        return {
            "name": random_gif.name,
            "size": random_gif.stat().st_size,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def increment_user_gifs_count(user_id: int, db: Session):
    try:
        update_query = text(
            "UPDATE users SET gifs_count = gifs_count + 1 WHERE id = :user_id"
        )
        db.execute(update_query, {"user_id": user_id})
        db.commit()

        select_query = text(
            "SELECT id, username, gifs_count FROM users WHERE id = :user_id"
        )
        result = db.execute(select_query, {"user_id": user_id})

        return result.first()

    except Exception as e:
        db.rollback()
        raise e


@app.post("/api/upload_gif", response_model=dict)
async def upload_gif(
    file: UploadFile = Depends(validate_gif_file),
    upload_dir: str = "gifs",
    current_user: schemas.UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        upload_path = Path(upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)

        original_filename = Path(file.filename).stem
        safe_filename = f"{original_filename}.gif"

        file_path = upload_path / safe_filename

        if file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="File with this name already exists",
            )

        async with aiofiles.open(file_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)

        file_size = file_path.stat().st_size

        increment_user_gifs_count(current_user.id, db)

        return {
            "filename": safe_filename,
            "size": file_size,
            "uploaded_at": datetime.now().isoformat(),
            "message": "GIF file uploaded successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}",
        )


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
