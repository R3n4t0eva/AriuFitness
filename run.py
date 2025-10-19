import sys
import os
import uvicorn

# Aggiunge la cartella 'src' al path di sistema per trovare i moduli
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🚀 Benvenuto in FitnessAI!")
    
    while True:
        choice = input("Scegli l'interfaccia: [1] GUI Desktop | [2] Web App: ")
        
        if choice == '1':
            print("Avvio della GUI Desktop...")
            # L'interprete ora sa come trovare il modulo gui.app
            from gui.app import start_application
            start_application()
            break
            
        elif choice == '2':
            print("Avvio della Web App... Apri il browser su http://127.0.0.1:8000")
            # Uvicorn deve sapere che l'app si trova nel modulo webapp.main
            uvicorn.run("webapp.main:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=['src'])
            break
            
        else:
            print("Scelta non valida. Per favore, inserisci 1 o 2.")

if __name__ == "__main__":
    main()