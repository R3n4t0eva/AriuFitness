import util
import os

class Users:
    """
    Classe che gestisce utenti e sessione corrente
    """

    # Attributi statici
    current_session = None
    current_user = None
    credentials_path = os.path.join(util.getUsersPath(), "credentials.json")
    data_path = os.path.join(util.getUsersPath(), "data.json")


    def user_exists(self, username):
        """
        Funzione che verifica se l'utente esiste già

        Args:
        - username (string): username dell'utente

        Returns:
        - (int): indice dell'utente se esiste, -1 altrimenti
        """

        credentials = util.read_json(Users.credentials_path)
        #return username in [credentials[i]["username"] for i in range(len(credentials))]
        for i in range(len(credentials)):
            if username == credentials[i]["username"]:
                return i
        return -1
    

    def add_user(self, username, password):
        """
        Funzione che aggiunge un utente

        Args:
        - username (string): username dell'utente
        - password (string): password dell'utente
        """

        credentials = util.read_json(Users.credentials_path)
        credentials.append({"username": username, "password": password})
        util.write_json(credentials, Users.credentials_path)

    
    def login(self, username, password):
        """
        Funzione che effettua il login e salva l'utente e la sessione corrente

        Args:
        - username (string): username dell'utente
        - password (string): password dell'utente

        Returns:
        - (bool): vero se il login è avvenuto con successo, falso altrimenti
        """

        index = self.user_exists(username)
        if index == -1:
            self.add_user(username, password)
        elif not password == util.read_json(Users.credentials_path)[index]["password"]:
            return False

        date = util.get_current_date()
        Users.current_user = username
        Users.current_session = date
        return True


    def update_session(self, exercise, reps, accuracy, avg_time):
        """
        Funzione che aggiorna i dati relativi all'esercizio eseguito

        Args:
        - exercise (string): esercizio eseguito
        - reps (int): numero di ripetizioni
        - accuracy (float): accuratezza
        - avg_time (float): tempo medio
        """

        data = util.read_json(Users.data_path)
        if Users.current_user not in data.keys():
            data[Users.current_user] = {}

        if Users.current_session not in data[Users.current_user].keys():
            data[Users.current_user][Users.current_session] = {}

        if exercise not in data[Users.current_user][Users.current_session].keys():
            data[Users.current_user][Users.current_session][exercise] = {}
            data[Users.current_user][Users.current_session][exercise]["reps"] = reps
            data[Users.current_user][Users.current_session][exercise]["accuracy"] = accuracy
            data[Users.current_user][Users.current_session][exercise]["avg_time"] = avg_time
        else:
            data[Users.current_user][Users.current_session][exercise]["accuracy"] = (data[Users.current_user][Users.current_session][exercise]["accuracy"] + accuracy) / 2
            data[Users.current_user][Users.current_session][exercise]["avg_time"] = (data[Users.current_user][Users.current_session][exercise]["avg_time"] * data[Users.current_user][Users.current_session][exercise]["reps"] + avg_time * reps) / (data[Users.current_user][Users.current_session][exercise]["reps"] + reps)
            data[Users.current_user][Users.current_session][exercise]["reps"] += reps

        util.write_json(data, Users.data_path)