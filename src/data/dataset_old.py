import os
import numpy as np
import tqdm
from imblearn.over_sampling import SMOTE
from data.video import Video
from data.frame_mediapipe import Frame
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


    @staticmethod
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
        return video


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

        labels = []
        parameters = {}
        processed_videos = 0

        # Ottengo il numero totale di video da processare
        total_videos = 0
        for category in categories:
            total_videos += len([d for d in os.listdir(os.path.join(util.getVideoPath(), category))])
        if callback:
            callback(0, total_videos)        
        
        for category in categories:  # Processo i video categoria per categoria
            video_category_path = os.path.join(util.getVideoPath(), category)
            subvideos = [d for d in os.listdir(video_category_path)]
            parameters[category] = []  # Inizializzo la lista dei parametri per la categoria

            for video_name in tqdm.tqdm(subvideos, desc=f"Analizzo la categoria {category}", unit="video"):  # Processo tutti i video della categoria
                video_path = os.path.join(video_category_path, video_name)
                video = Video(video_path, category)  # Process del video

                parameters[category].append(video.get_parameters())
                keypoints = []
                opticalflow = []
                angles = []

                for window in video.get_windows():  # Aggiornamento delle features
                    keypoints.append(window.get_keypoints())
                    opticalflow.append(window.get_opticalflow())
                    angles.append(window.get_angles())

                # Salvataggio graduale delle features e delle labels per evitare di saturare la memoria
                util.save_data(keypoints, os.path.join(util.getDatasetPath(), "keypoints.npy"))
                util.save_data(opticalflow, os.path.join(util.getDatasetPath(), "opticalflow.npy"))
                util.save_data(angles, os.path.join(util.getDatasetPath(), "angles.npy"))
                labels.extend([category for _ in range(video.get_num_windows())])

                del video  # Eliminazione del video per liberare memoria
                processed_videos += 1

                if callback:
                    callback(processed_videos, total_videos)

                if Dataset.stop_creation:
                    break

            if Dataset.stop_creation:
                break
            
        
        avg_all = {}
        for category in categories:  # Per ognuna delle categorie
            category_parameters = parameters[category]  # Parametri della categoria: lista di dizionari con keypoints_max, keypoints_min, angles_max, angles_min
            avg_category = {}
            for key in category_parameters[0].keys():  # Per ogni chiave del dizionario (keypoints_max, keypoints_min, angles_max, angles_min)
                avg_category[key] = [None for _ in range(len(category_parameters[0][key]))]
                for i in range(len(category_parameters[0][key])):  # Per ogni elemento della chiave
                    if key == 'keypoints_max' or key == 'keypoints_min':
                        avg_category[key][i] = [None for _ in range(len(category_parameters[0][key][i]))]
                        for j in range(len(category_parameters[0][key][i])):  # per ogni elemento della lista
                            mean = []
                            for k in range(len(category_parameters)):  # Per ogni elemento della categoria
                                mean.append(category_parameters[k][key][i][j])
                            avg_category[key][i][j] = np.mean(mean)
                    else:
                        mean = []
                        for k in range(len(category_parameters)):
                            mean.append(category_parameters[k][key][i])
                        avg_category[key][i] = np.mean(mean)
            avg_all[category] = avg_category
        parameters = avg_all


        # Salvo le labels in un file npy
        np.save(os.path.join(util.getDatasetPath(), "labels.npy"), labels)
        
        if not Dataset.stop_creation:
            # Oversampling del dataset
            # Ottengo i dataset appena creati
            kp = np.load(os.path.join(util.getDatasetPath(), "keypoints.npy"), allow_pickle=True)
            of = np.load(os.path.join(util.getDatasetPath(), "opticalflow.npy"), allow_pickle=True)
            an = np.load(os.path.join(util.getDatasetPath(), "angles.npy"), allow_pickle=True)
            labels = np.load(os.path.join(util.getDatasetPath(), "labels.npy"), allow_pickle=True)
            # Concateno le features
            features = util.concatenate_features(kp, of)
            features = util.concatenate_features(features, an)
            # Applico l'oversampling
            features, labels = self.oversampling(features, labels)
            # Divido le features in keypoints e opticalflow e angles
            num_keypoints_data = Frame.num_keypoints_data
            num_opticalflow_data = Frame.num_opticalflow_data
            kp = features[:, :, :num_keypoints_data]
            of = features[:, :, num_keypoints_data:num_keypoints_data + num_opticalflow_data]
            an = features[:, :, num_keypoints_data + num_opticalflow_data:]
            # Salvo i nuovi dataset
            np.save(os.path.join(util.getDatasetPath(), "keypoints.npy"), kp)
            np.save(os.path.join(util.getDatasetPath(), "opticalflow.npy"), of)
            np.save(os.path.join(util.getDatasetPath(), "angles.npy"), an)
            np.save(os.path.join(util.getDatasetPath(), "labels.npy"), labels)
            # Creo il file dei parametri
            np.save(os.path.join(util.getParametersPath(), "parameters.npy"), parameters)
        else:
            Dataset.stop_creation = False


    @staticmethod
    def stop():
        """
        Funzione che ferma la creazione del dataset.
        """

        Dataset.stop_creation = True
        print("Dataset creation stopped")