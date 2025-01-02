import os
import moviepy.editor as mp
import numpy as np
import tqdm

class Videos:

    def __init__(self, folder):
        self.folder = folder


    def get_categories(self):
        """
        Funzione che restituisce la lista delle categorie (cartelle) contenute nella cartella specificata.

        Args:
        - folder_path (str): Il percorso della cartella contenente le cartelle delle categorie

        Returns:
        - list: Una lista contenente i nomi delle categorie
        """

        return os.listdir(self.folder)


    def get_videos(self):
        """
        Funzione che restituisce un dizionario contenente tutti i video.
        Il dizionario ha come chiave il nome dell'esercizio (cartella) e come valore una lista contenente i nomi dei video.

        Args:
        - folder_path (str): Il percorso della cartella contenente i video suddivisi in cartelle per classe

        Returns:
        - dict: Un dizionario contenente i percorsi dei video
        """

        videos = {}
        for exercise in os.listdir(self.folder):
            videos[exercise] = []
            for video in os.listdir(os.path.join(self.folder, exercise)):
                videos[exercise].append((os.path.join(self.folder, exercise, video)).split("\\")[-1])

        return videos
    

    def process_videos(self):
        """
        Funzione che effettua data augmentation sui video.
        Per ogni video nelle cartelle, viene creata una copia specchiata, ruotata, zoomata.

        Args:
        - folder_path (str): Il percorso della cartella contenente i video suddivisi in cartelle per classe
        """

        videos = self.get_videos()

        for exercise in videos:
            for video in tqdm.tqdm(videos[exercise], desc=f"Modify speed of {exercise} videos", unit="video"):
                video_path = os.path.join(self.folder, exercise, video)
                self.speedVideo(video_path, f"{video_path[:-4]}_05.mp4", 0.5)
                self.speedVideo(video_path, f"{video_path[:-4]}_15.mp4", 1.5)

        videos = self.get_videos()

        for exercise in videos:
            for video in tqdm.tqdm(videos[exercise], desc=f"Processing {exercise} videos", unit="video"):
                video_path = os.path.join(self.folder, exercise, video)
                self.mirror_video(video_path, f"{video_path[:-4]}_m.mp4")
                self.rotate_video(video_path, f"{video_path[:-4]}_r.mp4")
                self.zoom_video(video_path, f"{video_path[:-4]}_z.mp4")

    
    def mirror_video(self, inputPath, outputPath):
        """
        Funzione che specchia un video.

        Args:
        - inputPath (str): Il path del video da processare.
        - outputPath (str): Il path del video da salvare.
        """

        # Carica il video
        video = mp.VideoFileClip(inputPath)
        # Specchia il video
        mirrored_video = video.fx(mp.vfx.mirror_x)
        # Salva il video specchiato
        mirrored_video.write_videofile(outputPath, codec='libx264', logger=None, verbose=False)


    def zoom_video(self, inputPath, outputPath, zoom_factor=None):
        """
        Funzione che ingrandisce un video.

        Args:
        - inputPath (str): Il path del video da processare.
        - outputPath (str): Il path del video da salvare.
        """

        # fattore di zoom come numero casuale tra 0.8 e 1.2
        if zoom_factor is None:
            zoom_factor = np.random.uniform(0.8, 1.2)
        # Carica il video
        video = mp.VideoFileClip(inputPath)
        # Calcola le nuove dimensioni
        new_width = video.w * zoom_factor
        new_height = video.h * zoom_factor
        # Applica l'effetto di zoom
        zoomed_video = video.fx(mp.vfx.resize, newsize=(new_width, new_height))
        # Se necessario, ritaglia il video per mantenere le dimensioni originali
        if zoom_factor > 1:
            crop_x = (new_width - video.w) / 2
            crop_y = (new_height - video.h) / 2
            zoomed_video = zoomed_video.fx(mp.vfx.crop, x1=crop_x, y1=crop_y, x2=crop_x + video.w, y2=crop_y + video.h)
        else:
            zoomed_video = zoomed_video.set_position(('center', 'center')).resize((video.w, video.h))
        # Scrivi il video con lo zoom applicato sul file di output
        zoomed_video.write_videofile(outputPath, codec='libx264', logger=None, verbose=False)
    

    def rotate_video(self, inputPath, outputPath, rotation_angle=None):
        """
        Funzione che ruota un video.

        Args:
        - inputPath (str): Il path del video da processare.
        - outputPath (str): Il path del video da salvare.
        """

        # Fattore di rotazione come numero casuale tra -10 e 10
        if rotation_angle is None:
            rotation_angle = np.random.uniform(-10, 10)
        # Carica il video
        video = mp.VideoFileClip(inputPath)
        # Ruota il video di 90 gradi in senso orario
        rotated_video = video.fx(mp.vfx.rotate, rotation_angle)
        # Salva il video ruotato
        rotated_video.write_videofile(outputPath, codec='libx264', logger=None, verbose=False)


    def speedVideo(self, inputPath, outputPath, speedFactor):
        """
        Funzione che modifica la velocità di un video.

        Args:
        - inputPath (str): Il path del video da processare.
        - outputPath (str): Il path del video da salvare.
        - speedFactor (float): Il fattore di velocità.
        """

        if speedFactor <= 0:
            raise ValueError("Il fattore di velocità deve essere maggiore di 0")

        # Carica il video
        video = mp.VideoFileClip(inputPath)
        
        # Modifica la velocità del video
        speeded_video = video.fx(mp.vfx.speedx, speedFactor)
        
        # Salva il video con la nuova velocità
        speeded_video.write_videofile(outputPath, codec='libx264', logger=None, verbose=False)