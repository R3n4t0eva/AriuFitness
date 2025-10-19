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
        # max e min angle sono liste di valori, uno per ogni angolo dell'esercizio
        # reverse indica se l'esercizio è inverso (True se inizia con l'angolo massimo e termina con l'angolo minimo, False altrimenti)
        self.executions = {
            'arms_extension': {
                'max_angle': [],
                'min_angle': [],
                'reverse': False
            },
            'arms_up': {
                'max_angle': [],
                'min_angle': [],
                'reverse': True
            },
            'chair_raises': {
                'max_angle': [],
                'min_angle': [],
                'reverse': False
            },
            'arms_lateral': {
                'max_angle': [],
                'min_angle': [],
                'reverse': False
            },
            'leg_lateral': {
                'max_angle': [],
                'min_angle': [],
                'reverse': False
            }
        }

        # inizializzo i valori massimi e minimi degli angoli per ogni categoria di esercizio
        for category in self.executions.keys():
            self.executions[category]['max_angle'] = [0 for i in range(len(vp.category_angles[category]))]
            self.executions[category]['min_angle'] = [180 for i in range(len(vp.category_angles[category]))]

        # dizionario che contiene i feedback per ogni categoria di esercizio. Ogni feedback è composto da un messaggio e un booleano che indica se il feedback è positivo o negativo
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
            }
        }

        self.last_frame = {
            'arms_extension': {
                "last": 0,
                "current": 0
            },
            'arms_up': {
                "last": 0,
                "current": 0
            },
            'chair_raises': {
                "last": 0,
                "current": 0
            },
            'arms_lateral': {
                "last": 0,
                "current": 0
            },
            'leg_lateral': {
                "last": 0,
                "current": 0
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
            }
        }


    def extract_parameters(self):
        """
        Funzione che estrae i parametri necessari per il calcolo delle ripetizioni e la generazione di feedback.
        """
        
        self.parameters = np.load(os.path.join(util.getParametersPath(), "parameters.npy"), allow_pickle=True).item()


    def update(self, frame):
        """
        Funzione che aggiorna il conteggio delle ripetizioni e la generazione di feedback.

        Args:
            frame (numpy.ndarray): frame da processare
        """

        for category in self.last_frame.keys():
            self.last_frame[category]["current"] += 1

        exercises_changed = self.update_repetitions(frame)
        self.update_feedbacks(frame)
        return exercises_changed

    
    '''def update_repetitions(self, frame):
        """
        Funzione che aggiorna il numero di ripetizioni per ogni categoria di esercizio.
        In essa vengono richiamate anche le funzioni per il calcolo dei tempi di esecuzione e l'accuratezza.

        Args:
            frame (Frame): frame da processare
        """

        exercises_changed = []
        curr_keypoints = frame.process_keypoints().tolist()

        for category in self.repetitions.keys():  # per ogni categoria di esercizio
            # calcolo la distanza tra i keypoints attuali e i keypoints massimi e minimi per la categoria di esercizio
            distance_max = min([self.keypoints_distance(curr_keypoints, keypoints) for keypoints in self.parameters[category]["keypoints_max"]])
            distance_min = min([self.keypoints_distance(curr_keypoints, keypoints) for keypoints in self.parameters[category]["keypoints_min"]])
            if category == "arms_extension":
                print(distance_max, distance_min)

            if not self.executions[category]['reverse']:  # se l'esercizio non è inverso
                if self.repetitions[category]['state'] == 'start':  # se lo stato dell'esercizio è start
                    if distance_max < distance_min:  # se il frame è più vicino all'angolo massimo (più vicino alla metà dell'esercizio)
                        self.repetitions[category]['state'] = 'end'
                        self.executions[category]['max_angle'] = [0 for i in range(len(vp.category_angles[category]))]
                        self.update_feedback_msg(category)
                elif self.repetitions[category]['state'] == 'end':
                    if distance_min < distance_max:
                        self.repetitions[category]['count'] += 1
                        self.last_frame[category]["last"] = self.last_frame[category]["current"]
                        self.last_frame[category]["current"] = 0
                        exercises_changed.append(category) if category not in exercises_changed else None
                        self.repetitions[category]['state'] = 'start'
                        self.executions[category]['min_angle'] = [180 for i in range(len(vp.category_angles[category]))]
                        self.update_feedback_msg(category)
                        self.update_times(category)
            else:
                if self.repetitions[category]['state'] == 'start':
                    if distance_max > distance_min:
                        self.repetitions[category]['state'] = 'end'
                        self.executions[category]['min_angle'] = [180 for i in range(len(vp.category_angles[category]))]
                        self.update_feedback_msg(category)
                elif self.repetitions[category]['state'] == 'end':
                    if distance_min > distance_max:
                        self.repetitions[category]['count'] += 1
                        self.last_frame[category]["last"] = self.last_frame[category]["current"]
                        self.last_frame[category]["current"] = 0
                        exercises_changed.append(category) if category not in exercises_changed else None
                        self.repetitions[category]['state'] = 'start'
                        self.executions[category]['max_angle'] = [0 for i in range(len(vp.category_angles[category]))]
                        self.update_feedback_msg(category)
                        self.update_times(category)
            
        return exercises_changed'''
    

    def update_repetitions(self, frame):
        """
        Funzione che aggiorna il numero di ripetizioni per ogni categoria di esercizio.
        In essa vengono richiamate anche le funzioni per il calcolo dei tempi di esecuzione e l'accuratezza.

        Args:
            frame (Frame): frame da processare
        """

        exercises_changed = []
        #curr_keypoints = frame.process_keypoints().tolist()
        curr_keypoints = frame.get_keypoints()

        tollerance = 30/100

        for category in self.repetitions.keys():  # per ogni categoria di esercizio
            # calcolo la distanza tra i keypoints attuali e i keypoints massimi e minimi per la categoria di esercizio
            #distance_max = min([self.keypoints_distance(curr_keypoints, keypoints) for keypoints in self.parameters[category]["keypoints_max"]])
            #distance_min = min([self.keypoints_distance(curr_keypoints, keypoints) for keypoints in self.parameters[category]["keypoints_min"]])
            curr_angle = util.calculate_angle(vp.extract_points(frame, vp.category_angles[category][0]), vp.extract_points(frame, vp.category_angles[category][1]), vp.extract_points(frame, vp.category_angles[category][2]))
            cat_min_angle = self.parameters[category]["angles_min"]
            cat_max_angle = self.parameters[category]["angles_max"]
            interval = (cat_max_angle - cat_min_angle) * tollerance

            if not self.executions[category]['reverse']:  # se l'esercizio non è inverso
                if self.repetitions[category]['state'] == 'start':  # se lo stato dell'esercizio è start
                    #if distance_max < distance_min:  # se il frame è più vicino all'angolo massimo (più vicino alla metà dell'esercizio)
                    if curr_angle > cat_max_angle - interval:
                        self.repetitions[category]['state'] = 'end'
                        self.executions[category]['max_angle'] = [0 for i in range(len(vp.category_angles[category]))]
                        self.update_feedback_msg(category)
                elif self.repetitions[category]['state'] == 'end':
                    #if distance_min < distance_max:
                    if curr_angle < cat_min_angle + interval:
                        self.repetitions[category]['count'] += 1
                        self.last_frame[category]["last"] = self.last_frame[category]["current"]
                        self.last_frame[category]["current"] = 0
                        exercises_changed.append(category) if category not in exercises_changed else None
                        self.repetitions[category]['state'] = 'start'
                        self.executions[category]['min_angle'] = [180 for i in range(len(vp.category_angles[category]))]
                        self.update_feedback_msg(category)
                        self.update_times(category)
            else:
                if self.repetitions[category]['state'] == 'start':
                    #if distance_max > distance_min:
                    if curr_angle < cat_min_angle + interval:
                        self.repetitions[category]['state'] = 'end'
                        self.executions[category]['min_angle'] = [180 for i in range(len(vp.category_angles[category]))]
                        self.update_feedback_msg(category)
                elif self.repetitions[category]['state'] == 'end':
                    #if distance_min > distance_max:
                    if curr_angle > cat_max_angle - interval:
                        self.repetitions[category]['count'] += 1
                        self.last_frame[category]["last"] = self.last_frame[category]["current"]
                        self.last_frame[category]["current"] = 0
                        exercises_changed.append(category) if category not in exercises_changed else None
                        self.repetitions[category]['state'] = 'start'
                        self.executions[category]['max_angle'] = [0 for i in range(len(vp.category_angles[category]))]
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

            #for angle_index in range(len(angles_points)):  # per ogni angolo dell'esercizio
            curr_angle = util.calculate_angle(vp.extract_points(frame, angles_points[0]), vp.extract_points(frame, angles_points[1]), vp.extract_points(frame, angles_points[2]))

            if self.repetitions[category]['state'] == 'start':  # se lo stato dell'esercizio è start
                if not self.executions[category]['reverse'] and curr_angle < self.executions[category]["min_angle"][0]:  # se l'angolo attuale è minore del minimo registrato
                    self.executions[category]['min_angle'][0] = curr_angle
                elif self.executions[category]['reverse'] and curr_angle > self.executions[category]["max_angle"][0]:
                    self.executions[category]['max_angle'][0] = curr_angle
            elif self.repetitions[category]['state'] == 'end':
                if not self.executions[category]['reverse'] and curr_angle > self.executions[category]["max_angle"][0]:
                    self.executions[category]['max_angle'][0] = curr_angle
                elif self.executions[category]['reverse'] and curr_angle < self.executions[category]["min_angle"][0]:
                    self.executions[category]['min_angle'][0] = curr_angle


    '''def update_feedback_msg(self, category, tollerance=5):
        """
        Funzione che aggiorna il feedback dell'esercizio e aggiorna i valori dell'accuratezza.

        Args:
            category (String): categoria dell'esercizio
            tollerance (int): tolleranza per il calcolo dell'accuratezza
        """
        
        tollerance = tollerance / 100
        angles_points = vp.category_angles[category]

        for angle_index in range(len(angles_points)):  # per ogni angolo dell'esercizio
            interval = (self.parameters[category]["angles_max"][angle_index] - self.parameters[category]["angles_min"][angle_index]) * tollerance  # calcolo l'intervallo di tolleranza
            self.repetitions[category]['accuracy'] = (self.repetitions[category]['accuracy'][0], self.repetitions[category]['accuracy'][1] + 1)  # incremento il numero totale di frame su cui calcolare l'accuratezza

            if self.repetitions[category]['state'] == 'start':  # se lo stato dell'esercizio è start
                if not self.executions[category]['reverse']:  # se l'esercizio non è inverso
                    # se l'angolo massimo registrato è minore del massimo atteso - intervallo: il feedback è end_under
                    # se l'angolo massimo registrato è maggiore del massimo atteso + intervallo: il feedback è end_over
                    # altrimenti il feedback è good
                    if self.executions[category]['max_angle'][angle_index] < self.parameters[category]["angles_max"][angle_index] - interval:
                        self.feedbacks[category]['current'] = 'end_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_over' else self.feedbacks[category]['current']
                    elif self.executions[category]['max_angle'][angle_index] > self.parameters[category]["angles_max"][angle_index] + interval:
                        self.feedbacks[category]['current'] = 'end_over' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
                    else:
                        self.feedbacks[category]['current'] = 'good' if self.feedbacks[category]['current'] == 'end_over' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
                else:
                    # se l'angolo minimo registrato è maggiore del minimo atteso + intervallo: il feedback è end_under
                    # se l'angolo minimo registrato è minore del minimo atteso - intervallo: il feedback è end_over
                    # altrimenti il feedback è good
                    if self.executions[category]['min_angle'][angle_index] > self.parameters[category]["angles_min"][angle_index] + interval:
                        self.feedbacks[category]['current'] = 'end_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_over' else self.feedbacks[category]['current']
                    elif self.executions[category]['min_angle'][angle_index] < self.parameters[category]["angles_min"][angle_index] - interval:
                        self.feedbacks[category]['current'] = 'end_over' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
                    else:
                        self.feedbacks[category]['current'] = 'good' if self.feedbacks[category]['current'] == 'end_over' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
            elif self.repetitions[category]['state'] == 'end':
                if not self.executions[category]['reverse']:
                    if self.executions[category]['min_angle'][angle_index] > self.parameters[category]["angles_min"][angle_index] + interval:
                        self.feedbacks[category]['current'] = 'start_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'start_over' else self.feedbacks[category]['current']
                    elif self.executions[category]['min_angle'][angle_index] < self.parameters[category]["angles_min"][angle_index] - interval:
                        self.feedbacks[category]['current'] = 'start_over' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'start_under' else self.feedbacks[category]['current']
                    else:
                        self.feedbacks[category]['current'] = 'good' if self.feedbacks[category]['current'] == 'start_over' or self.feedbacks[category]['current'] == 'start_under' else self.feedbacks[category]['current']
                else:
                    if self.executions[category]['max_angle'][angle_index] < self.parameters[category]["angles_max"][angle_index] - interval:
                        self.feedbacks[category]['current'] = 'start_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'start_over' else self.feedbacks[category]['current']
                    elif self.executions[category]['max_angle'][angle_index] > self.parameters[category]["angles_max"][angle_index] + interval:
                        self.feedbacks[category]['current'] = 'start_over' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'start_under' else self.feedbacks[category]['current']
                    else:
                        self.feedbacks[category]['current'] = 'good' if self.feedbacks[category]['current'] == 'start_over' or self.feedbacks[category]['current'] == 'start_under' else self.feedbacks[category]['current']
                        
            # se il feedback è positivo incremento il numero di frame corretti
            if self.feedbacks[category][self.feedbacks[category]['current']][1]:
                self.repetitions[category]['accuracy'] = (self.repetitions[category]['accuracy'][0] + 1, self.repetitions[category]['accuracy'][1])'''
    

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
        #interval = (self.parameters[category]["angles_max"][angle_index] - self.parameters[category]["angles_min"][angle_index]) * tollerance  # calcolo l'intervallo di tolleranza
        interval = (self.parameters[category]["angles_max"] - self.parameters[category]["angles_min"]) * tollerance
        self.repetitions[category]['accuracy'] = (self.repetitions[category]['accuracy'][0], self.repetitions[category]['accuracy'][1] + 1)  # incremento il numero totale di frame su cui calcolare l'accuratezza

        if self.repetitions[category]['state'] == 'start':  # se lo stato dell'esercizio è start
            if not self.executions[category]['reverse']:  # se l'esercizio non è inverso
                # se l'angolo massimo registrato è minore del massimo atteso - intervallo: il feedback è end_under
                # se l'angolo massimo registrato è maggiore del massimo atteso + intervallo: il feedback è end_over
                # altrimenti il feedback è good
                if self.executions[category]['max_angle'][0] < self.parameters[category]["angles_max"] - interval:
                    self.feedbacks[category]['current'] = 'end_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_over' else self.feedbacks[category]['current']
                elif self.executions[category]['max_angle'][0] > self.parameters[category]["angles_max"] + interval:
                    self.feedbacks[category]['current'] = 'end_over' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
                else:
                    self.feedbacks[category]['current'] = 'good' if self.feedbacks[category]['current'] == 'end_over' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
            else:
                # se l'angolo minimo registrato è maggiore del minimo atteso + intervallo: il feedback è end_under
                # se l'angolo minimo registrato è minore del minimo atteso - intervallo: il feedback è end_over
                # altrimenti il feedback è good
                if self.executions[category]['min_angle'][0] > self.parameters[category]["angles_min"] + interval:
                    self.feedbacks[category]['current'] = 'end_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_over' else self.feedbacks[category]['current']
                elif self.executions[category]['min_angle'][0] < self.parameters[category]["angles_min"] - interval:
                    self.feedbacks[category]['current'] = 'end_over' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
                else:
                    self.feedbacks[category]['current'] = 'good' if self.feedbacks[category]['current'] == 'end_over' or self.feedbacks[category]['current'] == 'end_under' else self.feedbacks[category]['current']
        elif self.repetitions[category]['state'] == 'end':
            if not self.executions[category]['reverse']:
                if self.executions[category]['min_angle'][0] > self.parameters[category]["angles_min"] + interval:
                    self.feedbacks[category]['current'] = 'start_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'start_over' else self.feedbacks[category]['current']
                elif self.executions[category]['min_angle'][0] < self.parameters[category]["angles_min"] - interval:
                    self.feedbacks[category]['current'] = 'start_over' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'start_under' else self.feedbacks[category]['current']
                else:
                    self.feedbacks[category]['current'] = 'good' if self.feedbacks[category]['current'] == 'start_over' or self.feedbacks[category]['current'] == 'start_under' else self.feedbacks[category]['current']
            else:
                if self.executions[category]['max_angle'][0] < self.parameters[category]["angles_max"] - interval:
                    self.feedbacks[category]['current'] = 'start_under' if self.feedbacks[category]['current'] == 'good' or self.feedbacks[category]['current'] == 'start_over' else self.feedbacks[category]['current']
                elif self.executions[category]['max_angle'][0] > self.parameters[category]["angles_max"] + interval:
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