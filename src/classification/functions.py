import math
import os
import numpy as np
import util

from data.video_params import VideoParams as vp

class Functions:
    """
    Classe che si occupa del conteggio delle ripetizioni e della generazione di feedback per l'utente.
    """

    def __init__(self):
        """
        Costruttore della classe. Inizializzo le variabili necessarie.
        """

        self.repetitions = {}
        self.reset_repetitions()
        self.parameters = {}
        self.extract_parameters()

        # dizionario che contiene i valori massimi e minimi calcolati degli angoli per ogni categoria di esercizio
        # max e min angle sono i valori massimi e minimi registrati durante l'esecuzione dell'esercizio
        # reverse indica se l'esercizio è inverso (True se inizia con l'angolo massimo e termina con l'angolo minimo, False altrimenti)
        self.executions = {
            'arms_extension': {
                'max_angle': 0,
                'min_angle': 180,
                'reverse': False
            },
            'arms_up': {
                'max_angle': 0,
                'min_angle': 180,
                'reverse': True
            },
            'chair_raises': {
                'max_angle': 0,
                'min_angle': 180,
                'reverse': False
            },
            'arms_lateral': {
                'max_angle': 0,
                'min_angle': 180,
                'reverse': False
            },
            'leg_lateral': {
                'max_angle': 0,
                'min_angle': 180,
                'reverse': False
            },
            'seated_crunch': {
                'max_angle': 0,
                'min_angle': 180,
                'reverse': False
            }
        }

        # dizionario che contiene i feedback per ogni categoria di esercizio.
        # Ogni feedback è composto da un messaggio e un booleano che indica se il feedback è positivo o negativo
        self.feedbacks = {
            'arms_extension': {
                'current': "good",
                'good': ("You're doing well!\nKeep it up", True),
                'start_over': ("Don't close your arms\ntoo much", False),
                'start_under': ("Bring your arms\ncloser together", False),
                'end_over': ("Don't open your arms\ntoo much", False),
                'end_under': ("Open your arms wider", False)
            },
            'arms_up': {
                'current': "good",
                'good': ("You're doing well!\nKeep it up", True),
                'start_over': ("You're doing well!\nKeep it up", True),
                'start_under': ("Lower your arms more", False),
                'end_over': ("You're doing well!\nKeep it up", True),
                'end_under': ("Raise your arms higher", False)
            },
            'chair_raises': {
                'current': "good",
                'good': ("You're doing well!\nKeep it up", True),
                'start_over': ("You're doing well!\nKeep it up", True),
                'start_under': ("Sit correctly on the chair", False),
                'end_over': ("You're doing well!\nKeep it up", True),
                'end_under': ("Stretch your legs\nwhen you stand up", False)
            },
            'arms_lateral': {
                'current': "good",
                'good': ("You're doing well!\nKeep it up", True),
                'start_over': ("Don't bring your arms\ntoo close to your body", False),
                'start_under': ("Bring your arms closer\nto your body", False),
                'end_over': ("Don't raise your arms\ntoo high", False),
                'end_under': ("Raise your arms higher", False)
            },
            'leg_lateral': {
                'current': "good",
                'good': ("You're doing well!\nKeep it up", True),
                'start_over': ("Don't close your leg\ntoo much", False),
                'start_under': ("Close your leg more", False),
                'end_over': ("Don't lift your leg\ntoo much", False),
                'end_under': ("Raise your leg higher", False)
            },
            'seated_crunch': {
                'current': "good",
                'good': ("You're doing well!\nKeep it up", True),
                'start_over': ("You're doing well!\nKeep it up", True),
                'start_under': ("Lean back more", False),
                'end_over': ("Don't lean forward\ntoo much", False),
                'end_under': ("Lean forward more", False)
            }
        }

        # dizionario che contiene:
        # last_frame: frame in cui è stata contata l'ultima ripetizione
        # current_frame: conteggio dei frame dall'ultima ripetizione
        # max: frame da cui si pensa inizi l'ultima ripetizione
        # max_state: stato per capire quando inizializzare max
        self.last_frame = {
            'arms_extension': {
                "last": 0,
                "current": 0,
                "max": 0,
                "max_state": "in"
            },
            'arms_up': {
                "last": 0,
                "current": 0,
                "max": 0,
                "max_state": "in"
            },
            'chair_raises': {
                "last": 0,
                "current": 0,
                "max": 0,
                "max_state": "in"
            },
            'arms_lateral': {
                "last": 0,
                "current": 0,
                "max": 0,
                "max_state": "in"
            },
            'leg_lateral': {
                "last": 0,
                "current": 0,
                "max": 0,
                "max_state": "in"
            },
            'seated_crunch': {
                "last": 0,
                "current": 0,
                "max": 0,
                "max_state": "in"
            }
        }


    def reset_repetitions(self):
        """
        Funzione che resetta conteggio ripetizioni, tempi di esecuzione e accuratezza per ogni categoria di esercizio.
        """

        self.repetitions = {
            'arms_extension': {
                'count': 0,
                'state': 'start',
                'start_time': 0,
                'times': [],
                'accuracy': (0, 0)
            },
            'arms_up': {
                'count': 0,
                'state': 'start',
                'start_time': 0,
                'times': [],
                'accuracy': (0, 0)
            },
            'chair_raises': {
                'count': 0,
                'state': 'start',
                'start_time': 0,
                'times': [],
                'accuracy': (0, 0)
            },
            'arms_lateral': {
                'count': 0,
                'state': 'start',
                'start_time': 0,
                'times': [],
                'accuracy': (0, 0)
            },
            'leg_lateral': {
                'count': 0,
                'state': 'start',
                'start_time': 0,
                'times': [],
                'accuracy': (0, 0)
            },
            'seated_crunch': {
                'count': 0,
                'state': 'start',
                'start_time': 0,
                'times': [],
                'accuracy': (0, 0)
            }
        }


    def extract_parameters(self):
        """
        Funzione che estrae i parametri necessari per il calcolo delle ripetizioni e la generazione di feedback.
        """
        
        self.parameters = np.load(os.path.join(util.getParametersPath(), "parameters.npy"), allow_pickle=True).item()


    def update(self, frame):
        """
        Funzione che aggiorna lo stato delle ripetizioni e dei feedback per ogni categoria di esercizio.

        Args:
            frame (numpy.ndarray): frame da processare

        Returns:
            list: lista delle categorie di esercizi che hanno cambiato stato da end a start (quindi per cui verrebbe contata una ripetizione)
        """

        for category in self.last_frame.keys():
            self.last_frame[category]["current"] += 1

        exercises_changed = self.update_repetitions(frame)
        self.update_feedbacks(frame)
        return exercises_changed
    

    def update_repetitions(self, frame, tollerance=30):
        """
        Funzione che aggiorna lo stato delle categorie di esercizi (start/end)

        Args:
            frame (numpy.ndarray): frame da processare
            tollerance (int): tolleranza per il calcolo delle ripetizioni

        Returns:
            list: lista delle categorie di esercizi che hanno cambiato stato da end a start (quindi per cui verrebbe contata una ripetizione)
        """

        exercises_changed = []
        curr_keypoints = frame.get_keypoints()

        tollerance = tollerance/100

        for category in self.repetitions.keys():  # per ogni categoria di esercizio
            # angolo corrente dell'esercizio
            curr_angle = util.calculate_angle(vp.extract_points(frame, vp.category_angles[category][0]), vp.extract_points(frame, vp.category_angles[category][1]), vp.extract_points(frame, vp.category_angles[category][2]))
            # angoli minimo e massimo del tipo di esercizio corrente
            cat_min_angle = self.parameters[category]["angles_min"]
            cat_max_angle = self.parameters[category]["angles_max"]
            # intervallo di tolleranza per il calcolo delle ripetizioni
            interval = (cat_max_angle - cat_min_angle) * tollerance

            # Aggiornamento del frame in cui si pensa inizi la ripetizione corrente
            # aggiornato quando l'angolo attuale esce dall'intervallo di tolleranza dell'angolo relativo allo stato "start"
            if not self.executions[category]['reverse']:  # se l'esercizio non è inverso
                if curr_angle > cat_min_angle + interval and self.last_frame[category]["max_state"] == "in":
                    self.last_frame[category]["max_state"] = "out"
                    self.last_frame[category]["max"] = self.last_frame[category]["current"] + 5
                elif curr_angle < cat_min_angle + interval and self.last_frame[category]["max_state"] == "out":
                    self.last_frame[category]["max_state"] = "in"
            else:
                if curr_angle < cat_max_angle - interval and self.last_frame[category]["max_state"] == "in":
                    self.last_frame[category]["max_state"] = "out"
                    self.last_frame[category]["max"] = self.last_frame[category]["current"] + 5
                elif curr_angle > cat_max_angle - interval and self.last_frame[category]["max_state"] == "out":
                    self.last_frame[category]["max_state"] = "in"

            # Aggiornamento del conteggio delle ripetizioni
            if not self.executions[category]['reverse']:  # se l'esercizio non è inverso
                if self.repetitions[category]['state'] == 'start':  # se lo stato dell'esercizio è start
                    if curr_angle > cat_max_angle - interval:  # se l'angolo attuale rientra nell'intervallo di tolleranza del massimo
                        self.repetitions[category]['state'] = 'end'  # cambio lo stato dell'esercizio in end (metà esercizio)
                        self.executions[category]['max_angle'] = 0  # resetto l'angolo massimo
                        self.update_feedback_msg(category)  # aggiorno il feedback dell'esercizio
                elif self.repetitions[category]['state'] == 'end':  # se lo stato dell'esercizio è end
                    if curr_angle < cat_min_angle + interval:  # se l'angolo attuale rientra nell'intervallo di tolleranza del minimo
                        self.last_frame[category]["last"] = self.last_frame[category]["current"]  # aggiorno l'ulltimo frame da cui parte la ripetizione successiva
                        self.last_frame[category]["current"] = 0  # resetto il conteggio dei frame per l'attuale ripetizione
                        exercises_changed.append(category) if category not in exercises_changed else None  # aggiungo la categoria all'elenco degli esercizi che hanno cambiato stato
                        self.repetitions[category]['state'] = 'start'  # cambio lo stato dell'esercizio in start (inizio esercizio)
                        self.executions[category]['min_angle'] = 180  # resetto l'angolo minimo
                        self.update_feedback_msg(category)  # aggiorno il feedback dell'esercizio
                        self.update_times(category)  # aggiorno i tempi di esecuzione
            else:  # se l'esercizio è inverso (cambia solo l'ordine di minimo e massimo)
                if self.repetitions[category]['state'] == 'start':
                    if curr_angle < cat_min_angle + interval:
                        self.repetitions[category]['state'] = 'end'
                        self.executions[category]['min_angle'] = 180
                        self.update_feedback_msg(category)
                elif self.repetitions[category]['state'] == 'end':
                    if curr_angle > cat_max_angle - interval:
                        self.last_frame[category]["last"] = self.last_frame[category]["current"]
                        self.last_frame[category]["current"] = 0
                        exercises_changed.append(category) if category not in exercises_changed else None
                        self.repetitions[category]['state'] = 'start'
                        self.executions[category]['max_angle'] = 0
                        self.update_feedback_msg(category)
                        self.update_times(category)
            
        return exercises_changed

    
    def update_times(self, category):
        """
        Funzione che aggiorna i tempi di esecuzione per una categoria specifica. Registro il tempo di esecuzione della ripetizione e resetto il tempo di inizio.
        Il conteggio parte dopo la prima ripetizione per evitare di calcolare il tempo di esecuzione della prima ripetizione.

        Args:
            category (String): categoria dell'esercizio
        """

        if self.repetitions[category]['count'] == 1:
            self.repetitions[category]['start_time'] = util.get_current_time()
        elif self.repetitions[category]['count'] > 1:
            self.repetitions[category]['times'].append(util.get_current_time() - self.repetitions[category]['start_time'])
            self.repetitions[category]['start_time'] = util.get_current_time()


    def update_feedbacks(self, frame):
        """
        Funzione che aggiorna gli angoli minimi e massimi durante l'esecuzione dell'esercizio.

        Args:
            frame (numpy.ndarray): frame da processare
        """

        for category in self.repetitions.keys():  # per ogni categoria di esercizio
            angles_points = vp.category_angles[category]

            curr_angle = util.calculate_angle(vp.extract_points(frame, angles_points[0]), vp.extract_points(frame, angles_points[1]), vp.extract_points(frame, angles_points[2]))

            if self.repetitions[category]['state'] == 'start':  # se lo stato dell'esercizio è start
                if not self.executions[category]['reverse'] and curr_angle < self.executions[category]["min_angle"]:  # se l'angolo attuale è minore del minimo registrato
                    self.executions[category]['min_angle'] = curr_angle
                elif self.executions[category]['reverse'] and curr_angle > self.executions[category]["max_angle"]:
                    self.executions[category]['max_angle'] = curr_angle
            elif self.repetitions[category]['state'] == 'end':
                if not self.executions[category]['reverse'] and curr_angle > self.executions[category]["max_angle"]:
                    self.executions[category]['max_angle'] = curr_angle
                elif self.executions[category]['reverse'] and curr_angle < self.executions[category]["min_angle"]:
                    self.executions[category]['min_angle'] = curr_angle
    

    def update_feedback_msg(self, category, tollerance=5):
        """
        Funzione che aggiorna il feedback dell'esercizio e aggiorna i valori dell'accuratezza.

        Args:
            category (String): categoria dell'esercizio
            tollerance (int): tolleranza per il calcolo dell'accuratezza
        """
        
        tollerance = tollerance / 100
        '''angles_points = vp.category_angles[category]

        for angle_index in range(len(angles_points)):  # per ogni angolo dell'esercizio'''
        
        angle_index = 0
        interval = (self.parameters[category]["angles_max"] - self.parameters[category]["angles_min"]) * tollerance
        self.repetitions[category]['accuracy'] = (self.repetitions[category]['accuracy'][0], self.repetitions[category]['accuracy'][1] + 1)  # incremento il numero totale di frame su cui calcolare l'accuratezza

        if self.repetitions[category]['state'] == 'start':  # se lo stato dell'esercizio è start
            if not self.executions[category]['reverse']:  # se l'esercizio non è inverso
                # se l'angolo massimo registrato è minore del massimo atteso - intervallo: il feedback è end_under
                # se l'angolo massimo registrato è maggiore del massimo atteso + intervallo: il feedback è end_over
                # altrimenti il feedback è good
                if self.executions[category]['max_angle'] < self.parameters[category]["angles_max"] - interval:
                    self.feedbacks[category]['current'] = 'end_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_over' else self.feedbacks[category]['current']
                elif self.executions[category]['max_angle'] > self.parameters[category]["angles_max"] + interval:
                    self.feedbacks[category]['current'] = 'end_over' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
                else:
                    self.feedbacks[category]['current'] = 'good' if self.feedbacks[category]['current'] == 'end_over' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
            else:
                # se l'angolo minimo registrato è maggiore del minimo atteso + intervallo: il feedback è end_under
                # se l'angolo minimo registrato è minore del minimo atteso - intervallo: il feedback è end_over
                # altrimenti il feedback è good
                if self.executions[category]['min_angle'] > self.parameters[category]["angles_min"] + interval:
                    self.feedbacks[category]['current'] = 'end_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_over' else self.feedbacks[category]['current']
                elif self.executions[category]['min_angle'] < self.parameters[category]["angles_min"] - interval:
                    self.feedbacks[category]['current'] = 'end_over' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
                else:
                    self.feedbacks[category]['current'] = 'good' if self.feedbacks[category]['current'] == 'end_over' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
        elif self.repetitions[category]['state'] == 'end':
            if not self.executions[category]['reverse']:
                if self.executions[category]['min_angle'] > self.parameters[category]["angles_min"] + interval:
                    self.feedbacks[category]['current'] = 'start_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'start_over' else self.feedbacks[category]['current']
                elif self.executions[category]['min_angle'] < self.parameters[category]["angles_min"] - interval:
                    self.feedbacks[category]['current'] = 'start_over' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'start_under' else self.feedbacks[category]['current']
                else:
                    self.feedbacks[category]['current'] = 'good' if self.feedbacks[category]['current'] == 'start_over' or self.feedbacks[category]['current'] == 'start_under' else self.feedbacks[category]['current']
            else:
                if self.executions[category]['max_angle'] < self.parameters[category]["angles_max"] - interval:
                    self.feedbacks[category]['current'] = 'start_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'start_over' else self.feedbacks[category]['current']
                elif self.executions[category]['max_angle'] > self.parameters[category]["angles_max"] + interval:
                    self.feedbacks[category]['current'] = 'start_over' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'start_under' else self.feedbacks[category]['current']
                else:
                    self.feedbacks[category]['current'] = 'good' if self.feedbacks[category]['current'] == 'start_over' or self.feedbacks[category]['current'] == 'start_under' else self.feedbacks[category]['current']
                    
        # se il feedback è positivo incremento il numero di frame corretti
        if self.feedbacks[category][self.feedbacks[category]['current']][1]:
            self.repetitions[category]['accuracy'] = (self.repetitions[category]['accuracy'][0] + 1, self.repetitions[category]['accuracy'][1])


    def keypoints_distance(self, kp1, kp2):
        """
        Calcolo la distanza tra due insiemi di keypoints

        Args:
            kp1 (list): primo insieme di keypoints (lista semplice di valori)
            kp2 (list): secondo insieme di keypoints (lista semplice di valori)

        Returns:
            float: distanza tra i due insiemi di keypoints
        """

        sum = 0
        for i in range(len(kp1)):
            sum += (kp1[i] - kp2[i]) ** 2
        return math.sqrt(sum)


    def reset_category_repetitions(self, category):
        """
        Resetto il conteggio delle ripetizioni per una categoria specifica.

        Args:
            category (String): categoria dell'esercizio
        """

        self.repetitions[category]['count'] = 0
        self.repetitions[category]['state'] = 'start'
        self.repetitions[category]['start_time'] = 0
        self.repetitions[category]['times'] = []
        self.repetitions[category]['accuracy'] = (0, 0)


    def get_category_repetitions(self, category):
        """
        Restituisco il numero di ripetizioni per una categoria specifica.

        Args:
            category (String): categoria dell'esercizio

        Returns:
            int: numero di ripetizioni
        """

        return self.repetitions[category]['count']
    

    def add_category_repetition(self, category):
        """
        Incremento il numero di ripetizioni per una categoria specifica.

        Args:
            category (String): categoria dell'esercizio
        """

        self.repetitions[category]['count'] += 1
    

    def get_category_avg_time(self, category):
        """
        Restituisco il tempo medio di esecuzione per una categoria specifica.

        Args:
            category (String): categoria dell'esercizio

        Returns:
            float: tempo medio di esecuzione
        """

        return np.mean(self.repetitions[category]['times']) if len(self.repetitions[category]['times']) > 0 else 0


    def get_category_accuracy(self, category):
        """
        Restituisco l'accuratezza dell'esecuzione per una categoria specifica.

        Args:
            category (String): categoria dell'esercizio

        Returns:
            float: accuratezza dell'esecuzione
        """

        return self.repetitions[category]['accuracy'][0] / self.repetitions[category]['accuracy'][1] if self.repetitions[category]['accuracy'][1] > 0 else 0
    

    def get_category_phrase(self, category):
        """
        Restituisco il feedback associato all'esercizio.

        Args:
            category (String): categoria dell'esercizio

        Returns:
            String: feedback associato all'esercizio
        """

        return self.feedbacks[category][self.feedbacks[category]['current']][0]
    

    def get_last_frame(self, category):
        """
        Restituisco l'ultimo frame processato per una categoria specifica.

        Args:
            category (String): categoria dell'esercizio

        Returns:
            int: ultimo frame processato
        """

        return self.last_frame[category]["last"]
    
    def get_max_last_frame(self, category):
        """
        Restituisco l'ultimo frame processato per una categoria specifica.

        Args:
            category (String): categoria dell'esercizio

        Returns:
            int: ultimo frame processato
        """

        return self.last_frame[category]["max"]
    

    def reset_all_last_frame(self):
        """
        Resetto l'ultimo frame processato per tutte le categorie di esercizio.
        """

        for category in self.last_frame.keys():
            self.last_frame[category]["last"] = self.last_frame[category]["current"]
            self.last_frame[category]["current"] = 0