from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta
import logging

# Настройка логирования
logging.basicConfig(
    filename='server_error.log',
    level=logging.DEBUG,  # Изменено на DEBUG для более подробного логирования
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Секретный ключ для JWT
SECRET_KEY = "your-secret-key-here"  # В продакшене используйте безопасный ключ
ALGORITHM = "HS256"

# Функции для работы с базой данных
def init_db():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, password TEXT, email TEXT)''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

# Инициализация базы данных при запуске
init_db()

# Функции для работы с JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/register")
async def register(request: Request):
    try:
        data = await request.json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        logger.info(f"Attempting to register user: {username}")

        if not all([username, password, email]):
            logger.error("Missing required fields in registration")
            raise HTTPException(status_code=400, detail="Missing required fields")

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Проверяем, существует ли пользователь
        c.execute("SELECT username FROM users WHERE username = ?", (username,))
        if c.fetchone():
            conn.close()
            logger.error(f"Username {username} already exists")
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Хешируем пароль
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # Сохраняем пользователя
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                  (username, hashed_password.decode(), email))
        conn.commit()
        conn.close()
        
        # Создаем пустой файл для досок пользователя
        filename = f"boards_{username}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            logger.info(f"Created empty boards file for user {username}")
        except Exception as e:
            logger.error(f"Error creating boards file for user {username}: {str(e)}")
        
        # Создаем токен
        access_token = create_access_token({"sub": username})
        logger.info(f"Successfully registered user: {username}")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Error in registration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(request: Request):
    try:
        data = await request.json()
        username = data.get('username')
        password = data.get('password')

        if not all([username, password]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Получаем пользователя
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        stored_password = result[0]
        
        # Проверяем пароль
        if not bcrypt.checkpw(password.encode(), stored_password.encode()):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Создаем токен
        access_token = create_access_token({"sub": username})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-token")
async def verify_token(request: Request):
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        username = await get_current_user(token)
        return {"username": username}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/sync-boards")
async def sync_boards(request: Request):
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        username = await get_current_user(token)
        data = await request.json()
        
        logger.info(f"Syncing boards for user {username}")
        logger.debug(f"Boards data: {json.dumps(data)}")
        
        # Сохраняем данные в файл
        filename = f"boards_{username}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully saved boards for user {username}")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error saving boards to file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error saving boards: {str(e)}")
    except Exception as e:
        logger.error(f"Error in sync_boards: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-boards")
async def get_boards(request: Request):
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            logger.error("No token provided in request")
            raise HTTPException(status_code=401, detail="No token provided")
            
        username = await get_current_user(token)
        logger.info(f"Getting boards for user: {username}")
        
        # Читаем данные из файла
        filename = f"boards_{username}.json"
        logger.info(f"Attempting to read boards from {filename}")
        
        if not os.path.exists(filename):
            logger.info(f"File {filename} does not exist, creating empty file")
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                logger.info(f"Created empty boards file for user {username}")
                return {"boards": {}}
            except Exception as e:
                logger.error(f"Error creating empty boards file: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error creating boards file: {str(e)}")
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Successfully read boards for user {username}")
            logger.debug(f"Boards data: {json.dumps(data)}")
            return {"boards": data}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from file: {str(e)}")
            # Если файл поврежден, создаем новый
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                logger.info(f"Created new boards file after JSON decode error for user {username}")
                return {"boards": {}}
            except Exception as write_error:
                logger.error(f"Error creating new boards file after JSON decode error: {str(write_error)}")
                raise HTTPException(status_code=500, detail="Error recovering from corrupted boards file")
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error reading boards: {str(e)}")
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in get_boards: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 