class Window:
    """
    Classe che rappresenta una finestra temporale di frames.
    """

    def __init__(self, frames):
        """
        Costruttore della classe.

        Args:
        - frames (Array): array di frame
        """

        self.frames = frames
        self.keypoints = None
        self.angles = None
        self.opticalflows = None

    # FUNZIONI GET E SET

    def get_frame(self, num):
        """
        Funzione che restituisce il frame in posizione num.

        Returns:
        - frame (Frame): il frame in posizione num
        """

        return self.frames[num]

    def get_keypoints(self):
        """
        Funzione che restituisce i keypoints

        Returns:
        - keypoints (numpy.ndarray): keypoints della finestra
        """

        return self.keypoints

    def get_angles(self):
        """
        Funzione che restituisce gli angoli della finestra

        Returns:
        - angles (numpy.ndarray): angoli della finestra
        """

        return self.angles

    def get_opticalflow(self):
        """
        Funzione che restituisce l'opticalflow della finestra

        Returns:
        - opticalflow (numpy.ndarray): opticalflow della finestra
        """

        return self.opticalflow

    def set_keypoints(self, keypoints):
        """
        Funzione che setta i keypoints

        Args:
        - keypoints (numpy.ndarray): keypoints della finestra
        """

        self.keypoints = keypoints

    def set_angles(self, angles):
        """
        Funzione che setta gli angoli della finestra

        Args:
        - angles (numpy.ndarray): angoli della finestra
        """

        self.angles = angles

    def set_opticalflow(self, opticalflow):
        """
        Funzione che setta l'opticalflow della finestra

        Args:
        - opticalflow (numpy.ndarray): opticalflow della finestra
        """

        self.opticalflow = opticalflow