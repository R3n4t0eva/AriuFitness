# In src/logic/functions.py
import random
from logic import util

# Dizionario dei keypoint di MediaPipe per una facile lettura
LANDMARK_DICT = {
    "LEFT_SHOULDER": 11, "RIGHT_SHOULDER": 12, "LEFT_ELBOW": 13, "RIGHT_ELBOW": 14,
    "LEFT_WRIST": 15, "RIGHT_WRIST": 16, "LEFT_HIP": 23, "RIGHT_HIP": 24,
    "LEFT_KNEE": 25, "RIGHT_KNEE": 26, "LEFT_ANKLE": 27, "RIGHT_ANKLE": 28
}

# --- 1. MESSAGGI DI FEEDBACK CENTRALIZZATI ---
FEEDBACK_MESSAGES = {
    'arms_extension': {
        'start': 'Inizia con le braccia piegate',
        'motivational': ['Forza!', 'Ottimo ritmo!', 'Stai andando alla grande!'],
        'correction_up': 'Piega di più le braccia',
        'correction_down': 'Stendi completamente le braccia',
        'good_rep': 'Perfetto!'
    },
    'chair_raises': {
        'start': 'Inizia seduto sulla sedia',
        'motivational': ['Schiena dritta!', 'Ben fatto!', 'Ancora uno!'],
        'correction_up': 'Stendi bene le gambe quando sali',
        'correction_down': 'Scendi più in basso, controllando il movimento',
        'good_rep': 'Ottimo movimento!'
    },
    'arms_up': {
        'start': 'Inizia con le braccia lungo i fianchi',
        'motivational': ['Sguardo in avanti!', 'Molto bene!', 'Forza, ci sei quasi!'],
        'correction_up': 'Alza le braccia più in alto',
        'correction_down': 'Abbassa le braccia completamente',
        'good_rep': 'Eccellente!'
    },
    'arms_lateral': {
        'start': 'Inizia con le braccia lungo i fianchi',
        'motivational': ['Non avere fretta', 'Movimento controllato', 'Stai facendo un ottimo lavoro'],
        'correction_up': 'Apri le braccia fino all\'altezza delle spalle',
        'correction_down': 'Torna alla posizione di partenza',
        'good_rep': 'Bene così!'
    },
    'leg_lateral': {
        'start': 'Inizia con i piedi uniti',
        'motivational': ['Mantieni l\'equilibrio', 'Non inarcare la schiena', 'Ottimo!'],
        'correction_up': 'Alza la gamba un po\' di più',
        'correction_down': 'Avvicina di più i piedi',
        'good_rep': 'Forza!'
    },
    'seated_crunch': {
        'start': 'Inizia con la schiena dritta',
        'motivational': ['Contrai gli addominali', 'Respira', 'Perfetto!'],
        'correction_up': 'Torna più indietro con la schiena',
        'correction_down': 'Avvicinati di più alle ginocchia',
        'good_rep': 'Ottimo crunch!'
    }
}


