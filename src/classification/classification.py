#import tensorflow as tf
import torch
import numpy as np
import util
import os

from data.frame_mediapipe import Frame
from classification.functions import Functions
from data.dataset import Dataset


class Classification:
    """
    Classe che si occupa di classificare l'esercizio eseguito.
    """

    def __init__(self, model_path, threshold=0.7):
        """
        Costruttore della classe.

        Args:
        - model_path (String): percorso del modello da utilizzare per la classificazione
        """

        # Se model path è un file che finisce con .h5, allora carico un modello keras
        if model_path.endswith(".h5"):
            #self.model = tf.keras.models.load_model(model_path)
            #self.model_lib = "keras"
            pass
        else:
            self.model = util.get_pytorch_model(model_path)
            self.model_lib = "pytorch"

        self.threshold = threshold

        # Inizializzo le variabili
        self.frames = []  # Finestra di frames
        self.keypoints = []  # Finestra di keypoints
        self.angles = [] # Finestra di angoli
        self.categories = np.load(os.path.join(util.getDatasetPath(), "categories.npy"))  # Categorie degli esercizi
        self.effective_exercise = "None"  # Esercizio effettivo
        self.last_predicted_exercise = "None"  # Ultima predizione
        self.empty_count = 0  # Contatore per i frame vuoti
        self.functions = Functions()  # Oggetto per le funzioni di supporto
        self.stop = False  # Flag per indicare l'interruzione dell'esercizio

    
    def stop_exercise(self):
        """
        Funzione per fermare l'esercizio.
        """

        self.stop = True
    

    def classify(self, frame, callback):
        """
        Funzione che riceve in input un frame e restituisce l'esercizio eseguito, il numero di ripetizioni e la frase associata.

        Args:
        - frame (numpy.ndarray): frame da classificare
        - callback (function): funzione di callback per aggiornare la GUI

        Returns:
        - effective_exercise (String): esercizio eseguito
        - rep (int): numero di ripetizioni
        - phrase (String): frase associata all'esercizio
        """

        # costruisco il frame corrente ed estraggo i keypoints
        curr_frame = Frame(frame)
        landmarks_o = curr_frame.get_keypoints()
        landmarks = []
        for landmark in landmarks_o:  # Creo una copia dei landmarks per evitare che vengano modificati i landmarks originali
            landmarks.append({
                "x": landmark["x"],
                "y": landmark["y"]
            })

        # Se il frame è diverso dal precedente, lo aggiungo alla finestra
        if len(self.frames) == 0 or not util.same_frame(self.frames[-1], curr_frame, threshold=0.05):
            curr_frame.interpolate_keypoints(self.frames[-1] if len(self.frames) > 0 else None, None)
            curr_frame.extract_angles()
            self.keypoints.append(curr_frame.process_keypoints())
            self.angles.append(curr_frame.process_angles())
            self.frames.append(curr_frame)

        # Se tutti i keypoints sono nulli, incremento il contatore di frame vuoti
        # Se il contatore supera una certa soglia, resetto lo storico delle predizioni, l'esercizio effettivo e svuoto la finestra
        if all([landmark["x"] == 0 and landmark["y"] == 0 for landmark in landmarks]):
            self.empty_count += 1
            if self.empty_count >= 30:
                self.effective_exercise = "None"
                self.frames = []
                self.keypoints = []
                self.angles = []
        else:
            self.empty_count = 0

        # Ottengo le categorie di esercizi per cui è stata contata una ripetizione con l'ultimo frame
        exercises_changed = self.functions.update(curr_frame)

        if len(exercises_changed) > 0:  # Se ci sono esercizi per cui è stata contata una ripetizione
            # Riduco le finestre di keypoints e angoli, mantenendo solo quelle che possono essere utilizzate per la classificazione
            max_last_frame = max([self.functions.get_last_frame(exercise) for exercise in exercises_changed])
            self.keypoints = self.keypoints[-(max_last_frame + 5):]
            self.angles = self.angles[-(max_last_frame + 5):]
            self.frames = self.frames[-(max_last_frame + 5):]

            for exercise in exercises_changed:  # per ogni esercizio per cui è stata contata una ripetizione
                last_frame = self.functions.get_last_frame(exercise)  # Ottengo l'ultimo frame in cui è stata contata una ripetizione
                # Ottengo il range di frames da utilizzare per la classificazione come il minimo tra last_frame e l'ultimo frame in cui sembra essere iniziata una ripetizione
                range_frames = min((last_frame + 5), self.functions.get_max_last_frame(exercise)) 

                # Se il range da prendere in considerazione è maggiore della dimensione della finestra e ci sono abbastanza keypoints e angoli
                if range_frames >= Dataset.window_size and len(self.keypoints) >= Dataset.window_size:
                    # Riduco i keypoints e gli angoli ai soli che verranno utilizzati per la classificazione
                    kp = self.keypoints[-range_frames:]
                    an = self.angles[-range_frames:]
                    # Riduco i keypoints e gli angoli ad una dimensione compatibile con la finestra del modello
                    interval = len(kp) // Dataset.window_size
                    X1 = [[kp[i] for i in range(0, len(kp), interval)]]
                    X2 = [[an[i] for i in range(0, len(an), interval)]]
                    # Eseguo la classificazione in base al modello utilizzato
                    if self.model_lib == "keras":
                        predictions = self.model.predict([X1, X2], verbose=0)
                    else:
                        predictions = self.model(torch.tensor(X1, dtype=torch.float32), torch.tensor(X2, dtype=torch.float32))
                        predictions = predictions.detach().numpy()
                    # Stampo le predizioni
                    for i in range(len(self.categories)):
                        print(f"{self.categories[i]}: , {predictions[0][i]}", end="; ")
                    print("\n")

                    prediction = np.argmax(predictions, axis=1)[0]  # Ottengo la predizione come indice della categoria con probabilità maggiore
                    prediction = self.categories[prediction] if predictions[0][prediction] > self.threshold else "None"  # Ottengo l'esercizio predetto (o None se la probabilità è troppo bassa)

                    if prediction == exercise:  # Se l'esercizio predetto è uguale a quello per cui è stata contata una ripetizione
                        self.effective_exercise = prediction  # La predizione diventa l'esercizio effettivo

                        # Se l'esercizio effettivo è diverso dall'ultimo esercizio predetto e l'ultimo esercizio predetto non era None, resetto le ripetizioni dell'esercizio predetto
                        if self.effective_exercise != self.last_predicted_exercise and self.last_predicted_exercise != "None":
                            self.functions.reset_category_repetitions(self.effective_exercise)
                        # Aggiungo una ripetizione all'esercizio effettivo e resetto l'ultimo frame per tutte le categorie di esercizi
                        self.functions.add_category_repetition(self.effective_exercise)
                        self.timestampt_last_rep = util.get_current_time()
                        self.functions.reset_all_last_frame()
                        self.last_predicted_exercise = self.effective_exercise

        # Se la flag di stop esercizio è attiva, pongo a None l'esercizio effettivo
        if self.stop:
            self.effective_exercise = "None"
            self.frames = []
            self.keypoints = []
            self.angles = []
            self.stop = False

        # Ripetizioni dell'esercizio effettivo
        cat_reps = self.functions.get_category_repetitions(self.effective_exercise) if self.effective_exercise != "None" else 0
        
        # Callback e return dei risultati
        if callback is not None:
            callback(frame, self.effective_exercise, cat_reps, self.functions.get_category_phrase(self.effective_exercise) if self.effective_exercise != "None" else "", landmarks)
        
        return self.effective_exercise, cat_reps, self.functions.get_category_phrase(self.effective_exercise) if self.effective_exercise != "None" else "", landmarks