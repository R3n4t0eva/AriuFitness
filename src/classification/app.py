import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from PIL import Image, ImageTk
import os
import threading
import cv2
import numpy as np

from data.dataset import Dataset
from learning.models_pytorch import create_model
from classification.classification import Classification
import util
from classification.users import Users

class GUI:
    """
    Classe che gestisce l'interfaccia grafica dell'applicazione.
    """

    def __init__(self, root):
        """
        Costruttore della classe GUI.
        """

        self.load_images()  # Carica le immagini per gli elementi grafici
        self.cameras = []  # Lista delle webcam disponibili
        self.find_cameras()  # Trova le webcam disponibili

        self.root = root  # Finestra principale
        self.root.title("ElderFit")  # Titolo della finestra

        # Imposta le dimensioni della finestra
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        # Crea un contenitore per i frame
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        # Crea i tre frame/pagine
        self.frame_home = tk.Frame(self.container)
        self.frame_learning = tk.Frame(self.container)
        self.frame_login = tk.Frame(self.container)

        # Posiziona i frame nel container
        self.frame_home.place(relwidth=1, relheight=1)  # Frame 1 occupa tutta la finestra
        self.frame_learning.place(relwidth=1, relheight=1)  # Frame 2 occupa tutta la finestra
        self.frame_login.place(relwidth=1, relheight=1)  # Frame 3 occupa tutta la finestra

        self.show_frame(self.frame_home)  # Mostra la prima pagina (frame_home) all'avvio

        self.build_frame_home()  # Costruisce i contenuti di frame_home
        self.build_frame_learning()  # Costruisce i contenuti di frame_learning
        self.build_frame_login()  # Costruisce i contenuti di frame_login
        
        self.create_threads()  # Creazione dei thread

        self.users = Users()  # Oggetto di gestione degli utenti

        self.classification_window = None  # Finestra di classificazione
        self.last_frame_time = 0  # Tempo dell'ultimo frame
        self.classification = Classification(os.path.join(util.getBasePath(), "models", "LSTM_Combo2.pth"))  # Oggetto di classificazione
        self.choice_keypoints = False  # Scelta per visualizzare i keypoints
        self.cap = None  # Oggetto per la cattura della webcam

    
    def load_images(self):
        """
        Funzione che carica le immagini per gli elementi grafici.
        """

        # Home: icona per il primo pulsante
        icon_home_first_button = Image.open(os.path.join(util.getBasePath(), "GUI_material", "icons", "brain_icon.png"))
        icon_home_first_button = icon_home_first_button.resize((80, 80), Image.LANCZOS)
        self.icon_home_first_button = ImageTk.PhotoImage(icon_home_first_button)

        # Home: icona per il secondo pulsante
        icon_home_second_button = Image.open(os.path.join(util.getBasePath(), "GUI_material", "icons", "exercise_icon.png"))
        icon_home_second_button = icon_home_second_button.resize((80, 80), Image.LANCZOS)
        self.icon_home_second_button = ImageTk.PhotoImage(icon_home_second_button)

        # Creazione del modello: icona di attesa
        icon_model_wait = Image.open(os.path.join(util.getBasePath(), "GUI_material", "icons", "wait.png"))
        icon_model_wait = icon_model_wait.resize((16, 16), Image.LANCZOS)
        self.icon_model_wait = ImageTk.PhotoImage(icon_model_wait)

        # Creazione del modello: icona di caricamento
        icon_model_loading = Image.open(os.path.join(util.getBasePath(), "GUI_material", "icons", "loading.png"))
        icon_model_loading = icon_model_loading.resize((16, 16), Image.LANCZOS)
        self.icon_model_loading = ImageTk.PhotoImage(icon_model_loading)

        # Creazione del modello: icona di completamento
        icon_model_complete = Image.open(os.path.join(util.getBasePath(), "GUI_material", "icons", "complete.png"))
        icon_model_complete = icon_model_complete.resize((16, 16), Image.LANCZOS)
        self.icon_model_complete = ImageTk.PhotoImage(icon_model_complete)

        # Creazione del modello: icona per il pulsante di avvio
        icon_model_start = Image.open(os.path.join(util.getBasePath(), "GUI_material", "icons", "play.png"))
        icon_model_start = icon_model_start.resize((18, 18), Image.LANCZOS)
        self.icon_model_start = ImageTk.PhotoImage(icon_model_start)

        # Creazione del modello: icona per il pulsante di cancellazione
        icon_model_cancel = Image.open(os.path.join(util.getBasePath(), "GUI_material", "icons", "cancel.png"))
        icon_model_cancel = icon_model_cancel.resize((18, 18), Image.LANCZOS)
        self.icon_model_cancel = ImageTk.PhotoImage(icon_model_cancel)

        # Creazione del modello: icona per il pulsante di indietro
        icon_model_back = Image.open(os.path.join(util.getBasePath(), "GUI_material", "icons", "back.png"))
        icon_model_back = icon_model_back.resize((18, 18), Image.LANCZOS)
        self.icon_model_back = ImageTk.PhotoImage(icon_model_back)

        # Classificazione: icona per la persona
        icon_classification_person = Image.open(os.path.join(util.getBasePath(), "GUI_material", "icons", "person.png"))
        icon_classification_person = icon_classification_person.resize((140, 140), Image.LANCZOS)
        self.icon_classification_person = ImageTk.PhotoImage(icon_classification_person)


    # ========================================================================================================
    # FRAME E FINESTRE
    # ========================================================================================================


    def build_frame_home(self):
        """
        Funzione che costruisce il frame home con i pulsanti per l'accesso alle funzionalità dell'applicazione.
        """

        # Font per il titolo con sottolineatura
        title_font = tkfont.Font(family="Arial", size=24, weight="bold", underline=True)

        # Titolo in alto al centro, con sottolineatura
        title_label = tk.Label(self.frame_home, text="ElderFit", font=title_font)
        title_label.pack(pady=20)

        # Sottotitolo subito sotto il titolo
        subtitle_label = tk.Label(self.frame_home, text="Digital Fitness Trainer", font=("Arial", 16))
        subtitle_label.pack(pady=10)

        # Creazione di un frame centrale per i pulsanti
        button_frame = tk.Frame(self.frame_home)
        button_frame.pack(pady=50)

        # Pulsante 1 con icona e testo
        button1 = ttk.Button(button_frame, text="Train the model", compound="top", image=self.icon_home_first_button, command=lambda: self.show_frame(self.frame_learning))
        button1.image = self.icon_home_first_button  # Per mantenere il riferimento all'immagine
        button1.grid(row=0, column=0, padx=20)

        # Pulsante 2 con icona e testo
        button2 = ttk.Button(button_frame, text="Detect the exercises", compound="top", image=self.icon_home_second_button, command=lambda: self.show_frame(self.frame_login))
        button2.image = self.icon_home_second_button  # Per mantenere il riferimento all'immagine
        button2.grid(row=0, column=1, padx=20)

        # Aggiunta di padding per creare pulsanti più grandi
        button1.config(padding=(20, 20), style="Large.TButton", width=15)
        button2.config(padding=(20, 20), style="Large.TButton", width=15)

        # Stile per i pulsanti
        button_style = ttk.Style()
        button_style.configure("Large.TButton", font=("Arial", 14))


    def build_frame_learning(self):
        """
        Funzione che costruisce il frame per la creazione del modello di classificazione.
        """

        # Frasi ed elementi delle fasi di creazione del modello
        self.phases = {
            "names": ["Creating the dataset", "Model training"],
            "elements": []
        }

        # Titolo della finestra di creazione del modello
        self.model_title = tk.Label(self.frame_learning, text="Create the model", font=("Arial", 24))
        self.model_title.pack(pady=50)

        # Creazione di un frame centrale per le label
        process_frame = tk.Frame(self.frame_learning)
        process_frame.pack(pady=40)

        # Font per le fasi
        phase_font = tkfont.Font(family="Arial", size=14)

        for i, phase in enumerate(self.phases["names"]):  # Per ogni fase
            # Label per la frase della fase
            label = tk.Label(process_frame, text=phase, font=phase_font)
            label.grid(row=i, column=0, sticky="w", padx=(0, 20), pady=(0, 10))
            # Frame per le informazioni della fase
            info_frame = tk.Frame(process_frame)
            info_frame.grid(row=i, column=1, sticky="e", padx=(20, 0))
            # Label per il conteggio di avanzamento della fase
            count_label = tk.Label(info_frame, text="", font=phase_font)
            count_label.grid(row=0, column=0, sticky="e", pady=(0, 10))
            # Label per l'icona di stato della fase
            icon_label = tk.Label(info_frame, image=self.icon_model_wait)
            icon_label.image = self.icon_model_wait
            icon_label.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=(0, 10))
            # Aggiunta degli elementi alla lista delle fasi
            self.phases["elements"].append((count_label, icon_label))

        # Frame che contiene i due pulsanti
        button_frame = tk.Frame(self.frame_learning)
        button_frame.pack()

        # Stile per i pulsanti
        button_style = ttk.Style()
        button_style.configure("ModelButtons.TButton", font=("Arial", 14))

        # Pulsante per tornare indietro
        self.model_back_button = ttk.Button(button_frame, text="Back", image=self.icon_model_back, compound="left", command=lambda: self.show_frame(self.frame_home))
        self.model_back_button.image = self.icon_model_back
        self.model_back_button.grid(row=0, column=0, padx=(0, 10))
        self.model_back_button.config(style="ModelButtons.TButton")

        # Pulsante per avviare la creazione del modello
        self.model_play_button = ttk.Button(button_frame, text="Start", image=self.icon_model_start, compound="left", command=lambda: self.on_play_button_click())
        self.model_play_button.image = self.icon_model_start
        self.model_play_button.grid(row=0, column=1, padx=(10, 10))
        self.model_play_button.config(style="ModelButtons.TButton")

        # Pulsante per annullare la creazione del modello
        self.model_cancel_button = ttk.Button(button_frame, text="Cancel", image=self.icon_model_cancel, compound="left", state="disabled", command=lambda: self.on_cancel_button_click())
        self.model_cancel_button.image = self.icon_model_cancel
        self.model_cancel_button.grid(row=0, column=2, padx=(10, 0))
        self.model_cancel_button.config(style="ModelButtons.TButton")


    def build_frame_login(self):
        """
        Funzione che costruisce il frame per il login e la registrazione degli utenti.
        """

        # Titolo della finestra di login
        title = tk.Label(self.frame_login, text="Login / Registration", font=("Arial", 24))
        title.pack(pady=(40, 30))

        # Frame per campi di input
        input_frame = tk.Frame(self.frame_login)
        input_frame.pack(pady=10)

        # font per le label e gli entry
        label_font = ("Arial", 16)
        entry_font = ("Arial", 15)

        # Campo Username
        label_username = tk.Label(input_frame, text="Username:", font=label_font)
        label_username.pack(anchor="w", padx=5)
        self.entry_username = tk.Entry(input_frame, width=30, font=entry_font)  # Campo di testo più grande
        self.entry_username.pack(fill="x", padx=5, pady=5)

        # Campo Password
        label_password = tk.Label(input_frame, text="Password:", font=label_font)
        label_password.pack(anchor="w", padx=5)
        self.entry_password = tk.Entry(input_frame, show="*", width=30, font=entry_font)  # Campo di testo più grande
        self.entry_password.pack(fill="x", padx=5, pady=5)

        # Label di errore nel login
        self.error_label = tk.Label(input_frame, text="", font=("Arial", 12), fg="red")
        self.error_label.pack(pady=5)

        # Frame per pulsanti
        button_frame = tk.Frame(self.frame_login)
        button_frame.pack(pady=(20, 10))

        # Stile per i pulsanti
        button_style = ttk.Style()
        button_style.configure("LoginButtons.TButton", font=("Arial", 14))

        # Pulsante per tornare indietro
        login_back_button = ttk.Button(button_frame, text="Back", image=self.icon_model_back, compound="left", command=self.back_login)
        login_back_button.image = self.icon_model_back
        login_back_button.grid(row=0, column=0, padx=(10, 10))
        login_back_button.config(style="LoginButtons.TButton")

        # Pulsante per effettuare il login
        login_enter_button = ttk.Button(button_frame, text="Login", image=self.icon_model_start, compound="left", command=self.login)
        login_enter_button.image = self.icon_model_start
        login_enter_button.grid(row=0, column=1, padx=(10, 10))
        login_enter_button.config(style="LoginButtons.TButton")
    

    def create_classification_window(self):
        """
        Funzione che crea la finestra per la classificazione degli esercizi e gestione delle varie funzionalità.
        """
        
        # Se la finestra di classificazione è già aperta, la riporta in primo piano
        if self.classification_window is not None and self.classification_window.winfo_exists():
            self.classification_window.lift()
            return

        self.root.withdraw()  # Nasconde la finestra principale

        # Creazione della finestra di classificazione con titolo
        self.classification_window = tk.Toplevel(self.root)
        self.classification_window.title("ElderFit - Exercise Detection")
        self.classification_window.protocol("WM_DELETE_WINDOW", self.close_classification_window)

        # Imposta le dimensioni della finestra
        self.classification_window.geometry("1000x740")
        self.classification_window.resizable(False, False)
        self.classification_window.columnconfigure(1, weight=1)

        # Frame per la parte sinistra
        left_frame_classification = tk.Frame(self.classification_window)
        left_frame_classification.grid(row=0, column=0, padx=(10, 10), pady=(10, 10))

        # Label webcam
        self.webcam_label = tk.Label(left_frame_classification)
        self.webcam_label.pack()

        # Frame per il trainer
        trainer_frame = tk.Frame(left_frame_classification)
        trainer_frame.pack(pady=(40, 20))

        # Label per l'immagine del trainer
        trainer_label = tk.Label(trainer_frame, image=self.icon_classification_person)
        trainer_label.image = self.icon_classification_person
        trainer_label.grid(row=0, column=0)

        # label per le frasi del trainer con contorno
        trainer_canvas = tk.Canvas(trainer_frame, width=440, height=140)
        trainer_canvas.grid(row=0, column=1)
        trainer_canvas.create_rectangle(10, 10, 440, 140, outline='black', width=2)
        trainer_canvas.create_text(220, 10, text="Trainer", font=("Arial", 12), justify="left", anchor="n")
        self.trainer_text = tk.Label(trainer_frame, text="Hello! I'm your personal trainer.\nI will help you to do the exercises correctly.\nLet's start!", font=("Arial", 18))
        trainer_canvas.create_window(220, 80, window=self.trainer_text)

        # Frame per la parte destra
        right_frame_classification = tk.Frame(self.classification_window)
        right_frame_classification.grid(row=0, column=1, padx=(10, 20), pady=(10, 10), sticky="new")
        right_frame_classification.columnconfigure(0, weight=1)

        # label titolo risultati
        results_title = tk.Label(right_frame_classification, text="Exercise Detection", font=("Arial", 20, "bold"))
        results_title.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        # frame esercizio rilevato
        frame_exercise = tk.Frame(right_frame_classification)
        frame_exercise.grid(row=1, column=0, pady=(0, 10), sticky="nsew")
        frame_exercise.columnconfigure(0, weight=1)
        frame_exercise.columnconfigure(1, weight=1)

        # label esercizio rilevato
        exercise_label = tk.Label(frame_exercise, text="Exercise:", font=("Arial", 16))
        exercise_label.grid(row=0, column=0, sticky="w", padx=5)

        # label ripetizioni
        self.exercise_name = tk.Label(frame_exercise, text="None", font=("Arial", 16))
        self.exercise_name.grid(row=0, column=1, sticky="e", padx=5)

        # frame ripetizioni
        frame_repetitions = tk.Frame(right_frame_classification)
        frame_repetitions.grid(row=2, column=0, pady=(0, 10), sticky="nsew")
        frame_repetitions.columnconfigure(0, weight=1)
        frame_repetitions.columnconfigure(1, weight=1)

        # label ripetizioni
        repetitions_label = tk.Label(frame_repetitions, text="Repetitions:", font=("Arial", 16))
        repetitions_label.grid(row=0, column=0, sticky="w", padx=5)

        # label ripetizioni valore
        self.repetitions_value = tk.Label(frame_repetitions, text="0", font=("Arial", 16))
        self.repetitions_value.grid(row=0, column=1, sticky="e", padx=5)

        # pulsante di fine esercizio
        end_exercise_button = ttk.Button(right_frame_classification, text="End exercise", image=self.icon_model_cancel, compound="left", command=lambda: self.classification.stop_exercise())
        end_exercise_button.grid(row=3, column=0, pady=(10, 10), sticky="ew")
        end_exercise_button.config(style="ModelButtons.TButton")

        # titolo impostazioni
        settings_title = tk.Label(right_frame_classification, text="Settings", font=("Arial", 20, "bold"))
        settings_title.grid(row=4, column=0, pady=(20, 10), sticky="ew")

        # frame selezione webcam
        frame_webcam = tk.Frame(right_frame_classification)
        frame_webcam.grid(row=5, column=0, pady=(0, 10), sticky="nsew")
        frame_webcam.columnconfigure(0, weight=1)
        frame_webcam.columnconfigure(1, weight=1)

        # label selezione webcam
        webcam_label = tk.Label(frame_webcam, text="Select webcam:", font=("Arial", 16))
        webcam_label.grid(row=0, column=0, sticky="w", padx=5)

        # menu selezione webcam
        self.webcam_menu = ttk.Combobox(frame_webcam, values=self.cameras, state="readonly", width=10)
        self.webcam_menu.current(0)
        self.webcam_menu.grid(row=0, column=1, sticky="e", padx=5)

        # frame per la scelta dei keypoint
        frame_keypoint = tk.Frame(right_frame_classification)
        frame_keypoint.grid(row=6, column=0, pady=(0, 10), sticky="nsew")
        frame_keypoint.columnconfigure(0, weight=1)
        frame_keypoint.columnconfigure(1, weight=1)

        # label selezione keypoint
        keypoint_label = tk.Label(frame_keypoint, text="Show keypoints:", font=("Arial", 16))
        keypoint_label.grid(row=0, column=0, sticky="w", padx=5)

        # checkbox selezione keypoint
        self.keypoint_var = tk.IntVar()
        keypoint_checkbox = tk.Checkbutton(frame_keypoint, variable=self.keypoint_var, command=self.on_choice_keypoints)
        keypoint_checkbox.grid(row=0, column=1, sticky="e", padx=5)

        # titolo lista esercizi
        exercises_title = tk.Label(right_frame_classification, text="Exercise tutorial", font=("Arial", 20, "bold"))
        exercises_title.grid(row=7, column=0, pady=(20, 10), sticky="ew")

        # lista scorrevole degli esercizi
        exercises = np.load(os.path.join(util.getDatasetPath(), "categories.npy"))        
        self.exercises_list = tk.Listbox(right_frame_classification, font=("Arial", 16), selectmode="single", height=10)
        for exercise in exercises:
            self.exercises_list.insert(tk.END, exercise.replace("_", " "))
        self.exercises_list.grid(row=8, column=0, pady=(0, 20), sticky="nsew")
        self.exercises_list.selection_set(0)

        # frame per i pulsanti
        frame_buttons = tk.Frame(right_frame_classification)
        frame_buttons.grid(row=9, column=0, pady=(0, 10), sticky="nsew")
        frame_buttons.columnconfigure(0, weight=1)
        frame_buttons.columnconfigure(1, weight=1)

        # stile per i pulsanti
        button_style = ttk.Style()
        button_style.configure("ModelButtons.TButton", font=("Arial", 14))

        # pulsante per chiudere la finestra
        close_button = ttk.Button(frame_buttons, text="Back", command=self.close_classification_window, image=self.icon_model_back, compound="left")
        close_button.image = self.icon_model_back
        close_button.grid(row=0, column=0, sticky="ew", padx=5)
        close_button.config(style="ModelButtons.TButton")

        # pulsante per visualizzare il tutorial dell'esercizio selezionato
        tutorial_button = ttk.Button(frame_buttons, text="Show tutorial", image=self.icon_model_start, compound="left", command=self.show_video_tutorial)
        tutorial_button.image = self.icon_model_start
        tutorial_button.grid(row=0, column=1, sticky="ew", padx=5)
        tutorial_button.config(style="ModelButtons.TButton")        

        # Inizializzazione della webcam
        self.cap = cv2.VideoCapture(self.cameras[0])
        self.webcam_menu.bind("<<ComboboxSelected>>", self.on_webcam_selected)
        # Aggiorno la webcam
        self.detection()


    # ========================================================================================================
    # FUNZIONI
    # ========================================================================================================


    def back_login(self):
        """
        Funzione che torna alla home dalla finestra di login
        """
        
        self.show_frame(self.frame_home)
        self.error_label.config(text="")


    def login(self):
        """
        Funzione che gestisce il login dell'utente
        """

        # Recupero delle credenziali e controllo che non siano vuote
        username = self.entry_username.get()
        password = self.entry_password.get()
        if username == "" or password == "":
            self.error_label.config(text="Username and password are required")
            return

        # Controllo se l'utente esiste e se la password è corretta
        if self.users.login(username, password):
            self.entry_username.delete(0, tk.END)
            self.entry_password.delete(0, tk.END)
            self.error_label.config(text="")
            self.create_classification_window()
        else:
            self.error_label.config(text="Incorrect password")


    def show_video_tutorial(self):
        """
        Funzione che mostra il tutorial dell'esercizio selezionato.
        """

        # Ottengo la selezione dalla lista degli esercizi e apro il video corrispondente
        exercise = self.exercises_list.get(self.exercises_list.curselection()).replace(" ", "_")
        tutorial_path = os.path.join(util.getVideoInfoPath(), f"{exercise}.mp4")
        cap_tutorial = cv2.VideoCapture(tutorial_path)

        while True:  # Riproduco il video del tutorial in una finestra
            ret, frame = cap_tutorial.read()
            if ret:
                # Scritta per indicare come chiudere la finestra
                cv2.putText(frame, "Press 'q' to close the window", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

                cv2.imshow("Tutorial", frame)

                if cv2.waitKey(25) & 0xFF == ord('q'):
                    break
            else:
                break
        
        # Chiudo la finestra del tutorial
        cap_tutorial.release()
        cv2.destroyAllWindows()

    
    def close_classification_window(self):
        """
        Funzione che chiude la finestra di classificazione e riporta in primo piano la finestra principale
        """

        self.classification_window.destroy()
        self.classification_window = None
        self.cap.release()
        self.root.deiconify()
        self.show_frame(self.frame_home)
    

    def detection(self):
        """
        Funzione che gestisce la classificazione degli esercizi.
        """

        def update_classification(frame_w, exercise, rep, trainer_phrase, keypoints):
            """
            Funzione interna per l'aggiornamento della classificazione.

            Args:
                frame_w (np.ndarray): Frame della webcam.
                exercise (str): Nome dell'esercizio rilevato.
                rep (int): Numero di ripetizioni rilevate.
                trainer_phrase (str): Frase del trainer.
                keypoints (list): Lista dei keypoints rilevati.
            """

            frame_c = cv2.cvtColor(frame_w, cv2.COLOR_BGR2RGB)
            if self.choice_keypoints:  # Visualizzazione dei keypoints se selezionato
                for kp in keypoints:
                    cv2.circle(frame_c, (int(kp["x"] * frame.shape[1]), int(kp["y"] * frame.shape[0])), 5, (0, 255, 0), -1)
            # Processo l'immagine e la visualizzo nella finestra
            img = Image.fromarray(frame_c)
            img = ImageTk.PhotoImage(image=img)
            self.webcam_label.config(image=img)
            self.webcam_label.image = img
            # Aggiorno le informazioni dell'esercizio rilevato: nome, ripetizioni e frase del trainer
            self.exercise_name.config(text=exercise.replace("_", " "))
            self.repetitions_value.config(text=rep)
            self.trainer_text.config(text=trainer_phrase)
        
        # Acquisizione del frame dalla webcam e classificazione
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (640, 480))
            self.classification.classify(frame, update_classification)
        # Richiamo la funzione dopo 10 ms
        self.webcam_label.after(10, self.detection)


    # ========================================================================================================
    # EVENTI E FUNZIONI
    # ========================================================================================================

    def find_cameras(self):
        """
        Funzione che trova le webcam disponibili.
        """

        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.read()[0]:
                self.cameras.append(i)
                cap.release()
            else:
                break

    
    def on_webcam_selected(self, event):
        """
        Funzione che gestisce la selezione della webcam.
        """
        
        self.cap.release()
        self.cap = cv2.VideoCapture(self.cameras[self.webcam_menu.current()])


    def on_choice_keypoints(self):
        """
        Funzione che gestisce la scelta per visualizzare i keypoints.
        """

        self.choice_keypoints = self.keypoint_var.get()


    def create_threads(self):
        """
        Funzione che crea i thread per la creazione del dataset e del modello.
        """

        def update_progress_dataset(processed_videos, total_videos):
            """
            Funzione interna per l'aggiornamento del progresso della creazione del dataset.

            Args:
                processed_videos (int): Numero di video processati.
                total_videos (int): Numero totale di video
            """

            self.phases["elements"][0][0].config(text=f"{processed_videos}/{total_videos}")

        def start_creation_dataset():
            """
            Funzione interna per avviare la creazione del dataset.
            """

            Dataset().create(callback=update_progress_dataset)
        
        def start_creation_model():
            """
            Funzione interna per avviare la creazione del modello.
            """

            # Carico i dati di training e di validation
            X1, X2, X3, y, num_classes = util.get_dataset("train")
            X1_test, X2_test, X3_test, y_test, _ = util.get_dataset("test")
            # Addestramento
            create_model(X1, X2, X3, y, X1_test, X2_test, X3_test, y_test, num_classes)

        # Creazione dei thread e impostazione delle variabili di controllo
        self.dataset_thread = threading.Thread(target=start_creation_dataset)
        self.model_thread = threading.Thread(target=start_creation_model)
        self.dataset_thread_interrupted = False
        self.model_thread_interrupted = False


    def show_frame(self, frame):
        """
        Funzione che mostra un frame/pagina.

        Args:
            frame (tk.Frame): Frame da mostrare.
        """

        if frame == self.frame_learning:
            self.model_title.config(text="Create the model")
        frame.tkraise()


    def on_play_button_click(self):
        """
        Funzione che gestisce il click sul pulsante di avvio della creazione del modello.
        """

        # Disabilita e abilita i pulsanti necessari
        self.model_play_button.config(state="disabled")
        self.model_cancel_button.config(state="normal")
        self.model_back_button.config(state="disabled")
        self.model_title.config(text="Model creation in progress...")
        # Impostazione delle icone di caricamento
        self.phases["elements"][0][1].config(image=self.icon_model_loading)
        self.phases["elements"][0][1].image = self.icon_model_loading
        self.phases["elements"][1][1].config(image=self.icon_model_wait)
        self.phases["elements"][1][1].image = self.icon_model_wait
        
        # Creazione del dataset
        self.dataset_thread.start()
        self.dataset_thread_finished()


    def dataset_thread_finished(self):
        """
        Funzione che gestisce la fine del thread di creazione del dataset.
        """

        if self.dataset_thread.is_alive(): # Finchè il thread è attivo
            self.root.after(100, self.dataset_thread_finished) # Richiama la funzione dopo 100 ms
        else:  # Se il thread è concluso
            if not self.dataset_thread_interrupted:  # Se il thread non è stato interrotto
                # Impostazione delle icone di completamento e caricamento
                self.phases["elements"][0][1].config(image=self.icon_model_complete)
                self.phases["elements"][0][1].image = self.icon_model_complete
                self.phases["elements"][1][1].config(image=self.icon_model_loading)
                self.phases["elements"][1][1].image = self.icon_model_loading
                self.model_cancel_button.config(state="disabled")
                # Avvio del thread di creazione del modello
                self.model_thread.start()
                self.model_thread_finished()
            else:  # Se il thread è stato interrotto
                self.model_title.config(text="Model creation interrupted")
                # Impostazione delle icone di attesa
                self.phases["elements"][0][1].config(image=self.icon_model_wait)
                self.phases["elements"][0][1].image = self.icon_model_wait
                self.phases["elements"][0][0].config(text="")
                # Abilitazione dei pulsanti
                self.model_play_button.config(state="normal")
                self.model_back_button.config(state="normal")
                self.dataset_thread_interrupted = False
            # Attendo la fine del thread di creazione del dataset
            self.dataset_thread.join()
            # Ricreo i thread
            self.create_threads()
    

    def model_thread_finished(self):
        """
        Funzione che gestisce la fine del thread di creazione del modello.
        """

        if self.model_thread.is_alive():  # Se il thread è attivo
            self.root.after(100, self.model_thread_finished)  # Richiama la funzione dopo 100 ms
        else:  # Se il thread è concluso
            if not self.model_thread_interrupted:  # Se il thread non è stato interrotto
                self.model_title.config(text="Model creation complete")
                # Impostazione delle icone di completamento
                self.phases["elements"][1][1].config(image=self.icon_model_complete)
                self.phases["elements"][1][1].image = self.icon_model_complete
                # Abilitazione e disabilitazione dei pulsanti
                self.model_play_button.config(state="normal")
                self.model_cancel_button.config(state="disabled")
                self.model_back_button.config(state="normal")
            else:  # Se il thread è stato interrotto
                self.model_title.config(text="Model creation interrupted")
                # Impostazione delle icone di attesa
                self.phases["elements"][0][1].config(image=self.icon_model_wait)
                self.phases["elements"][0][1].image = self.icon_model_wait
                self.phases["elements"][1][1].config(image=self.icon_model_wait)
                self.phases["elements"][1][1].image = self.icon_model_wait
                self.phases["elements"][0][0].config(text="")
                self.phases["elements"][1][0].config(text="")
                # Abilitazione dei pulsanti
                self.model_play_button.config(state="normal")
                self.model_back_button.config(state="normal")
                self.model_thread_interrupted = False
            # Attendo la fine del thread di creazione del modello
            self.model_thread.join()
            # Ricreo i thread
            self.create_threads()


    def on_cancel_button_click(self):
        """
        Funzione che gestisce il click sul pulsante di cancellazione della creazione del modello.
        """

        if self.dataset_thread.is_alive():  # Se il thread del dataset è attivo
            # Disabilita il pulsante e imposta il titolo
            self.model_cancel_button.config(state="disabled")
            self.model_title.config(text="Interrupting the process...")
            self.dataset_thread_interrupted = True
            # Interrompe il thread del dataset
            Dataset().stop()
        elif self.model_thread.is_alive():  # Se il thread del modello è attivo
            # Disabilita il pulsante e imposta il titolo
            self.model_cancel_button.config(state="disabled")
            self.model_title.config(text="Interrupting the process...")
            self.model_thread_interrupted = True

def start_application():
    """
    Funzione che avvia l'applicazione Tkinter.
    """

    root = tk.Tk()
    app = GUI(root)
    root.mainloop()