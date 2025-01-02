import datetime
import json
import os
from dotenv import load_dotenv
import numpy as np
import mediapipe as mp
#import tensorflow as tf
#import tensorflow_hub as hub
import torch

from learning.models_pytorch import MultiInputLSTM

load_dotenv()


mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

#movenet = hub.load("https://tfhub.dev/google/movenet/singlepose/lightning/4")
#movenet = hub.load("https://www.kaggle.com/models/google/movenet/frameworks/TensorFlow2/variations/singlepose-lightning/versions/4")


def getExerciseCategories():
    """
    Funzione che restituisce la lista delle categorie di esercizi

    Returns:
        list: la lista delle categorie di esercizi
    """

    return [ct for ct in os.getenv("EXERCISE_CATEGORIES").split(",")]


def calculate_angle(a, b, c):
    """
    Funzione che, dati 3 punti con le loro coordinate x e y, restituisce l'ampiezza dell'angolo in gradi

    Args:
    - a (dict): primo angolo
    - b (dict): secondo angolo
    - c (dict): terzo angolo

    Returns:
    - angle (double): angolo in gradi
    """
    radians = np.arctan2(c["y"] - b["y"], c["x"] - b["x"]) - np.arctan2(a["y"] - b["y"], a["x"] - b["x"])
    angle = np.abs(radians*180.0/np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle


def calculate_distance(a, b):
    """
    Funzione che calcola la distanza euclidea tra due punti.

    Args:
    - p1 (Array): primo punto
    - p2 (Array): secondo punto

    Returns:
    - float: distanza euclidea tra i due punti
    """

    return np.sqrt((a['x'] - b['x'])**2 + (a['y'] - b['y'])**2)


def save_data(data, file_path):
    """
    Funzione che salva dati nel file in modalità append

    Args:
    - data: dati da aggiungere al file
    - file_path (string): percorso del file in cui salvare i dati

    Returns:
    - (bool): vero se i dati sono stati salvati correttamente, falso altrimenti
    """

    try:
        if os.path.exists(file_path):
            existing_data = np.load(file_path, allow_pickle=True)
            data = np.concatenate((existing_data, data))
        np.save(file_path, data)
        return True
    except Exception as e:
        return False
    

def concatenate_features(features1, features2):
    """
    Funzione che concatena due insiemi di features.

    Args:
    - features1 (numpy.ndarray): Il primo insieme di features.
    - features2 (numpy.ndarray): Il secondo insieme di features.

    Returns:
    - concatenated_features (numpy.ndarray): Le features concatenate.
    """

    return np.concatenate([features1, features2], axis=2)


def normalize(features):
    """
    Funzione che normalizza un insieme di features.

    Args:
    - features (numpy.ndarray): L'insieme di features da normalizzare.

    Returns:
    - normalized_features (numpy.ndarray): Le features normalizzate.
    """

    min_val = np.min(features)
    max_val = np.max(features)
    return (features - min_val) / (max_val - min_val)


def same_frame(frame1, frame2, threshold=0.08):
    """
    Funzione che riceve in input 2 frame e restituisce True se i keypoints sono molto simili tra loro e False altrimenti.
    La somiglianza è gestita da un valore di soglia.

    Args:
    - frame1 (Frame): primo frame
    - frame2 (Frame): secondo frame

    Returns:
    - bool: True se i frame sono simili, False altrimenti
    """

    keypoints1 = frame1.get_keypoints()
    keypoints2 = frame2.get_keypoints()
    if len(keypoints1) != len(keypoints2):
        return False
    for i in range(len(keypoints1)):
        if abs(keypoints1[i]["x"] - keypoints2[i]["x"]) > threshold or abs(keypoints1[i]["y"] - keypoints2[i]["y"]) > threshold:
            return False
    return True


def get_pytorch_model(model_path):
    """
    Funzione che estrae i migliori iperparametri dal file e crea il modello PyTorch.

    Args:
    - model_path (string): percorso del modello

    Returns:
    - model (nn.Module): modello PyTorch
    """

    best_params = np.load(os.path.join(getModelsPath(), "best_params.npy"), allow_pickle=True).item()
    model = MultiInputLSTM(
        best_params['X1_size'], best_params['X2_size'],
        best_params['hidden_size_1'], best_params['hidden_size_2'], best_params['hidden_size_3'],
        best_params['num_classes'], best_params['dropout_rate'])
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()
    return model


def get_dataset(type):
    """
    Funzione che restituisce il dataset di train o di test.

    Args:
    - type (string): tipo di dataset da restituire ("train" o "test")

    Returns:
    - X1 (numpy.ndarray): dati dei keypoints
    - X2 (numpy.ndarray): dati dell'optical flow
    - X3 (numpy.ndarray): dati degli angoli
    - y (numpy.ndarray): etichette
    """

    if type == "train":
        dataset_path = getDatasetPath()
    elif type == "test":
        dataset_path = getDatasetTestPath()
    else:
        return None
    
    X1 = np.load(os.path.join(dataset_path, "keypoints.npy"))
    X2 = np.load(os.path.join(dataset_path, "opticalflow.npy"))
    X3 = np.load(os.path.join(dataset_path, "angles.npy"))
    y = np.load(os.path.join(dataset_path, "labels.npy"))
    num_classes = len(np.unique(y))
    categories = np.load(os.path.join(dataset_path, "categories.npy"))
    y = np.array([list(categories).index(label) for label in y])

    return X1, X2, X3, y, num_classes


def read_json(file_path):
    """
    Funzione che legge un file JSON.

    Args:
    - file_path (string): percorso del file JSON

    Returns:
    - data (dict): dati letti dal file JSON
    """

    with open(file_path) as f:
        data = json.load(f)
    return data


def write_json(data, file_path):
    """
    Funzione che scrive un file JSON.

    Args:
    - data (dict): dati da scrivere nel file JSON
    - file_path (string): percorso del file JSON

    Returns:
    - (bool): vero se i dati sono stati scritti correttamente, falso altrimenti
    """

    try:
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        return False
    

def get_current_date():
    """
    Restituisce la data corrente nel formato "DD-MM-YYYY-HH-MM-SS"

    Returns:
    - (string): data corrente
    """

    return datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")


def get_current_time():
    """
    Restituisce il tempo corrente che può essere utilizzato per calcolare il tempo trascorso

    Returns:
    - (float): tempo corrente
    """

    return datetime.datetime.now().timestamp()


def get_videos():
    """
    Funzione che restituisce un dizionario contenente tutti i video.
    Il dizionario ha come chiave il nome dell'esercizio (cartella) e come valore una lista contenente i nomi dei video.

    Args:
    - folder_path (str): Il percorso della cartella contenente i video suddivisi in cartelle per classe

    Returns:
    - dict: Un dizionario contenente i percorsi dei video
    """

    videos = {}
    videos_path = getVideoPath()
    for exercise in os.listdir(videos_path):
        videos[exercise] = []
        for type in os.listdir(os.path.join(videos_path, exercise)):
            for video in os.listdir(os.path.join(videos_path, exercise, type)):
                videos[exercise].append((os.path.join(videos_path, exercise, type, video)))
                
    return videos



# ================================================================== #
# ================ FUNZIONI PER IL RECUPERO DEI PATH =============== #
# ================================================================== #

def getBasePath():
    """
    Metodo che ritorna il path base del progetto

    Returns:
        str: il path base del progetto
    """

    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..")


def getVideoPath():
    """
    Funzione che restituisce il percorso della cartella dei video

    Returns:
        str: il percorso della cartella dei video
    """

    return os.path.join(getBasePath(), os.getenv("VIDEO_PATH"))


def getVideoInfoPath():
    """
    Funzione che restituisce il percorso della cartella dei video informativi

    Returns:
        str: il percorso della cartella delle informazioni sui video
    """

    return os.path.join(getBasePath(), os.getenv("VIDEO_INFO_PATH"))


def getDatasetPath():
    """
    Funzione che restituisce il percorso della cartella del dataset

    Returns:
        str: il percorso della cartella del dataset
    """

    return os.path.join(getBasePath(), "dataset", os.getenv("DATASET_TRAIN_PATH"))


def getDatasetTestPath():
    """
    Funzione che restituisce il percorso della cartella del dataset di test

    Returns:
        str: il percorso della cartella del dataset di test
    """

    return os.path.join(getBasePath(), "dataset", os.getenv("DATASET_TEST_PATH"))


def getModelsPath():
    """
    Funzione che restituisce il percorso della cartella dei modelli

    Returns:
        str: il percorso della cartella dei modelli
    """

    return os.path.join(getBasePath(), os.getenv("MODELS_PATH"))


def getParametersPath():
    """
    Funzione che restituisce il percorso della cartella dei parametri

    Returns:
        str: il percorso della cartella dei parametri
    """

    return os.path.join(getBasePath(), "dataset", os.getenv("PARAMETERS_PATH"))


def getUsersPath():
    """
    Funzione che restituisce il percorso della cartella contenenente i dati degli utenti

    Returns:
        str: il percorso della cartella degli utenti
    """

    return os.path.join(getBasePath(), os.getenv("USERS_PATH"))


def getWindowSize():
    """
    Funzione che restituisce la dimensione della finestra

    Returns:
        int: la dimensione della finestra
    """

    return int(os.getenv("WINDOW_SIZE"))