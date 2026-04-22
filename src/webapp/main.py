import sys
import os
import asyncio
import base64
import numpy as np
import cv2
import traceback
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import timedelta
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import date

# Contesto per l'hashing della password
# Usiamo PBKDF2-SHA256 per evitare:
# - incompatibilità passlib<->bcrypt su Python recenti
# - limite bcrypt dei 72 byte sulla password
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Configurazione per i token JWT
SECRET_KEY = "la-tua-chiave-segreta-super-difficile" # CAMBIA QUESTA CHIAVE!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Path al nostro "database" di utenti
USERS_DB_PATH = "users/credentials.json"

# --- MODELLI DATI (Pydantic) ---

class UserBase(BaseModel):
    email: EmailStr
    nome: str
    cognome: str
    data_nascita: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    data_nascita: Optional[str] = None

# --- FUNZIONI HELPER ---

def get_user(email: str) -> Optional[UserInDB]:
    """Cerca un utente per email nel nostro file JSON."""
    try:
        with open(USERS_DB_PATH, "r") as f:
            users = json.load(f)
        for user_data in users:
            if user_data["email"] == email:
                return UserInDB(**user_data)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return None

def verify_password(plain_password, hashed_password):
    """Verifica una password in chiaro con quella hashata."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Crea l'hash di una password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token di accesso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = get_user(token_data.email)
    if user is None:
        raise credentials_exception
    return user

def is_adult_yyyy_mm_dd(dob: str) -> bool:
    # dob atteso "YYYY-MM-DD"
    try:
        y, m, d = [int(x) for x in dob.split("-")]
        born = date(y, m, d)
    except Exception:
        return False
    today = date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age >= 18




# Assicura che il server possa trovare i moduli nella cartella 'logic'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from logic.classification import Classification

# 1. Inizializzazione dell'app FastAPI
app = FastAPI(title="ElderFit API")

# --->>> 2. CONFIGURA IL MIDDLEWARE SUBITO DOPO <<<---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint di test per verificare che il server sia attivo
@app.get("/")
def read_root():
    return {"status": "ElderFit server is running"}

# --- ENDPOINT DI REGISTRAZIONE E LOGIN ---

@app.post("/register", response_model=UserBase)
def register_user(user: UserCreate):
    """Registra un nuovo utente."""
    if not user.password or len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if len(user.password.encode("utf-8")) > 1024:
        raise HTTPException(status_code=400, detail="Password is too long")

    db_user = get_user(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    user_in_db = UserInDB(**user.dict(), hashed_password=hashed_password)
    
    users = []
    try:
        with open(USERS_DB_PATH, "r") as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass # Il file non esiste o è vuoto
        
    users.append(user_in_db.dict())
    
    with open(USERS_DB_PATH, "w") as f:
        json.dump(users, f, indent=2)
        
    return UserBase(**user.dict())


@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Effettua il login e restituisce un token."""
    user = get_user(form_data.username) # OAuth2 form usa 'username' per l'email
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserBase)
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return UserBase(
        email=current_user.email,
        nome=current_user.nome,
        cognome=current_user.cognome,
        data_nascita=current_user.data_nascita,
    )

@app.put("/users/me", response_model=UserBase)
def update_users_me(payload: UserUpdate, current_user: UserInDB = Depends(get_current_user)):
    nome = payload.nome.strip() if payload.nome is not None else None
    cognome = payload.cognome.strip() if payload.cognome is not None else None
    data_nascita = payload.data_nascita.strip() if payload.data_nascita is not None else None

    if nome is not None and not nome:
        raise HTTPException(status_code=400, detail="Nome non valido")
    if cognome is not None and not cognome:
        raise HTTPException(status_code=400, detail="Cognome non valido")
    if data_nascita is not None:
        if not is_adult_yyyy_mm_dd(data_nascita):
            raise HTTPException(status_code=400, detail="Devi essere maggiorenne (almeno 18 anni)")

    try:
        with open(USERS_DB_PATH, "r") as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = []

    updated = None
    for i in range(len(users)):
        if users[i].get("email") == current_user.email:
            if nome is not None:
                users[i]["nome"] = nome
            if cognome is not None:
                users[i]["cognome"] = cognome
            if data_nascita is not None:
                users[i]["data_nascita"] = data_nascita
            updated = users[i]
            break

    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")

    with open(USERS_DB_PATH, "w") as f:
        json.dump(users, f, indent=2)

    return UserBase(
        email=updated.get("email"),
        nome=updated.get("nome", ""),
        cognome=updated.get("cognome", ""),
        data_nascita=updated.get("data_nascita", ""),
    )


# 3. Gestione della connessione WebSocket per la classificazione
class ConnectionManager:
    """Gestisce le connessioni WebSocket attive."""
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_json(self, data: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)

manager = ConnectionManager()


@app.websocket("/ws/classify/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # 1. ACCETTA LA CONNESSIONE PRIMA DI TUTTO
    await websocket.accept()
    # 2. ORA REGISTRA LA CONNESSIONE (senza usare manager.connect)
    manager.active_connections[client_id] = websocket
    
    print(f"DEBUG: Client #{client_id} connesso, tento di caricare il classificatore...")
    
    try:
        classifier = Classification(model_path="models/LSTM_Combo2.pth")
        print(f"DEBUG: Classificatore per client #{client_id} caricato con successo.")

        while True:
            message = await websocket.receive_text()
            
            try:
                data = json.loads(message)
                # Comando per iniziare un esercizio
                if data.get("type") == "start_exercise":
                    exercise_name = data.get("exercise_name")
                    if exercise_name:
                        classifier.set_active_exercise(exercise_name)
                    continue
                
                # ---> AGGIUNGI QUESTO BLOCCO PER IL RESET <---
                if data.get("type") == "reset_reps":
                    classifier.reset_current_reps()
                    continue
            
            except json.JSONDecodeError:
                # Se non è JSON, è un frame video in Base64
                base64_str = message
                img_data = base64.b64decode(base64_str.split(',')[1])
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is not None:
                exercise, rep, phrase, landmarks = await asyncio.to_thread(classifier.classify, frame)
                
                # --- QUESTA È LA CORREZIONE ---
                # Converte i dati dei keypoint da NumPy a tipi Python standard (float)
                # in modo che possano essere convertiti in JSON.
                json_safe_landmarks = [
                    {"x": float(lm.get("x", 0)), "y": float(lm.get("y", 0))}
                    for lm in landmarks if lm # Assicura che il landmark non sia nullo
                ]
                # -----------------------------

                # Costruisci la risposta usando i dati "puliti"
                response = {
                    "exercise": exercise.replace("_", " "),
                    "repetitions": rep,
                    "phrase": phrase,
                    "keypoints": json_safe_landmarks # <-- Usa la nuova lista convertita
                }
                
                print(f"Invio al client: Esercizio={response['exercise']}, Num. Keypoint={len(response['keypoints'])}")
                await manager.send_json(response, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        print(f"Client #{client_id} disconnesso.")
    except Exception as e:
        # Questo ora stamperà l'errore completo e dettagliato
        print(f"\n!!! ERRORE FATALE per client #{client_id} !!!")
        traceback.print_exc()
        manager.disconnect(client_id)
