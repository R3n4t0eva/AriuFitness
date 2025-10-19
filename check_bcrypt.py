import sys
import bcrypt

print("--- Diagnosi di BCrypt ---")
try:
    # 1. Stampa quale eseguibile di Python stiamo usando
    print(f"Eseguibile Python: {sys.executable}")
    print("-" * 20)

    # 2. Stampa il percorso esatto del file del modulo 'bcrypt' che viene importato
    print(f"Percorso del modulo bcrypt: {bcrypt.__file__}")
    print("-" * 20)

    # 3. Prova ad accedere all'attributo che causa l'errore
    print("Tento di accedere a bcrypt.__about__...")
    version = bcrypt.__about__.__version__
    print(f"SUCCESSO: Versione di bcrypt trovata: {version}")
    print("Questo significa che è installata la libreria corretta.")

except AttributeError:
    print("\n!!! ERRORE: AttributeError Rilevato !!!")
    print("Il modulo 'bcrypt' importato NON ha l'attributo '__about__'.")
    print("Questa è la conferma definitiva che Python sta caricando la libreria sbagliata.")

except Exception as e:
    print(f"\nÈ avvenuto un errore inaspettato: {e}")

print("\n--- Fine della Diagnosi ---")