import math
import cv2
import numpy as np
import util
import tensorflow as tf

class Frame:
    num_keypoints_data = 24
    num_opticalflow_data = 24
    num_movenet_keypoints = 17
    angleDict = {  # angoli utili alla predizione
        'angl_left_elbow': [5, 3, 1],
        'angl_right_elbow': [2, 4, 6],
        'angl_left_shoulder': [3, 1, 7],
        'angl_right_shoulder': [4, 2, 8],
        'angl_left_hip': [1, 7, 9],
        'angl_right_hip': [2, 8, 10],
        'angl_left_knee': [7, 9, 11],
        'angl_right_knee': [8, 10, 12],
    }
    # keypoints utili alla predizione
    keypoints_list = [0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

    def __init__(self, frame):
        """
        Costruttore della classe che inizializza gli attributi
        """
        self.keypoints = None  # keypoints estratti dal frame
        self.angles = None  # angoli estratti dal frame
        self.frame = frame  # frame

        self.extract_keypoints()

    def extract_keypoints(self):
        """
        Funzione che estrae i keypoints dal frame con Mediapipe e mantiene solo quelli necessari.
        """

        with util.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            # Recolor dell'immagine
            image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            image = tf.image.resize_with_pad(tf.expand_dims(image, axis=0), 192, 192)
            image = image.numpy().astype(np.int32)
            outputs = util.movenet.signatures["serving_default"](tf.constant(image))
            keypoints = outputs['output_0'].numpy()[0][0]

            # Creao un array dove ogni elemento rappresenta un keypoint di mediapipe
            # Ogni keypoint è un array di 3 elementi: coordinate x, y del punto e visibilità
            points = [None] * Frame.num_movenet_keypoints
            for i in range(Frame.num_movenet_keypoints):
                try:
                    if i < len(keypoints):
                        landmark = keypoints[i]
                        #points[i] = [landmark.x, landmark.y, landmark.z, landmark.visibility]
                        points[i] = {
                            "x": landmark[0],
                            "y": landmark[1],
                            "visibility": landmark[2],
                        }
                    else:
                        #points[i] = [0.0, 0.0, 0.0, 0.0]  # valori di default se il punto non è rilevato
                        points[i] = {
                            "x": 0.0,
                            "y": 0.0,
                            "visibility": 0.0,
                        }
                except:
                    #points[i] = [0.0, 0.0, 0.0, 0.0]
                    points[i] = {
                        "x": 0.0,
                        "y": 0.0,
                        "visibility": 0.0,
                    }

            # Prendo in considerazione solo i keypoints necessari salvandoli nell'attributo keypoints
            self.keypoints = np.array([points[i] for i in range(Frame.num_movenet_keypoints) if i in Frame.keypoints_list])

    def extract_angles(self):
        """
        Funzione che estrae gli angoli in base ai keypoints precedentemente estratti
        """

        angles = []
        for angle in Frame.angleDict:
            angle_keypoints = Frame.angleDict[angle]
            angle = util.calculate_angle(self.keypoints[angle_keypoints[0]], self.keypoints[angle_keypoints[1]], self.keypoints[angle_keypoints[2]])
            angles.append(angle)

        self.angles = angles

    def extract_opticalflow(self, prev_frame, area_size=5):
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
            x, y = int(kp["x"]), int(kp["y"])
            x1, y1 = max(0, x - area_size // 2), max(0, y - area_size // 2)
            x2, y2 = min(current_gray.shape[1], x + area_size // 2), min(current_gray.shape[0], y + area_size // 2)
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

        for i in range(0, len(self.keypoints)):
            curr_kp = self.keypoints[i]
            if curr_kp["visibility"] < treshold:
                if prev_frame is not None and next_frame is not None:
                    prev_kp = prev_frame.get_keypoint(i)
                    next_kp = next_frame.get_keypoint(i)
                    if prev_kp["visibility"] >= treshold and next_kp["visibility"] >= treshold:
                        self.keypoints[i]["x"] = (prev_kp["x"] + next_kp["x"]) / 2
                        self.keypoints[i]["y"] = (prev_kp["y"] + next_kp["y"]) / 2
                        self.keypoints[i]["visibility"] = curr_kp["visibility"]
                    elif prev_kp["visibility"] >= treshold:
                        self.keypoints[i]["x"] = prev_kp["x"]
                        self.keypoints[i]["y"] = prev_kp["y"]
                        self.keypoints[i]["visibility"] = prev_kp["visibility"]
                    elif next_kp["visibility"] >= treshold:
                        self.keypoints[i]["x"] = next_kp["x"]
                        self.keypoints[i]["y"] = next_kp["y"]
                        self.keypoints[i]["visibility"] = next_kp["visibility"]
                else:
                    self.keypoints[i]["x"] = 0.0
                    self.keypoints[i]["y"] = 0.0
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

        kp_copy = self.keypoints.copy()

        # Trasforma le coordinate x e y di ogni punto in coordinate rispetto al keypoint 0
        for i in range(1, len(kp_copy)):
            kp_copy[i]["x"] -= kp_copy[0]["x"]
            kp_copy[i]["y"] -= kp_copy[0]["y"]

        # Trasformo ogni elemento da dizionario a array
        kp = [None for _ in range(len(kp_copy))]
        for i in range(len(kp_copy)):
            kp[i] = [None for _ in range(3)]
            kp[i][0] = kp_copy[i]["x"]
            kp[i][1] = kp_copy[i]["y"]
            kp[i][2] = kp_copy[i]["visibility"]
        # Elimino il punto 0 rendendo l'array di dimensione (12, 3)
        processed_keypoints = np.delete(kp, 0, axis=0)
        '''# Normalizzo le coordinate x e y in base alla lunghezza del corpo (altezza del busto con mediapipe)
        processed_keypoints = np.array(processed_keypoints)
        processed_keypoints[:, 0] /= np.linalg.norm(processed_keypoints[1] - processed_keypoints[7])
        processed_keypoints[:, 1] /= np.linalg.norm(processed_keypoints[1] - processed_keypoints[7])'''
        # Normalizzo le coordinate x e y in base alla lunghezza del corpo (distanza tra i fianchi)
        norm = math.sqrt((kp_copy[7]["x"] - kp_copy[8]["x"])**2 + (kp_copy[7]["y"] - kp_copy[8]["y"])**2)
        for i in range(len(kp) - 1):
            processed_keypoints[i][0] /= norm if norm != 0 else 1
            processed_keypoints[i][1] /= norm if norm != 0 else 1
        processed_keypoints = np.array(processed_keypoints)
        # Elimino da ogni punto la visibility rendendo l'array di dimensione (12, 2)
        processed_keypoints = np.delete(processed_keypoints, 2, axis=1)
        # Rendo l'array keypoints da dimensione (12, 2) a (24, 1)
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