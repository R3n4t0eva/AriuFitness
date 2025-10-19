import cv2
import mediapipe as mp
from logic.functions import Functions # Importa la TUA classe Functions

class Classification:
    def __init__(self, model_path=None):
        print(f"Classification inializzata. Il percorso del modello '{model_path}' è stato ricevuto.")
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.exercise_logic = Functions()
        self.current_exercise_name = None

    def set_active_exercise(self, exercise_name):
        """
        Imposta l'esercizio corrente, traducendo il nome dell'interfaccia
        nella chiave interna usata dalla logica di conteggio.
        """
        # --- MAPPA AGGIORNATA CON I TUOI NOMI ESATTI ---
        NAME_TO_KEY_MAP = {
            "estensioni delle braccia": "arms_extension",
            "estensioni delle braccia sulla testa": "arms_up",
            "alzate laterali": "arms_lateral",
            "squat da seduto": "chair_raises",
            "alzata gambe laterale": "leg_lateral",
            "addominali da seduto": "seated_crunch"
        }

        lower_exercise_name = exercise_name.lower()
        internal_key = NAME_TO_KEY_MAP.get(lower_exercise_name)

        if internal_key:
            self.current_exercise_name = internal_key
            self.exercise_logic.set_current_exercise(internal_key)
            self.exercise_logic.reset_category_repetitions(internal_key)
            print(f"Esercizio RICONOSCIUTO. GUI: '{exercise_name}' -> Chiave Interna: '{self.current_exercise_name}'")
        else:
            self.current_exercise_name = None
            print(f"ERRORE: Esercizio '{exercise_name}' non trovato nella mappa. Controllare NAME_TO_KEY_MAP.")

    def reset_current_reps(self):
        if self.current_exercise_name:
            self.exercise_logic.reset_category_repetitions(self.current_exercise_name)

    def classify(self, frame, callback=None):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image)
        
        exercise_name = "Seleziona un esercizio"
        reps = 0
        phrase = "Nessuna persona rilevata o nessun esercizio selezionato."
        keypoints = []

        if self.current_exercise_name and results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            self.exercise_logic.track(landmarks)
            reps = self.exercise_logic.get_category_repetitions(self.current_exercise_name)
            phrase = self.exercise_logic.get_category_phrase(self.current_exercise_name)
            exercise_name = self.current_exercise_name.replace("_", " ").title()
            keypoints = [{"x": lm.x, "y": lm.y} for lm in landmarks]

        if callback:
            callback(frame_w=frame, exercise=exercise_name, rep=reps, trainer_phrase=phrase, keypoints=keypoints)
        else:
            return exercise_name, reps, phrase, keypoints