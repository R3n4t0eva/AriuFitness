import os
import cv2
import numpy as np
import tqdm
from imblearn.over_sampling import SMOTE
#from data.video import Video
from data.frame_mediapipe import Frame
from data.video_params import VideoParams
import util
from dotenv import load_dotenv

load_dotenv()

class Dataset:

    stop_creation = False
    window_size = 8

    def __init__(self):
        """
        Costruttore della classe Dataset. Inizializza le liste di video e labels.
        """
        
        self.videos = []
        self.labels = []
        self.rep_per_video = 10
        '''self.rep_per_video = {
            "arms_lateral": {
                "1": 8
            },
            "arms_up": {
                "1": 8,
                "2": 10
            },
            "leg_lateral": {
                "1": 10
            },
            "arms_extension": {
                "1": 8
            },
            "chair_raises": {
                "1": 8
            },
            "seated_crunch": {
                "1": 10,
                "2": 10
            },
            "knee_up": {
                "1": 10,
                "2": 10
            }
        }'''


    def oversampling(self, X, y):
        """
        Funzione che effettua l'oversampling tramite SMOTE delle classi minoritarie.

        Args:
        - X (numpy.ndarray): Le features del dataset.
        - y (numpy.ndarray): Le labels del dataset.

        Returns:
        - X_resampled (numpy.ndarray): Le features del dataset con oversampling.
        - y_resampled (numpy.ndarray): Le labels del dataset con oversampling.
        """

        X_shape = X.shape

        # Riformatta X per SMOTE (appiana le dimensioni)
        X = X.reshape(X_shape[0], -1)

        # Effettua l'oversampling
        smote = SMOTE(sampling_strategy='auto')
        X_resampled, y_resampled = smote.fit_resample(X, y)

        # Riformatta X in modo che abbia la forma originale
        X_resampled = X_resampled.reshape(-1, *X_shape[1:])

        return X_resampled, y_resampled


    def create(self, callback=None):
        """
        Funzione che crea il dataset per l'addestramento.

        Args:
        - callback (function): Funzione di callback per aggiornare la progressione della creazione del dataset.
        """

        # Se il dataset esiste già lo elimino
        if os.path.exists(util.getDatasetPath()):
            for file in os.listdir(util.getDatasetPath()):
                os.remove(os.path.join(util.getDatasetPath(), file))

        categories = [d for d in os.listdir(util.getVideoPath())]  # Ottengo le categorie di esercizi
        np.save(os.path.join(util.getDatasetPath(), "categories.npy"), categories)  # Salvo le categorie in un file npy

        # Ottengo il numero totale di video da processare
        total_videos = 0
        videos = util.get_videos()
        for category in videos:
            total_videos += len(videos[category])
        if callback:
            callback(0, total_videos)

        labels = []
        parameters = {}
        processed_videos = 0

        for category in videos:  # Per ogni categoria di esercizi
            parameters[category] = []

            for video_path in tqdm.tqdm(videos[category], desc=f"Analizzo la categoria {category}", unit="video"):  # Per ogni video della categoria
                # Estraggo tutti i frame, creao per ognuno un oggetto Frame e lo aggiungo alla lista video_frames
                cap = cv2.VideoCapture(video_path)
                video_frames = []
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    video_frames.append(Frame(frame))
                cap.release()

                # Interpolo i keypoints e calcolo gli angoli per ogni frame
                for i in range(len(video_frames)):
                    video_frames[i].interpolate_keypoints(video_frames[i - 1] if i > 0 else None, video_frames[i + 1] if i < len(video_frames) - 1 else None)
                    video_frames[i].extract_angles()

                # Creo una lista di keypoints e angoli per ogni frame che contengono i keypoints e gli angoli processati di tutti i frame
                keypoints_frames = []
                angles_frames = []
                for frame in video_frames:
                    keypoints_frames.append(frame.process_keypoints())
                    angles_frames.append(frame.process_angles())
                
                '''params = VideoParams(video_frames, category)
                parameters[category].append(params.extract_parameters())'''

                # Ottengo parametri utili alla divisione dei video e alla creazione delle finestre
                video_name = os.path.basename(video_path)
                #rep_per_video_eff = self.rep_per_video[category][video_name.split(".")[0]]
                rep_per_video_eff = self.rep_per_video
                frames_per_rep = len(video_frames) // rep_per_video_eff
                frames_interval = frames_per_rep // Dataset.window_size
                windows_keypoints = []
                windows_angles = []

                # Estraggo i parametri utilizzando le ripetizioni dei video e non il video intero
                for i in range(0, rep_per_video_eff):
                    params = VideoParams(video_frames[i * frames_per_rep: (i * frames_per_rep) + frames_per_rep], category)
                    parameters[category].append(params.extract_parameters())

                for i in range(0, rep_per_video_eff):
                    if i != 0 and i != rep_per_video_eff - 1:
                        for k in range(-5, 6):
                            windows_keypoints.append(keypoints_frames[i * frames_per_rep + k: (i * frames_per_rep + k) + Dataset.window_size * frames_interval: frames_interval])
                            windows_angles.append(angles_frames[i * frames_per_rep + k: (i * frames_per_rep + k) + Dataset.window_size * frames_interval: frames_interval])
                    elif i == 0:
                        for k in range(0, 6):
                            windows_keypoints.append(keypoints_frames[i * frames_per_rep + k: (i * frames_per_rep + k) + Dataset.window_size * frames_interval: frames_interval])
                            windows_angles.append(angles_frames[i * frames_per_rep + k: (i * frames_per_rep + k) + Dataset.window_size * frames_interval: frames_interval])
                    else:
                        for k in range(-5, 1):
                            windows_keypoints.append(keypoints_frames[i * frames_per_rep + k: (i * frames_per_rep + k) + Dataset.window_size * frames_interval: frames_interval])
                            windows_angles.append(angles_frames[i * frames_per_rep + k: (i * frames_per_rep + k) + Dataset.window_size * frames_interval: frames_interval])

                # se sono state create finestre di dimensione diversa da window_size, stampo "errore"
                #print(len(windows_keypoints))
                for w in windows_keypoints[-90:]:
                    if len(w) != Dataset.window_size:
                        print("ERRORE")

                util.save_data(windows_keypoints, os.path.join(util.getDatasetPath(), "keypoints.npy"))
                util.save_data(windows_angles, os.path.join(util.getDatasetPath(), "angles.npy"))
                labels.extend([category for _ in range(len(windows_keypoints))])

                processed_videos += 1

                if callback:
                    callback(processed_videos, total_videos)

                if Dataset.stop_creation:
                    break

            if Dataset.stop_creation:
                break

        new_parameters = {}
        for category in categories:
            avg_all = {}
            for key in parameters[category][0].keys():
                if "keypoints" in key:
                    kp_mean = []
                    for i in range(len(parameters[category][0][key])):
                        mean = []
                        for j in range(len(parameters[category])):
                            mean.append(parameters[category][j][key][i])
                        kp_mean.append(np.mean(mean))
                    avg_all[key] = kp_mean
                else:
                    mean = []
                    for j in range(len(parameters[category])):
                        mean.append(parameters[category][j][key])
                    avg_all[key] = np.mean(mean)
            new_parameters[category] = avg_all
        parameters = new_parameters


        np.save(os.path.join(util.getParametersPath(), "parameters.npy"), parameters)
        np.save(os.path.join(util.getDatasetPath(), "labels.npy"), labels)

        if not Dataset.stop_creation:
            kp = np.load(os.path.join(util.getDatasetPath(), "keypoints.npy"), allow_pickle=True)
            an = np.load(os.path.join(util.getDatasetPath(), "angles.npy"), allow_pickle=True)
            labels = np.load(os.path.join(util.getDatasetPath(), "labels.npy"), allow_pickle=True)
            features = util.concatenate_features(kp, an)
            #features, labels = self.oversampling(features, labels)
            num_keypoints_data = Frame.num_keypoints_data
            num_angles_data = Frame.num_angles_data
            kp = features[:, :, :num_keypoints_data]
            an = features[:, :, num_keypoints_data:]
            np.save(os.path.join(util.getDatasetPath(), "keypoints.npy"), kp)
            np.save(os.path.join(util.getDatasetPath(), "angles.npy"), an)
            np.save(os.path.join(util.getDatasetPath(), "labels.npy"), labels)
        else:
            Dataset.stop_creation = False


    @staticmethod
    def stop():
        """
        Funzione che ferma la creazione del dataset.
        """

        Dataset.stop_creation = True
        print("Dataset creation stopped")