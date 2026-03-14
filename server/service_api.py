from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sqlite3 as sq
import uuid
from pydantic import BaseModel
import hashlib
from dotenv import load_dotenv
import os
import random
from PIL import Image, ImageDraw
load_dotenv()
app = FastAPI()
DB_PATH = os.getenv("DATABASE_NAME")

# Раздаём файлы из files/ по URL /files/...
os.makedirs("files", exist_ok=True)
app.mount("/files", StaticFiles(directory="files"), name="files")

#SQL
#-------------------------------------------------------
def get_db():
    conn = sq.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sq.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uuid        TEXT PRIMARY KEY,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            icon TEXT,
            sub_level TEXT NOT NULL DEFAULT 'free',
            sub_expire_date DATETIME,
            tokens_left INT DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()
#------------------------------------------------------

def generate_icon(user_id: str, folder: str):
    """
    Генерирует identicon — 5x5 сетка с симметрией как у GitHub.
    Seed берётся из uuid — каждый раз одна и та же картинка для одного юзера.
    Сохраняет в files/users/{uuid}/icon.png
    """
    rng = random.Random(user_id)  # детерминированный random на основе uuid

    # случайный цвет (не слишком тёмный и не слишком светлый)
    r = rng.randint(50, 200)
    g = rng.randint(50, 200)
    b = rng.randint(50, 200)
    color = (r, g, b)
    bg = (240, 240, 240)

    grid = 5
    cell = 60  # размер одной ячейки в пикселях
    size = grid * cell

    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)

    # генерируем только левую половину (3 колонки), зеркалим на правую
    for row in range(grid):
        for col in range(3):
            if rng.random() > 0.5:
                x = col * cell
                y = row * cell
                draw.rectangle([x, y, x + cell, y + cell], fill=color)
                # зеркало
                mirror_col = grid - 1 - col
                if mirror_col != col:
                    x2 = mirror_col * cell
                    draw.rectangle([x2, y, x2 + cell, y + cell], fill=color)

    icon_path = os.path.join(folder, "icon.png")
    img.save(icon_path)
    return icon_path

#CURL CLASS
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str
class Update(BaseModel):
    item: str
    newitem: str
    olditem: str = ""  # нужен только при смене пароля



#API SETTINGS

@app.get("/")
async def root():
    return {"status": "Koritsu API running"}


@app.post("/register")
def register(data: RegisterRequest):
    user_id = str(uuid.uuid4())


    password_hash = hashlib.sha256((data.password + user_id).encode()).hexdigest()

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (uuid, username, password) VALUES (?, ?, ?)",
            (user_id, data.username, password_hash)
        )
        try:
            user_folder = f"files/users/{user_id}"
            os.makedirs(f"{user_folder}/fragmos", exist_ok=True)
            os.makedirs(f"{user_folder}/engrafo", exist_ok=True)
            icon_path = generate_icon(user_id, user_folder)
            conn.execute("UPDATE users SET icon = ? WHERE uuid = ?", (icon_path, user_id))
        except Exception as e:
            return {"error": f"Some internal error {e}"}
        conn.commit()
    except sq.IntegrityError:
        return {"error": "Username already taken"}
    finally:
        conn.close()

    return {"success": f"User {data.username} created!"}


@app.post("/login")
def login(data: LoginRequest):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (data.username,)
    ).fetchone()
    conn.close()

    if row is None:
        return {"error": "User not found!"}

    password_hash = hashlib.sha256((data.password + row["uuid"]).encode()).hexdigest()

    if password_hash == row["password"]:
        return {"success": "Auth true", "uuid": row["uuid"]}
    else:
        return {"error": "Username or password is incorrect!"}

@app.get("/user/{uuid}")
def get_user_data(uuid: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE uuid = ?", (uuid,)).fetchone() 
    conn.close()
    if row is None:
        return {"error": "User not exist"}
    else:
        return {"user_data": {"username": row["username"], "icon": row["icon"], "sub_level": row["sub_level"], "sub_expire_date": row["sub_expire_date"], "tokens_left": row["tokens_left"]}}

@app.get("/user/{uuid}/{folder}")
def get_user_folder_files(uuid: str, folder: str):
    if folder not in ("fragmos", "engrafo"):
        return {"error": "Unable to get folder"}
    if folder == "engrafo":
        return {"error": "Service not available"}

    folder_path = f"files/users/{uuid}/fragmos"
    if not os.path.exists(folder_path):
        return {"error": "User folder not found"}
    files = [f for f in os.listdir(folder_path) if f.endswith(".xml")]
    return {"files": files}


@app.patch("/user/{uuid}")
def update_item(uuid: str, data: Update):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE uuid = ?", (uuid,)).fetchone()

    if row is None:
        conn.close()
        return {"error": "User not exist"}

    match data.item:
        case "username":
            taken = conn.execute("SELECT uuid FROM users WHERE username = ?", (data.newitem,)).fetchone()
            if taken is not None:
                conn.close()
                return {"error": "Username already taken"}
            conn.execute("UPDATE users SET username = ? WHERE uuid = ?", (data.newitem, uuid))
            conn.commit()
            conn.close()
            return {"success": f"Username changed to {data.newitem}"}

        case "password":
            # проверяем старый пароль
            old_hash = hashlib.sha256((data.olditem + row["uuid"]).encode()).hexdigest()
            if old_hash != row["password"]:
                conn.close()
                return {"error": "Old password is incorrect"}
            new_hash = hashlib.sha256((data.newitem + row["uuid"]).encode()).hexdigest()
            conn.execute("UPDATE users SET password = ? WHERE uuid = ?", (new_hash, uuid))
            conn.commit()
            conn.close()
            return {"success": "Password changed"}

        case "icon":
            # newitem = имя файла иконки (файл уже должен быть загружен отдельно)
            icon_path = f"files/users/{uuid}/{data.newitem}"
            if not os.path.exists(icon_path):
                conn.close()
                return {"error": "Icon file not found"}
            conn.execute("UPDATE users SET icon = ? WHERE uuid = ?", (icon_path, uuid))
            conn.commit()
            conn.close()
            return {"success": f"Icon updated"}

        case "tokens_left":
            if data.olditem == "minus":
                amount = int(data.newitem)
                new_balance = row["tokens_left"] - amount
                if new_balance < 0:
                    conn.close()
                    return {"error": "Not enough tokens"}
                conn.execute("UPDATE users SET tokens_left = ? WHERE uuid = ?", (new_balance, uuid))
                conn.commit()
                conn.close()
                return {"success": f"Tokens left: {new_balance}"}
            if data.olditem == "plus":
                amount = int(data.newitem)
                new_balance = row["tokens_left"] + amount
                if new_balance < 0:
                    conn.close()
                    return {"error": "Not enough tokens"}
                conn.execute("UPDATE users SET tokens_left = ? WHERE uuid = ?", (new_balance, uuid))
                conn.commit()
                conn.close()
                return {"success": f"Tokens left: {new_balance}"}

        case _:
            conn.close()
            return {"error": f"Unknown field: {data.item}"}
