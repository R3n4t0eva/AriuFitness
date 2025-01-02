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

    def __init__(self):
        """
        Costruttore della classe Dataset. Inizializza le liste di video e labels.
        """
        
        self.videos = []
        self.labels = []
        self.window_size = 8
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


    '''@staticmethod
    def process_video(video_info):
        """
        Funzione che processa un video.

        Args:
        - video_info (tuple): Una tupla contenente il path del video e la categoria di appartenenza.

        Returns:
        - video (Video): Il video processato.
        """

        video = Video(video_info[0], video_info[1])
        print(f"{video_info[0]} processed")
        return video'''


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

        for category in videos:
            parameters[category] = []

            for video_path in tqdm.tqdm(videos[category], desc=f"Analizzo la categoria {category}", unit="video"):
                cap = cv2.VideoCapture(video_path)
                video_frames = []
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    video_frames.append(Frame(frame))
                cap.release()

                for i in range(len(video_frames)):
                    video_frames[i].interpolate_keypoints(video_frames[i - 1] if i > 0 else None, video_frames[i + 1] if i < len(video_frames) - 1 else None)
                    video_frames[i].extract_angles()

                keypoints_frames = []
                angles_frames = []
                for frame in video_frames:
                    keypoints_frames.append(frame.process_keypoints())
                    angles_frames.append(frame.process_angles())
                
                params = VideoParams(video_frames, category)
                parameters[category].append(params.extract_parameters())

                video_name = os.path.basename(video_path)
                #frames_per_rep = len(video_frames) // self.rep_per_video[category][video_name.split(".")[0]]
                frames_per_rep = len(video_frames) // self.rep_per_video
                frames_interval = frames_per_rep // self.window_size
                last_start_frame = len(video_frames) - self.window_size * frames_interval - 1
                windows_keypoints = [keypoints_frames[i:i + self.window_size * frames_interval:frames_interval] for i in range(0, last_start_frame)]
                windows_angles = [angles_frames[i:i + self.window_size * frames_interval:frames_interval] for i in range(0, last_start_frame)]

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

        '''avg_all = {}
        for category in categories:
            category_parameters = parameters[category]
            avg_category = {}
            for key in category_parameters[0].keys():
                avg_category[key] = [None for _ in range(len(category_parameters[0][key]))]
                for i in range(len(category_parameters[0][key])):
                    if key == 'keypoints_max' or key == 'keypoints_min':
                        avg_category[key][i] = [None for _ in range(len(category_parameters[0][key][i]))]
                        for j in range(len(category_parameters[0][key][i])):
                            mean = []
                            for k in range(len(category_parameters)):
                                mean.append(category_parameters[k][key][i][j])
                            avg_category[key][i][j] = np.mean(mean)
                    else:
                        mean = []
                        for k in range(len(category_parameters)):
                            mean.append(category_parameters[k][key][i])
                        avg_category[key][i] = np.mean(mean)
            avg_all[category] = avg_category
        parameters = avg_all'''

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