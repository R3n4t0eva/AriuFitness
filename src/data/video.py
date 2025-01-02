import cv2
import numpy as np
from data.frame_mediapipe import Frame
from data.window import Window
from data.video_params_old import VideoParams
import os
import util
from dotenv import load_dotenv

load_dotenv()

class Video:
    """
    Classe che rappresenta un video. Un video è composto da una serie di finestre, ognuna delle quali contiene una serie di frame.
    """

    def __init__(self, path, category):
        """
        Costruttore della classe Video

        Args:
        - path (string): percorso del video
        - category (string): categoria del video
        """

        self.windows = None
        self.path = path
        self.category = category
        self.parameters = None
        self.extract_values()


    def extract_values(self):
        """
        Funzione che suddivide il video in finestre ed estrae i keypoints, gli angoli e l'opticalflow di ogni finestra e i parametri del video.
        """

        cap = cv2.VideoCapture(self.path)
        frames = []

        while True:  # Leggo tutti i frame del video e li salvo in un array se hanno un certo livello di differenza con il frame precedente
            ret, frame = cap.read()
            if not ret:
                break

            f = Frame(frame)
            if len(frames) == 0 or not util.same_frame(frames[-1], f, threshold=0.01):
                frames.append(f)

        # Divido tutti i frame in finestre di 15 frame con sovrapposizione di 14 frame
        self.windows = [Window([frames[i:i + util.getWindowSize()]]) for i in range(len(frames) - util.getWindowSize() + 1)]

        opticalflow = []

        for i in range(len(frames)):  # Estraggo keypoints, angoli e opticalflow di ogni frame
            frames[i].interpolate_keypoints(frames[i - 1] if i > 0 else None, frames[i + 1] if i < len(frames) - 1 else None)
            frames[i].extract_angles()
            if i > 0:
                opticalflow.append(frames[i].extract_opticalflow(frames[i - 1]))
            else:
                opticalflow.append(np.zeros((Frame.num_opticalflow_data,)))

        for i in range(len(self.windows)):  # Aggiorno i valori di keypoints, angoli e opticalflow di ogni finestra
            self.windows[i].set_keypoints(np.array([frames[j].process_keypoints() for j in range(i, i + 15)]))
            self.windows[i].set_angles(np.array([frames[j].process_angles() for j in range(i, i + 15)]))
            self.windows[i].set_opticalflow(np.array(opticalflow[i:i + util.getWindowSize()]))

        params = VideoParams(frames, self.category)
        self.parameters = params.extract_parameters()


    # FUNZIONI GET E SET

    def get_windows(self):
        """
        Funzione che restituisce tutte le finestre

        Returns:
        - windows (Array): tutte le finestre del video
        """

        return self.windows

    def get_window(self, num):
        """
        Funzione che restituisce la finestra in posizione num.

        Returns:
        - window (Window): la finestra in posizione num
        """

        return self.windows[num]

    def get_num_windows(self):
        """
        Funzione che restituisce il numero di finestre da cui è composto il video.

        Returns:
        - num_windows (int): numero di finestre da cui è composto il video
        """

        return len(self.windows)

    def get_path(self):
        """
        Funzione che restituisce il percorso del video.

        Returns:
        - path (string): percorso del video
        """

        return self.path

    def get_category(self):
        """
        Funzione che restituisce la categoria del video

        Returns:
        - category (string): categria del video
        """

        return self.category
    

    def get_parameters(self):
        """
        Funzione che restituisce i parametri del video

        Returns:
        - params (Array): parametri del video
        """

        return self.parameters