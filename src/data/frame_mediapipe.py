import cv2
import numpy as np
import util

class Frame:
    """
    Classe che rappresenta un frame di un video.
    """

    # Quantità di dati facenti parte del dataset per ogni feature
    num_keypoints_data = 36
    num_angles_data = 8
    num_opticalflow_data = 24
    num_mediapipe_keypoints = 33

    angles_dict = {  # angoli articolari
        'left_elbow': [5, 3, 1],
        'right_elbow': [2, 4, 6],
        'left_shoulder': [3, 1, 7],
        'right_shoulder': [8, 2, 4],
        'left_hip': [1, 7, 9],
        'right_hip': [2, 8, 10],
        'left_knee': [7, 9, 11],
        'right_knee': [8, 10, 12]
    }

    keypoints_list = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]  # keypoints utili alla predizione


    def __init__(self, frame):
        """
        Costruttore della classe che inizializza gli attributi

        Args:
        - frame (numpy.ndarray): il frame del video
        """
        self.keypoints = None  # keypoints estratti dal frame
        self.angles = None  # angoli estratti dal frame
        self.frame = frame  # frame
        self.mediapipe_landmarks = []  # landmarks estratti dal frame

        self.extract_keypoints()


    def extract_keypoints(self):
        """
        Funzione che estrae i keypoints dal frame con Mediapipe e mantiene solo quelli necessari.
        """

        with util.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            # Recolor dell'immagine
            image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            # Estrazione dei keypoints
            results = pose.process(image)
            # salvataggio dei landmarks necessari
            if results.pose_landmarks:
                for i in range(len(results.pose_landmarks.landmark)):
                    if i in Frame.keypoints_list:
                        self.mediapipe_landmarks.append(results.pose_landmarks.landmark[i])
                    else:
                        self.mediapipe_landmarks.append(None)

            # Creo un array dove ogni elemento rappresenta un keypoint di mediapipe e ogni keypoints è un dizionario con coordinate e visibilità
            points = [None] * Frame.num_mediapipe_keypoints
            for i in range(Frame.num_mediapipe_keypoints):
                try:
                    if i < len(results.pose_landmarks.landmark):  # se il punto è rilevato
                        landmark = results.pose_landmarks.landmark[i]
                        points[i] = {"x": landmark.x, "y": landmark.y, "z": landmark.z, "visibility": landmark.visibility}
                    else:  # valori di default se il punto non è rilevato
                        points[i] = {"x": 0.0, "y": 0.0, "z": 0.0, "visibility": 0.0}
                except:  # valori di default in caso di errore nella rilevazione del punto
                    points[i] = {"x": 0.0, "y": 0.0, "z": 0.0, "visibility": 0.0}

            # Prendo in considerazione solo i keypoints necessari salvandoli nell'attributo keypoints
            self.keypoints = np.array([points[i] for i in range(Frame.num_mediapipe_keypoints) if i in Frame.keypoints_list])


    def extract_angles(self):
        """
        Funzione che estrae gli angoli in base ai keypoints precedentemente estratti
        """

        angles = []
        for angle in Frame.angles_dict:
            angle_keypoints = Frame.angles_dict[angle]
            angle = util.calculate_angle(self.keypoints[angle_keypoints[0]], self.keypoints[angle_keypoints[1]], self.keypoints[angle_keypoints[2]])
            angles.append(angle)
        self.angles = angles


    def extract_opticalflow(self, prev_frame, area_size=50):
        """
        Funzione che estrae il flusso ottico tra due frame.
        Viene estratto il flusso ottico per ogni area di dimensione area_size x area_size intorno ai keypoints.

        Args:
        - prev_frame (numpy.ndarray): Il frame precedente
        - area_size (int): La dimensione dell'area intorno al keypoints (opzionale)

        Returns:
        - numpy.ndarray: Il flusso ottico
        """

        # Recolor dei frame
        prev_gray = cv2.cvtColor(prev_frame.get_frame(), cv2.COLOR_BGR2GRAY)
        current_gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

        flow_vectors = []

        for i in range(1, len(self.keypoints)):
            kp = self.keypoints[i]
            # ottengo le coordinate del keypoints e calcolo le coordinate dell'area intorno al keypoints
            x = max(min(int(kp["x"] * prev_gray.shape[1]), prev_gray.shape[1] - 1), 1)
            y = max(min(int(kp["y"] * prev_gray.shape[0]), prev_gray.shape[0] - 1), 1)
            x1, y1 = max(1, x - area_size // 2), max(1, y - area_size // 2)
            x2, y2 = min(current_gray.shape[1] - 1, x + area_size // 2), min(current_gray.shape[0] - 1, y + area_size // 2)
            # calcolo il flusso ottico nell'area intorno al keypoints
            flow = cv2.calcOpticalFlowFarneback(prev_gray[y1:y2, x1:x2], current_gray[y1:y2, x1:x2], None, 0.5, 3, 15, 3, 5, 1.2, 0)
            flow_vector = np.mean(flow, axis=(0, 1))
            flow_vectors.append(flow_vector)

        # Riduco la dimensione dell'array da (12, 2) a (24, 1)
        flow_vectors = np.array(flow_vectors)
        flow_vectors = flow_vectors.flatten()
        return np.array(flow_vectors)


    def interpolate_keypoints(self, prev_frame, next_frame, treshold=0.3):
        """
        Funzione che interpola i keypoints con confidence bassa.

        Args:
        - prev_frame (numpy.ndarray): Il frame precedente
        - next_frame (numpy.ndarray): Il frame successivo
        - treshold (float): La soglia di confidence sotto la quale i keypoints vengono interpolati
        """

        # Interpolo i keypoints con confidence al di sotto della soglia treshold
        for i in range(0, len(self.keypoints)):
            curr_kp = self.keypoints[i]
            if curr_kp["visibility"] < treshold:
                if prev_frame is not None and next_frame is not None:  # Se i frame precedente e successivo sono disponibili eseguo l'interpolazione
                    prev_kp = prev_frame.get_keypoint(i)
                    next_kp = next_frame.get_keypoint(i)
                    if prev_kp["visibility"] >= treshold and next_kp["visibility"] >= treshold:  # Eseguo l'interpolazione se i keypoints sono visibili nei frame
                        self.keypoints[i]["x"] = (prev_kp["x"] + next_kp["x"]) / 2
                        self.keypoints[i]["y"] = (prev_kp["y"] + next_kp["y"]) / 2
                        self.keypoints[i]["z"] = (prev_kp["z"] + next_kp["z"]) / 2
                        self.keypoints[i]["visibility"] = curr_kp["visibility"]
                    elif prev_kp["visibility"] >= treshold:
                        self.keypoints[i]["x"] = prev_kp["x"]
                        self.keypoints[i]["y"] = prev_kp["y"]
                        self.keypoints[i]["z"] = prev_kp["z"]
                        self.keypoints[i]["visibility"] = prev_kp["visibility"]
                    elif next_kp["visibility"] >= treshold:
                        self.keypoints[i]["x"] = next_kp["x"]
                        self.keypoints[i]["y"] = next_kp["y"]
                        self.keypoints[i]["z"] = next_kp["z"]
                        self.keypoints[i]["visibility"] = next_kp["visibility"]
                else:  # Se non sono disponibili frame precedente e successivo imposto i keypoints a 0
                    self.keypoints[i]["x"] = 0.0
                    self.keypoints[i]["y"] = 0.0
                    self.keypoints[i]["z"] = 0.0
                    self.keypoints[i]["visibility"] = curr_kp["visibility"]
                self.keypoints[i]["visibility"] = 0.0
            else:
                self.keypoints[i]["visibility"] = 1.0

    def process_keypoints(self):
        """
        Funzione che processa i keypoints in modo da utilizzarli per l'addestramento

        Returns:
        - processed_keypoints (numpy.ndarray): i keypoints processati
        """

        #kp_copy = self.keypoints.copy()
        kp_copy = [None for _ in range(len(self.keypoints))]
        for i in range(len(self.keypoints)):
            kp_copy[i] = {
                "x": self.keypoints[i]["x"],
                "y": self.keypoints[i]["y"],
                "z": self.keypoints[i]["z"],
                "visibility": self.keypoints[i]["visibility"]
            }

        # Trasforma le coordinate x e y di ogni punto in coordinate rispetto al keypoint 0
        for i in range(1, len(kp_copy)):
            kp_copy[i]["x"] -= kp_copy[0]["x"]
            kp_copy[i]["y"] -= kp_copy[0]["y"]
            kp_copy[i]["z"] -= kp_copy[0]["z"]

        # Trasformo ogni elemento da dizionario a array
        kp = [None for _ in range(len(kp_copy))]
        for i in range(len(kp_copy)):
            kp[i] = [None for _ in range(4)]
            kp[i][0] = kp_copy[i]["x"]
            kp[i][1] = kp_copy[i]["y"]
            kp[i][2] = kp_copy[i]["z"]
            kp[i][3] = kp_copy[i]["visibility"]
        
        # Elimino il punto 0 rendendo l'array di dimensione (12, 4)
        processed_keypoints = np.delete(kp, 0, axis=0)

        # Normalizzo le coordinate x e y in base alla lunghezza del corpo (distanza tra i fianchi)
        '''norm = math.sqrt((kp_copy[7]["x"] - kp_copy[8]["x"])**2 + (kp_copy[7]["y"] - kp_copy[8]["y"])**2)
        for i in range(len(kp) - 1):
            processed_keypoints[i][0] /= norm if norm != 0 else 1
            processed_keypoints[i][1] /= norm if norm != 0 else 1
            processed_keypoints[i][2] /= norm if norm != 0 else 1
        processed_keypoints = np.array(processed_keypoints)'''

        # Elimino da ogni punto la visibility rendendo l'array di dimensione (12, 3)
        processed_keypoints = np.delete(processed_keypoints, 3, axis=1)
        # Elimino la coordinata z
        #processed_keypoints = np.delete(processed_keypoints, 2, axis=1)
        # Rendo l'array keypoints da dimensione (12, 3) a (36, 1)
        processed_keypoints = processed_keypoints.flatten()

        return processed_keypoints

    def process_angles(self):
        """
        Funzione che processa gli angoli in modo da utilizzarli per l'addestramento.

        Returns:
        - processed_angles (numpy.ndarray): gli angoli processati
        """

        processed_angles = np.array(self.angles)
        return processed_angles


    # FUNZIONI GET E SET

    def get_keypoints(self):
        """
        Funzione che restituisce i keypoints.

        Returns:
        - array: keypoints del frame
        """

        return self.keypoints

    def get_keypoint(self, num):
        """
        Funzione che restituisce il keypoint in posizione num

        Returns:
        - keypoint (dict): keypoint in posizione num
        """

        return self.keypoints[num]

    def get_angles(self):
        """
        Funzione che restituisce gli angoli.

        Returns:
        - array: angoli del frame
        """

        return self.angles

    def get_frame(self):
        """
        Funzione che restituisce il frame.

        Returns:
        - frame: il frame
        """

        return self.frame
    
    def get_landmarks(self):
        """
        Funzione che restituisce i landmarks.

        Returns:
        - landmarks: i landmarks
        """

        return self.mediapipe_landmarks