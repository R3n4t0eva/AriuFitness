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

# Contesto per l'hashing della password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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




# Assicura che il server possa trovare i moduli nella cartella 'logic'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from logic.classification import Classification

# 1. Inizializzazione dell'app FastAPI
app = FastAPI(title="TrainerAI API")

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
    return {"status": "TrainerAI server is running"}

# --- ENDPOINT DI REGISTRAZIONE E LOGIN ---

@app.post("/register", response_model=UserBase)
def register_user(user: UserCreate):
    """Registra un nuovo utente."""
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
