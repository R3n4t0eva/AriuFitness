from supabase import create_client, Client
from typing import Optional, List, Dict, Any

# Usa le tue credenziali reali
URL = "https://czrztgsqpbijesiuwhnw.supabase.co" 
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN6cnp0Z3NxcGJpamVzaXV3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY5ODI5NjEsImV4cCI6MjA5MjU1ODk2MX0.U4HntAfDPxUqg9CIXKjbSj2W_igYhijIQoaI1l9UwV0"

supabase: Client = create_client(URL, KEY)

# ==================== FUNZIONI AUTENTICAZIONE (Supabase Auth) ====================

def registra_utente_auth(email: str, password: str, nome: str, cognome: str, data_nascita: str):
    """
    Registra un nuovo utente usando Supabase Auth.
    Crea l'account di autenticazione e il profilo nella tabella profili.
    """
    try:
        # 1. Crea l'utente nel servizio Auth di Supabase
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            return {"success": False, "error": "Errore nella creazione dell'account"}
        
        # 2. Crea il profilo nella tabella profili
        profilo_data = {
            "email": email,
            "nome": nome,
            "cognome": cognome,
            "data_nascita": data_nascita
        }
        
        profilo_response = supabase.table("profili").insert(profilo_data).execute()
        
        return {"success": True, "data": profilo_response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def login_utente(email: str, password: str):
    """
    Effettua il login usando Supabase Auth.
    Restituisce il token di accesso.
    """
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not auth_response.session:
            return {"success": False, "error": "Email o password non corretti"}
        
        return {
            "success": True,
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== FUNZIONI PROFILO ====================

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Recupera il profilo di un utente per email."""
    try:
        response = supabase.table("profili").select("*").eq("email", email).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Errore nel recuperare profilo: {e}")
        return None


def aggiorna_utente(email: str, nome: Optional[str] = None, cognome: Optional[str] = None, 
                   data_nascita: Optional[str] = None) -> Dict[str, Any]:
    """Aggiorna i dati di un utente esistente."""
    try:
        data = {}
        if nome is not None:
            data["nome"] = nome
        if cognome is not None:
            data["cognome"] = cognome
        if data_nascita is not None:
            data["data_nascita"] = data_nascita
        
        response = supabase.table("profili").update(data).eq("email", email).execute()
        return {"success": True, "data": response.data[0] if response.data else data}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== FUNZIONI ALLENAMENTI ====================

def get_esercizio_id_by_nome(nome: str) -> Optional[int]:
    """Trova l'esercizio_id dalla tabella esercizi basandosi sul nome."""
    try:
        response = supabase.table("esercizi").select("id").eq("nome", nome).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        return None
    except Exception as e:
        print(f"Errore nel recuperare esercizio_id: {e}")
        return None

def salva_allenamento(email: str, esercizio_id: int, risultato_cv: Dict[str, Any]):
    """
    Salva un record nello storico. 
    risultato_cv è il dizionario con i dati della Computer Vision.
    """
    try:
        data = {
            "utente_email": email,
            "esercizio_id": esercizio_id,
            "risultato_json": risultato_cv 
            # data e ora sono automatici (DEFAULT)
        }
        response = supabase.table("storico_esercizi").insert(data).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== FUNZIONI FEEDBACK ====================

def salva_feedback(email: str, messaggio: str, emoji: str):
    """
    Salva un feedback. 
    emoji DEVE essere: 'soddisfatto', 'neutrale' o 'insoddisfatto' (ENUM)
    """
    try:
        data = {
            "utente_email": email,
            "messaggio": messaggio,
            "emoji": emoji
        }
        response = supabase.table("feedback").insert(data).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== QUERY COMPLESSE ====================

def get_storico_completo(email: str):
    """Recupera lo storico includendo i dettagli dell'esercizio (JOIN)"""
    try:
        # Grazie alle FK, possiamo chiedere a Supabase di includere i dati di 'esercizi'
        response = supabase.table("storico_esercizi") \
            .select("data, ora, risultato_json, esercizi(nome, zona_allenamento)") \
            .eq("utente_email", email) \
            .order("data", desc=True) \
            .execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}