# --- 2. CLASSE FUNCTIONS COMPLETA ---
class Functions:
    def __init__(self):
        self.exercise_states = {
            'arms_extension': {'reps': 0, 'stage': 'up', 'phrase': FEEDBACK_MESSAGES['arms_extension']['start']},
            'arms_up': {'reps': 0, 'stage': 'down', 'phrase': FEEDBACK_MESSAGES['arms_up']['start']},
            'arms_lateral': {'reps': 0, 'stage': 'down', 'phrase': FEEDBACK_MESSAGES['arms_lateral']['start']},
            'chair_raises': {'reps': 0, 'stage': 'down', 'phrase': FEEDBACK_MESSAGES['chair_raises']['start']},
            'leg_lateral': {'reps': 0, 'stage': 'down', 'phrase': FEEDBACK_MESSAGES['leg_lateral']['start']},
            'seated_crunch': {'reps': 0, 'stage': 'up', 'phrase': FEEDBACK_MESSAGES['seated_crunch']['start']}
        }
        self.feedback_counter = 0
        self.feedback_cooldown = 90  # Mostra un complimento ogni 90 frame (circa 3 secondi)

    def set_current_exercise(self, exercise):
        self.current_exercise = exercise
        print(f"Esercizio impostato su: {self.current_exercise}")

    def reset_reps(self):
        """Azzera il conteggio delle ripetizioni per l'esercizio corrente."""
        if self.current_exercise and self.current_exercise in self.exercise_states:
            self.exercise_states[self.current_exercise]['reps'] = 0
            print(f"Repetizioni per {self.current_exercise} azzerate.") 

    def track(self, landmarks):
        if not self.current_exercise:
            return None
        
        tracker_map = {
            'chair_raises': self._track_chair_raises,
            'arms_extension': self._track_arms_extension,
            'arms_up': self._track_arms_up,
            'arms_lateral': self._track_arms_lateral,
            'leg_lateral': self._track_leg_lateral,
            'seated_crunch': self._track_seated_crunch
        }

        if self.current_exercise in tracker_map:
            return tracker_map[self.current_exercise](landmarks)
        
        return None

    def update(self, landmarks, exercise_name):
        """Funzione principale che chiama la logica specifica per l'esercizio."""
        if landmarks is None or landmarks.size == 0 or exercise_name not in self.exercise_states:
            return

        # Chiama la funzione di tracking specifica per l'esercizio attivo
        tracker_method = getattr(self, f'_track_{exercise_name}', None)
        if tracker_method:
            tracker_method(landmarks)

    def _update_feedback(self, state, exercise_name, correction_made):
        """Gestisce il feedback motivazionale in modo stabile."""
        if not correction_made:
            self.feedback_counter += 1
            if self.feedback_counter >= self.feedback_cooldown:
                state['phrase'] = random.choice(FEEDBACK_MESSAGES[exercise_name]['motivational'])
                self.feedback_counter = 0

    # --- LOGICHE DI TRACKING PER OGNI ESERCIZIO ---

    def _track_arms_extension(self, landmarks):
        if LANDMARK_DICT['RIGHT_WRIST'] >= len(landmarks): return
        state = self.exercise_states['arms_extension']
        shoulder = landmarks[LANDMARK_DICT['RIGHT_SHOULDER']]
        elbow = landmarks[LANDMARK_DICT['RIGHT_ELBOW']]
        wrist = landmarks[LANDMARK_DICT['RIGHT_WRIST']]
        angle = util.calculate_angle(shoulder, elbow, wrist)
        
        correction_made = False
        
        if state['stage'] == 'up': # Braccio dovrebbe essere piegato
            if angle > 75: 
                state['phrase'] = FEEDBACK_MESSAGES['arms_extension']['correction_up']
                correction_made = True
            if angle > 145: state['stage'] = 'down'
        
        elif state['stage'] == 'down': # Braccio dovrebbe essere teso
            if angle < 140: 
                state['phrase'] = FEEDBACK_MESSAGES['arms_extension']['correction_down']
                correction_made = True
            if angle < 70:
                state['stage'] = 'up'
                state['reps'] += 1
                state['phrase'] = f"{FEEDBACK_MESSAGES['arms_extension']['good_rep']} {state['reps']}"
                self.feedback_counter = 0
                return
        
        self._update_feedback(state, 'arms_extension', correction_made)
            
    def _track_chair_raises(self, landmarks):
        state = self.exercise_states['chair_raises']
        left_angle, right_angle = 180.0, 180.0
        try:
            left_hip = landmarks[LANDMARK_DICT['LEFT_HIP']]
            left_knee = landmarks[LANDMARK_DICT['LEFT_KNEE']]
            left_ankle = landmarks[LANDMARK_DICT['LEFT_ANKLE']]
            left_angle = util.calculate_angle(left_hip, left_knee, left_ankle)
        except: pass
        try:
            right_hip = landmarks[LANDMARK_DICT['RIGHT_HIP']]
            right_knee = landmarks[LANDMARK_DICT['RIGHT_KNEE']]
            right_ankle = landmarks[LANDMARK_DICT['RIGHT_ANKLE']]
            right_angle = util.calculate_angle(right_hip, right_knee, right_ankle)
        except: pass

        correction_made = False

        if state['stage'] == 'up':
            if left_angle < 140 or right_angle < 140:
                state['stage'] = 'down'
                state['reps'] += 1
                state['phrase'] = f"{FEEDBACK_MESSAGES['chair_raises']['good_rep']} {state['reps']}"
                self.feedback_counter = 0
        elif state['stage'] == 'down':
            if left_angle > 150 and right_angle > 150:
                state['stage'] = 'up'
        
        self._update_feedback(state, 'chair_raises', correction_made)

    def _track_arms_up(self, landmarks):
        if LANDMARK_DICT['RIGHT_ELBOW'] >= len(landmarks): return
        state = self.exercise_states['arms_up']
        hip = landmarks[LANDMARK_DICT['RIGHT_HIP']]
        shoulder = landmarks[LANDMARK_DICT['RIGHT_SHOULDER']]
        elbow = landmarks[LANDMARK_DICT['RIGHT_ELBOW']]
        angle = util.calculate_angle(hip, shoulder, elbow)
        
        correction_made = False

        if state['stage'] == 'down': # Braccia in basso
            if angle > 45: 
                state['phrase'] = FEEDBACK_MESSAGES['arms_up']['correction_down']
                correction_made = True
            if angle > 140: state['stage'] = 'up'
        
        elif state['stage'] == 'up': # Braccia in alto
            if angle < 135: 
                state['phrase'] = FEEDBACK_MESSAGES['arms_up']['correction_up']
                correction_made = True
            if angle < 40:
                state['stage'] = 'down'
                state['reps'] += 1
                state['phrase'] = f"{FEEDBACK_MESSAGES['arms_up']['good_rep']} {state['reps']}"
                self.feedback_counter = 0
                return

        self._update_feedback(state, 'arms_up', correction_made)

    def _track_arms_lateral(self, landmarks):
        if LANDMARK_DICT['RIGHT_ELBOW'] >= len(landmarks): return
        state = self.exercise_states['arms_lateral']
        hip = landmarks[LANDMARK_DICT['RIGHT_HIP']]
        shoulder = landmarks[LANDMARK_DICT['RIGHT_SHOULDER']]
        elbow = landmarks[LANDMARK_DICT['RIGHT_ELBOW']]
        angle = util.calculate_angle(hip, shoulder, elbow)
        correction_made = False

        if state['stage'] == 'down': # Braccia lungo i fianchi
            if angle > 35: 
                state['phrase'] = FEEDBACK_MESSAGES['arms_lateral']['correction_down']
                correction_made = True
            if angle > 80: state['stage'] = 'up'
        
        elif state['stage'] == 'up': # Braccia aperte a 90 gradi
            if angle < 75: 
                state['phrase'] = FEEDBACK_MESSAGES['arms_lateral']['correction_up']
                correction_made = True
            if angle < 30:
                state['stage'] = 'down'
                state['reps'] += 1
                state['phrase'] = f"{FEEDBACK_MESSAGES['arms_lateral']['good_rep']} {state['reps']}"
                self.feedback_counter = 0
                return

        self._update_feedback(state, 'arms_lateral', correction_made)

    def _track_leg_lateral(self, landmarks):
        if LANDMARK_DICT['RIGHT_KNEE'] >= len(landmarks): return
        state = self.exercise_states['leg_lateral']
        left_hip = landmarks[LANDMARK_DICT['LEFT_HIP']]
        right_hip = landmarks[LANDMARK_DICT['RIGHT_HIP']]
        right_knee = landmarks[LANDMARK_DICT['RIGHT_KNEE']]
        angle = util.calculate_angle(left_hip, right_hip, right_knee)
        
        
        correction_made = False

        if state['stage'] == 'down': # Gambe unite (angolo ~80-90)
            # Se l'angolo supera 100, significa che la gamba si sta alzando
            if angle > 100: 
                state['stage'] = 'up'
        
        elif state['stage'] == 'up': # Gamba alzata (angolo > 100)
            # Se l'angolo torna sotto 90, la ripetizione è completa
            if angle < 90:
                state['stage'] = 'down'
                state['reps'] += 1
                state['phrase'] = f"{FEEDBACK_MESSAGES['leg_lateral']['good_rep']} {state['reps']}"
                self.feedback_counter = 0
                return

        self._update_feedback(state, 'leg_lateral', correction_made)

    def _track_seated_crunch(self, landmarks):
        if LANDMARK_DICT['RIGHT_KNEE'] >= len(landmarks): return
        state = self.exercise_states['seated_crunch']
        shoulder = landmarks[LANDMARK_DICT['RIGHT_SHOULDER']]
        hip = landmarks[LANDMARK_DICT['RIGHT_HIP']]
        knee = landmarks[LANDMARK_DICT['RIGHT_KNEE']]
        angle = util.calculate_angle(shoulder, hip, knee)
        
        correction_made = False

        if state['stage'] == 'up': # Schiena indietro (angolo > 130)
            # Se l'angolo scende sotto 115, l'utente si sta piegando in avanti
            if angle < 115: 
                state['stage'] = 'down'
        
        elif state['stage'] == 'down': # Crunch completato (angolo < 115)
            # Se l'angolo torna sopra 130, la ripetizione è completa
            if angle > 130:
                state['stage'] = 'up'
                state['reps'] += 1
                state['phrase'] = f"{FEEDBACK_MESSAGES['seated_crunch']['good_rep']} {state['reps']}"
                self.feedback_counter = 0
                return
        
        self._update_feedback(state, 'seated_crunch', correction_made)

    # --- FUNZIONI DI SUPPORTO ---
    def get_category_repetitions(self, exercise_name):
        return self.exercise_states.get(exercise_name, {}).get('reps', 0)

    def get_category_phrase(self, exercise_name):
        return self.exercise_states.get(exercise_name, {}).get('phrase', '')
        
    def reset_category_repetitions(self, exercise_name):
        if exercise_name in self.exercise_states:
            self.exercise_states[exercise_name]['reps'] = 0
            self.exercise_states[exercise_name]['phrase'] = FEEDBACK_MESSAGES.get(exercise_name, {}).get('start', 'Inizia Esercizio')
            if exercise_name in ['arms_extension', 'seated_crunch']:
                 self.exercise_states[exercise_name]['stage'] = 'up'
            else:
                 self.exercise_states[exercise_name]['stage'] = 'down'
