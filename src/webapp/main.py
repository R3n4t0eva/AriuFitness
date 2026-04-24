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
from pydantic import BaseModel, EmailStr
from datetime import date

# Assicura che il server possa trovare i moduli nella cartella 'logic'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from logic import database

# Configurazione per i token JWT (per validare il token di Supabase)
SECRET_KEY = "your-supabase-jwt-secret"  # Supabase fornisce questo
ALGORITHM = "HS256"

# --- MODELLI DATI (Pydantic) ---

class UserBase(BaseModel):
    email: EmailStr
    nome: str
    cognome: str
    data_nascita: str

class UserCreate(UserBase):
    password: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    data_nascita: Optional[str] = None

# --- FUNZIONI HELPER ---

def get_user(email: str) -> Optional[UserBase]:
    """Cerca un utente per email nel database Supabase."""
    try:
        user_data = database.get_user_by_email(email)
        if user_data:
            return UserBase(**user_data)
        return None
    except Exception as e:
        print(f"Errore nel recuperare utente: {e}")
        return None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserBase:
    """Valida il token Supabase e restituisce l'utente corrente."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica il token (Supabase usa JWT)
        payload = jwt.decode(token, options={"verify_signature": False})  # Verifica off per MVP
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(email)
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

# Import Classification
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
    """Registra un nuovo utente usando Supabase Auth."""
    if not user.password or len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if len(user.password.encode("utf-8")) > 1024:
        raise HTTPException(status_code=400, detail="Password is too long")
    
    if not is_adult_yyyy_mm_dd(user.data_nascita):
        raise HTTPException(status_code=400, detail="Devi essere maggiorenne (almeno 18 anni)")

    db_user = get_user(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Registra usando Supabase Auth (email + password)
    # e crea il profilo nella tabella profili
    result = database.registra_utente_auth(
        email=user.email,
        password=user.password,
        nome=user.nome,
        cognome=user.cognome,
        data_nascita=user.data_nascita
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=f"Registration error: {result.get('error')}")
        
    return UserBase(**user.dict())


@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Effettua il login usando Supabase Auth e restituisce un token."""
    email = form_data.username  # OAuth2 form usa 'username' per l'email
    password = form_data.password
    
    # Effettua il login usando Supabase Auth
    result = database.login_utente(email, password)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": "bearer"
    }


@app.get("/users/me", response_model=UserBase)
def read_users_me(current_user: UserBase = Depends(get_current_user)):
    return current_user

@app.put("/users/me", response_model=UserBase)
def update_users_me(payload: UserUpdate, current_user: UserBase = Depends(get_current_user)):
    """Aggiorna i dati dell'utente nel database Supabase."""
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

    # Aggiorna nel database Supabase
    result = database.aggiorna_utente(
        email=current_user.email,
        nome=nome,
        cognome=cognome,
        data_nascita=data_nascita
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=f"Update error: {result.get('error')}")
    
    updated = result.get("data", {})
    return UserBase(
        email=updated.get("email"),
        nome=updated.get("nome", ""),
        cognome=updated.get("cognome", ""),
        data_nascita=updated.get("data_nascita", ""),
    )

'''
# --- ENDPOINT PER ALLENAMENTI ---

@app.post("/workouts/session")
def save_workout_session(session_data: SessionData, current_user: UserBase = Depends(get_current_user)):
    """Salva una sessione completa di allenamento nel database."""
    try:
        from datetime import datetime as dt
        data_sessione = dt.utcnow().isoformat()
        
        # Salva gli esercizi nello storico
        for esercizio in session_data.esercizi:
            # Trova l'esercizio_id dalla tabella esercizi
            esercizio_id = database.get_esercizio_id_by_nome(esercizio.esercizio)
            if esercizio_id is None:
                print(f"Warning: Esercizio '{esercizio.esercizio}' non trovato nel database")
                continue
            
            risultato_json = {
                "reps": esercizio.reps,
                "accuratezza": esercizio.accuratezza,
                "tempo_medio": esercizio.tempo_medio,
                "difficolta": session_data.difficolta,
                "commento": session_data.commento
            }
            
            result = database.salva_allenamento(
                email=current_user.email,
                esercizio_id=esercizio_id,
                risultato_cv=risultato_json
            )
            
            if not result["success"]:
                print(f"Errore nel salvataggio dell'esercizio {esercizio.esercizio}: {result.get('error')}")
        
        return {
            "success": True,
            "message": "Workout session saved successfully",
            "data_sessione": data_sessione
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/workouts/history")
def get_workout_history(current_user: UserBase = Depends(get_current_user)):
    """Recupera la storia degli allenamenti dell'utente."""
    try:
        result = database.get_storico_completo(current_user.email)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=f"Error retrieving workouts: {result.get('error')}")
        
        return {"success": True, "data": result.get("data", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
'''