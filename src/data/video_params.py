import util

class VideoParams:

    # Dizionario che contiene gli angoli che caratterizzano ciascuna categoria
    category_angles = {
        'arms_extension': [3, (7, 8), 4],
        'arms_up': [5, (9, 10), 6],
        'arms_lateral': [3, 1, 7],
        'chair_raises': [8, 7, 10],
        'leg_lateral': [11, (7, 8), 12],
        'seated_crunch': [1, 0, 2]
    }


    def __init__(self, frames, category):
        """
        Costruttore della classe VideoParams

        Args:
        - frames (list): lista di frame
        - category (string): categoria del video
        """

        self.frames = frames
        self.category = category

    
    def extract_parameters(self):
        """
        Estrae i parametri del video

        Returns:
        - dict: parametri del video (keypoints_max, keypoints_min, angles_max, angles_min)
        """

        angle_points = self.category_angles[self.category]
        angles = []

        for i in range(len(self.frames)):
            angle = util.calculate_angle(self.extract_points(self.frames[i], angle_points[0]), self.extract_points(self.frames[i], angle_points[1]), self.extract_points(self.frames[i], angle_points[2]))
            angles.append(angle)

        # Trovo l'indice di angles in cui c'è l'angolo più ampio e quello più stretto
        max_angle_index = angles.index(max(angles))
        min_angle_index = angles.index(min(angles))
        # Aggiungo gli angoli trovati alle liste
        angles_max = max(angles)
        angles_min = min(angles)
        # Aggiungo i frame corrispondenti agli indici trovati
        frame_max = self.frames[max_angle_index]
        frame_min = self.frames[min_angle_index]

        # Estraggo i keypoints dai frame
        keypoints_max = frame_max.process_keypoints().tolist()
        keypoints_min = frame_min.process_keypoints().tolist()

        return {
            'keypoints_max': keypoints_max,
            'keypoints_min': keypoints_min,
            'angles_max': angles_max,
            'angles_min': angles_min
        }


    @staticmethod
    def extract_points(frame, p):
        """
        Funzione statica che restituisce il punto p-esimo del frame.
        Se il punto è una tupla, restituisce il punto medio tra i due punti.

        Args:
        - frame (Frame): frame da cui estrarre il punto
        - p (int, Tuple): punto

        Returns:
        - point (dict): punto
        """
        
        if type(p) == int:
            return frame.get_keypoint(p)
        else:
            a = p[0]
            b = p[1]
            return {
                'x': (frame.get_keypoint(a)['x'] + frame.get_keypoint(b)['x']) / 2,
                'y': (frame.get_keypoint(a)['y'] + frame.get_keypoint(b)['y']) / 2
            }