#import tensorflow as tf
import torch
import numpy as np
import util
import os

from data.frame_mediapipe import Frame
from classification.functions_old import Functions
from classification.users import Users


class Classification:
    """
    Classe che si occupa di classificare l'esercizio eseguito.
    """

    def __init__(self, model_path, threshold=0.8):
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
        self.users = Users()

        # Inizializzo le variabili
        self.frames = []  # Finestra di frames
        self.last_frame = None  # Frame precedente
        self.categories = np.load(os.path.join(util.getDatasetPath(), "categories.npy"))  # Categorie degli esercizi
        self.predicted_exercise = []  # Storico delle predizioni
        self.effective_exercise = "None"  # Esercizio effettivo
        self.last_predicted_exercise = "None"  # 
        self.empty_count = 0  # Contatore per i frame vuoti
        self.stop_count = 0  # Contatore per i frame fermi
        self.functions = Functions()  # Oggetto per le funzioni di supporto


    def same_frame(self, frame1, frame2, threshold=0.05):
        """
        Funzione che riceve in input 2 frame e restituisce True se i keypoints sono molto simili tra loro e False altrimenti.
        La somiglianza è gestita da un valore di soglia.

        Args:
        - frame1 (Frame): primo frame
        - frame2 (Frame): secondo frame
        - threshold (float): valore di soglia per la somiglianza

        Returns:
        - bool: True se i frame sono simili, False altrimenti
        """

        keypoints1 = frame1.get_keypoints()
        keypoints2 = frame2.get_keypoints()
        if len(keypoints1) != len(keypoints2):
            return False
        for i in range(len(keypoints1)):
            if abs(keypoints1[i]["x"] - keypoints2[i]["x"]) > threshold or abs(keypoints1[i]["y"] - keypoints2[i]["y"]) > threshold:
                return False
        return True
    

    def classify(self, frame, callback):
        """
        Funzione che riceve in input un frame e restituisce l'esercizio eseguito, il numero di ripetizioni e la frase associata.

        Args:
        - frame (numpy.ndarray): frame da classificare

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

        # Se il frame è diverso dal precedente, lo aggiungo alla finestra e resetto il contatore di frame fermi
        if len(self.frames) == 0 or not util.same_frame(self.frames[-1], curr_frame, threshold=0.05):
            self.frames.append(curr_frame)
            self.stop_count = 0
        else:  # Altrimenti incremento il contatore di frame fermi
            self.stop_count += 1
            if self.stop_count >= 15:  # Se il contatore supera una certa soglia, resetto lo storico delle predizioni, l'esercizio effettivo e svuoto la finestra
                self.predicted_exercise = ["None", "None", "None"]
                self.effective_exercise = "None"
                self.frames = []

        if len(self.frames) == util.getWindowSize():  # Se la lista ha raggiunto la dimensione della finestra effettuo la classificazione
            # Calcolo i keypoints, gli angoli e l'optical flow per ogni frame nella finestra
            opticalflow = []
            for i in range(len(self.frames)):  # Per ogni frame nella lista calcolo i keypoints, gli angoli e l'optical flow
                self.frames[i].interpolate_keypoints(self.frames[i - 1] if i > 0 else None, self.frames[i + 1] if i < len(self.frames) - 1 else None)
                self.frames[i].extract_angles()
                if i > 0:
                    opticalflow.append(self.frames[i].extract_opticalflow(self.frames[i - 1]))
                else:
                    opticalflow.append(np.zeros((Frame.num_opticalflow_data,)))
                
            # Creo i 3 input per il modello con i dati dei keypoints, degli angoli e dell'optical flow
            kp = np.array([self.frames[i].process_keypoints() for i in range(util.getWindowSize())])
            an = np.array([self.frames[i].process_angles() for i in range(util.getWindowSize())])
            of = np.array(opticalflow)
            X1 = kp.reshape(1, util.getWindowSize(), -1)
            X2 = of.reshape(1, util.getWindowSize(), -1)
            X3 = an.reshape(1, util.getWindowSize(), -1)

            # Eseguo la classificazione
            if self.model_lib == "keras":
                predictions = self.model.predict([X1, X2, X3], verbose=0)
            else:
                predictions = self.model(torch.tensor(X1, dtype=torch.float32), torch.tensor(X3, dtype=torch.float32))
                predictions = predictions.detach().numpy()
            print(predictions)

            # Aggiorno lo storico delle predizioni
            prediction = np.argmax(predictions, axis=1)[0]
            self.predicted_exercise.append(self.categories[prediction] if predictions[0][prediction] > self.threshold else "None")
            # Riduco la lunghezza dello storico a 3 e calcolo l'esercizio effettivo come quello presente piu volte
            if len(self.predicted_exercise) == 7:
                self.predicted_exercise = self.predicted_exercise[1:]
            print(self.predicted_exercise)

            # Calcolo l'esercizio effettivo come quello presente piu volte
            if len(self.predicted_exercise) >= 3:
                self.effective_exercise = max(set(self.predicted_exercise), key=self.predicted_exercise.count)
            else:
                self.effective_exercise = self.predicted_exercise[-1]
                
            # Se viene predetto un esercizio per la prima volta, azzero le sue ripetizioni
            if self.predicted_exercise.count(self.predicted_exercise[-1]) == 1 and self.predicted_exercise[-1] != "None":
                self.functions.reset_category_repetitions(self.predicted_exercise[-1])
                
            # Riduco la finestra di un frame
            self.frames = self.frames[1:]

        if all([landmark["x"] == 0 and landmark["y"] == 0 for landmark in landmarks]):  # Se tutti i keypoints sono nulli, incremento il contatore di frame vuoti
            self.empty_count += 1
            if self.empty_count >= 10:  # Se il contatore supera una certa soglia, resetto lo storico delle predizioni, l'esercizio effettivo e svuoto la finestra
                self.predicted_exercise = ["None", "None", "None"]
                self.effective_exercise = "None"
                self.frames = []
        else:
            self.empty_count = 0

        # Se viene rilevato un nuovo esercizio, aggiorno le informazioni dell'utente
        if self.effective_exercise != self.last_predicted_exercise and self.last_predicted_exercise != "None":
            exer = self.last_predicted_exercise
            reps = self.functions.get_category_repetitions(exer)
            avg_time = self.functions.get_category_avg_time(exer)
            accuracy = self.functions.get_category_accuracy(exer)
            if reps > 2:
                self.users.update_session(exer, reps, accuracy, avg_time)

        # Aggiorno le funzioni di supporto e calcolo il numero di ripetizioni dell'esercizio effettivo
        self.functions.update(curr_frame)
        cat_reps = self.functions.get_category_repetitions(self.effective_exercise) if self.effective_exercise != "None" else 0

        self.last_predicted_exercise = self.effective_exercise
        
        if callback is not None:
            callback(frame, self.effective_exercise, cat_reps, self.functions.get_category_phrase(self.effective_exercise) if self.effective_exercise != "None" else "", landmarks)
        
        return self.effective_exercise, cat_reps, self.functions.get_category_phrase(self.effective_exercise) if self.effective_exercise != "None" else "", landmarks
