import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.init as init
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
import optuna
import util


# Dispositivo su cui eseguire il training: GPU se disponibile, altrimenti CPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

best_accuracy = 0.0


class EarlyStopping:
    """
    Classe che implementa la tecnica di early stopping per fermare l'addestramento del modello.
    """

    def __init__(self, patience=5, min_delta=0):
        """
        Costruttore della classe EarlyStopping.

        Args:
        - patience (int): numero di epoche senza miglioramenti prima di fermare l'addestramento.
        - min_delta (float): soglia minima di miglioramento.
        """
        self.patience = patience
        self.min_delta = min_delta
        self.best_score = None
        self.counter = 0
        self.early_stop = False

    def __call__(self, val_loss, model, path):
        """
        Funzione che controlla se il modello ha smesso di migliorare e, in caso affermativo, ferma l'addestramento, salvando il modello come checkpoint.

        Args:
        - val_loss (float): valore della loss di validazione.
        - model (torch.nn.Module): modello da controllare.
        - path (str): percorso in cui salvare il modello.
        """

        score = -val_loss

        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(model, path)
        elif score < self.best_score + self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.save_checkpoint(model, path)
            self.counter = 0

    def save_checkpoint(self, model, path):
        """
        Funzione che salva il modello come checkpoint.

        Args:
        - model (torch.nn.Module): modello da salvare.
        - path (str): percorso in cui salvare il modello.
        """

        torch.save(model.state_dict(), path)
        print("Model saved as checkpoint")



class MultiInputLSTM(nn.Module):
    """
    Classe che definisce il modello LSTM a tre input.
    """

    def __init__(self, input_size_1, input_size_2, input_size_3, hidden_size_1, hidden_size_2, hidden_size_3, num_classes, dropout_rate):
        """
        Costruttore della classe MultiInputLSTM. Inizializza i layer LSTM e i layer fully connected.

        Args:
        - input_size_1 (int): dimensione dell'input del primo ramo.
        - input_size_2 (int): dimensione dell'input del secondo ramo.
        - input_size_3 (int): dimensione dell'input del terzo ramo.
        - hidden_size_1 (int): dimensione dell'hidden state del primo layer LSTM di ogni ramo.
        - hidden_size_2 (int): dimensione dell'hidden state del secondo layer LSTM di ogni ramo.
        - hidden_size_3 (int): dimensione dell'hidden state del layer fully connected.
        - num_classes (int): numero di classi.
        - dropout_rate (float): rate di dropout.
        """

        super(MultiInputLSTM, self).__init__()

        self.lstm1_1 = nn.LSTM(input_size_1, hidden_size_1, 1, batch_first=True, bidirectional=False)
        self.dropout1_1 = nn.Dropout(dropout_rate)
        self.lstm2_1 = nn.LSTM(hidden_size_1, hidden_size_2, 1, batch_first=True, bidirectional=False)
        self.dropout2_1 = nn.Dropout(dropout_rate)

        self.lstm1_2 = nn.LSTM(input_size_2, hidden_size_1, 1, batch_first=True, bidirectional=False)
        self.dropout1_2 = nn.Dropout(dropout_rate)
        self.lstm2_2 = nn.LSTM(hidden_size_1, hidden_size_2, 1, batch_first=True, bidirectional=False)
        self.dropout2_2 = nn.Dropout(dropout_rate)

        self.lstm1_3 = nn.LSTM(input_size_3, hidden_size_1, 1, batch_first=True, bidirectional=False)
        self.dropout1_3 = nn.Dropout(dropout_rate)
        self.lstm2_3 = nn.LSTM(hidden_size_1, hidden_size_2, 1, batch_first=True, bidirectional=False)
        self.dropout2_3 = nn.Dropout(dropout_rate)
        
        self.fc1 = nn.Linear(hidden_size_2 * 3, hidden_size_3)
        self.relu = nn.ReLU()
        self.dropout_4 = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(hidden_size_3, num_classes)
        self.sigmoid = nn.Sigmoid()

        self.init_weights()

    def init_weights(self):
        """
        Funzione che inizializza i pesi del modello.
        """

        for name, param in self.named_parameters():
            if 'weight' in name:
                init.xavier_uniform_(param)
            elif 'bias' in name:
                init.constant_(param, 0.0)
    
    def forward(self, x1, x2, x3):
        """
        Funzione che definisce il forward pass del modello con i tre input.

        Args:
        - x1 (torch.Tensor): input del primo ramo.
        - x2 (torch.Tensor): input del secondo ramo.
        - x3 (torch.Tensor): input del terzo ramo.

        Returns:
        - out (torch.Tensor): output del modello.
        """

        out1, _ = self.lstm1_1(x1)
        out1 = self.dropout1_1(out1)
        out1, _ = self.lstm2_1(out1)
        out1 = self.dropout2_1(out1)
        out1 = out1[:, -1, :]

        out2, _ = self.lstm1_2(x2)
        out2 = self.dropout1_2(out2)
        out2, _ = self.lstm2_2(out2)
        out2 = self.dropout2_2(out2)
        out2 = out2[:, -1, :]

        out3, _ = self.lstm1_3(x3)
        out3 = self.dropout1_3(out3)
        out3, _ = self.lstm2_3(out3)
        out3 = self.dropout2_3(out3)
        out3 = out3[:, -1, :]

        concatenated = torch.cat((out1, out2, out3), 1)
        out = self.fc1(concatenated)
        out = torch.nn.functional.relu(out)
        out = self.relu(out)
        out = self.dropout_4(out)
        out = self.fc2(out)
        out = self.sigmoid(out)
        return out
    

class CustomDataset(Dataset):
    """
    Classe che definisce un dataset custom per PyTorch.
    """

    def __init__(self, X1, X2, X3, y):
        """
        Costruttore della classe CustomDataset.

        Args:
        - X1 (numpy.ndarray): primo insieme di features.
        - X2 (numpy.ndarray): secondo insieme di features.
        - X3 (numpy.ndarray): terzo insieme di features.
        - y (numpy.ndarray): labels.
        """

        self.X1 = torch.tensor(X1, dtype=torch.float32)
        self.X2 = torch.tensor(X2, dtype=torch.float32)
        self.X3 = torch.tensor(X3, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        """
        Funzione che ritorna la lunghezza del dataset.

        Returns:
        - len (int): lunghezza del dataset.
        """

        return len(self.y)
    
    def __getitem__(self, idx):
        """
        Funzione che restituisce un elemento del dataset.

        Args:
        - idx (int): indice dell'elemento da restituire.

        Returns:
        - X1[idc] (torch.Tensor): primo insieme di features.
        - X2[idc] (torch.Tensor): secondo insieme di features.
        - X3[idc] (torch.Tensor): terzo insieme di features.
        - y[idc] (torch.Tensor): label.
        """

        return self.X1[idx], self.X2[idx], self.X3[idx], self.y[idx]
    


def train_model(model, train_loader, val_loader, criterion, optimizer, regularizer, weight_decay_rate, num_epochs=20, patience=5, trial=None):
    """
    Funzione che addestra un modello.

    Args:
    - model (torch.nn.Module): modello da addestrare.
    - train_loader (torch.utils.data.DataLoader): dataloader per il training.
    - val_loader (torch.utils.data.DataLoader): dataloader per la validazione.
    - criterion (torch.nn.Module): funzione di loss.
    - optimizer (torch.optim.Optimizer): ottimizzatore.
    - regularizer (str): tipo di regolarizzazione.
    - weight_decay_rate (float): tasso di decay per la regolarizzazione.
    - num_epochs (int): numero di epoche.
    - patience (int): patience per l'early stopping.

    Returns:
    - model (torch.nn.Module): modello addestrato.
    """

    early_stopping = EarlyStopping(patience=patience, min_delta=0)
    model.train()  # Modello impostato in modalità training

    for epoch in range(num_epochs):
        epoch_loss = 0

        for X1_batch, X2_batch, X3_batch, y_batch in train_loader:
            # Spostamento dei tensori sul dispositivo (cpu o gpu)
            X1_batch = X1_batch.to(device)
            X2_batch = X2_batch.to(device)
            X3_batch = X3_batch.to(device)
            y_batch = y_batch.to(device)

            optimizer.zero_grad()  # Resetto i gradienti
            outputs = model(X1_batch, X2_batch, X3_batch)  # Forward pass
            loss = criterion(outputs, y_batch)  # Calcolo della loss

            if regularizer == 'l1':  # Nel caso di regolarizzazione L1 si aggiunge il termine di regolarizzazione alla loss
                l1_penalty = sum(param.abs().sum() for param in model.parameters())
                loss += weight_decay_rate * l1_penalty

            loss.backward()  # backward pass per calcolare i gradienti
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # Clipping dei gradienti: fa in modo che il gradiente non cresca troppo
            optimizer.step()  # Aggiornamento dei pesi
            epoch_loss += loss.item()  # Aggiornamento della loss

        print(f"\nEpoch {epoch + 1}/{num_epochs}\nTraining Loss: {epoch_loss / len(train_loader):.4f}")  # Stampa della loss di training

        # Validation
        model.eval()  # Modello impostato in modalità valutazione
        val_loss = 0  # Inizializzazione della loss di validazione
        val_predictions = []  # Inizializzazione delle predizioni
        val_true_labels = []  # Inizializzazione delle label reali

        with torch.no_grad():
            for X1_val_batch, X2_val_batch, X3_val_batch, y_val_batch in val_loader:
                # Spostamento dei tensori sul dispositivo (cpu o gpu)
                X1_val_batch = X1_val_batch.to(device)
                X2_val_batch = X2_val_batch.to(device)
                X3_val_batch = X3_val_batch.to(device)
                y_val_batch = y_val_batch.to(device)

                outputs = model(X1_val_batch, X2_val_batch, X3_val_batch)  # Forward pass della validazione
                loss = criterion(outputs, y_val_batch)  # Calcolo della loss della validazione
                val_loss += loss.item()  # Aggiornamento della loss della validazione

                val_predictions.extend(outputs.cpu().numpy())  # Aggiornamento delle predizioni
                val_true_labels.extend(y_val_batch.cpu().numpy())  # Aggiornamento delle label reali

        avg_val_loss = val_loss / len(val_loader)
        print(f"Validation Loss: {avg_val_loss:.4f}")  # Stampa della loss di validazione

        # Stampa dei valori unici delle classi predette e delle classi reali
        val_predictions = np.array(val_predictions)
        val_true_labels = np.array(val_true_labels)
        print("Unique predicted classes:", np.unique(np.argmax(val_predictions, axis=1)))
        print("Unique true classes:", np.unique(np.argmax(val_true_labels, axis=1)))

        # Check early stopping
        early_stopping(val_loss / len(val_loader), model, os.path.join(util.getModelsPath(), 'checkpoint.pth'))
        if early_stopping.early_stop:
            print("\nEarly stopping")
            break

        '''if trial is not None:
            trial.report(avg_val_loss, step=epoch)
            if trial.should_prune():
                raise optuna.TrialPruned()'''

        model.train()  # Modello impostato in modalità training
        
    # Caricamento del modello con i pesi migliori (checkpoint dell'early stopping)
    model.load_state_dict(torch.load(os.path.join(util.getModelsPath(), 'checkpoint.pth')))
    return model


def evaluate_model(model, X1_test, X2_test, X3_test, y_test, custom_device=None):
    """
    Funzione che valuta un modello.

    Args:
    - model (torch.nn.Module): modello da valutare.
    - X1_test (numpy.ndarray): features del primo ramo.
    - X2_test (numpy.ndarray): features del secondo ramo.
    - X3_test (numpy.ndarray): features del terzo ramo.
    - y_test (numpy.ndarray): labels.

    Returns:
    - accuracy (float): accuracy del modello.
    """

    # Spostamento dei tensori sul dispositivo (cpu o gpu)
    X1_test = torch.tensor(X1_test, dtype=torch.float32).to(device if custom_device is None else custom_device)
    X2_test = torch.tensor(X2_test, dtype=torch.float32).to(device if custom_device is None else custom_device)
    X3_test = torch.tensor(X3_test, dtype=torch.float32).to(device if custom_device is None else custom_device)
    y_test = torch.tensor(y_test, dtype=torch.float32).to(device if custom_device is None else custom_device)

    model.eval()  # Modello impostato in modalità valutazione

    with torch.no_grad():  # Disabilita il calcolo dei gradienti
        outputs = model(X1_test, X2_test, X3_test)  # Forward pass
        predictions = outputs.cpu().numpy()  # Predizioni del modello
        y_pred = (predictions == predictions.max(axis=1)[:, None]).astype(int)  # Conversione delle predizioni in array di 0 e 1 (one-hot encoding)
        y_test = y_test.cpu().numpy()  # Conversione delle label in array numpy

        # Calcolo e stampa delle metriche
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        print(f"\nEvaluation Metrics\nAccuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1 Score: {f1:.4f}")

        return accuracy


def save_model(model, file_path):
    """
    Funzione che salva un modello in un file.

    Args:
    - model (torch.nn.Module): modello da salvare.
    - file_path (str): percorso in cui salvare il modello.
    """

    torch.save(model.state_dict(), file_path)


def load_model(model, file_path):
    """
    Funzione che carica un modello da un file.

    Args:
    - model (torch.nn.Module): modello da caricare.
    - file_path (str): percorso da cui caricare il modello.
    """

    model.load_state_dict(torch.load(file_path))
    model.eval()


def objective(trial, X1_train, X2_train, X3_train, y_train, X1_val, X2_val, X3_val, y_val, num_classes):
    """
    Funzione obiettivo per l'ottimizzazione degli iperparametri.

    Args:
    - trial (optuna.Trial): oggetto trial per l'ottimizzazione.
    - X1_train (numpy.ndarray): features del primo ramo per il training.
    - X2_train (numpy.ndarray): features del secondo ramo per il training.
    - X3_train (numpy.ndarray): features del terzo ramo per il training.
    - y_train (numpy.ndarray): labels per il training.
    - X1_val (numpy.ndarray): features del primo ramo per la validazione.
    - X2_val (numpy.ndarray): features del secondo ramo per la validazione.
    - X3_val (numpy.ndarray): features del terzo ramo per la validazione.
    - y_val (numpy.ndarray): labels per la validazione.
    - num_classes (int): numero di classi.

    Returns:
    - val_accuracy (float): accuracy del modello.
    """

    # Conversione dei dati da numpy a tensori PyTorch e one-hot encoding delle labels
    y_train = torch.from_numpy(y_train).int().to(torch.long)
    y_val = torch.from_numpy(y_val).int().to(torch.long)
    y_train = torch.nn.functional.one_hot(y_train, num_classes=num_classes).float()
    y_val = torch.nn.functional.one_hot(y_val, num_classes=num_classes).float()

    # Definizione degli iperparametri da ottimizzare

    
    hyperparameters = {
        'num_epochs': trial.suggest_int('num_epochs', 20, 30),
        'hidden_size_1': trial.suggest_int('hidden_size_1', 64, 96, step=32),
        'hidden_size_2': trial.suggest_int('hidden_size_2', 32, 64, step=32),
        'hidden_size_3': trial.suggest_int('hidden_size_3', 32, 96, step=32),
        'dropout_rate': trial.suggest_float('dropout_rate', 0.2, 0.4, step=0.1),
        'learning_rate': trial.suggest_loguniform('learning_rate', 1e-5, 1e-2),
        'batch_size': trial.suggest_int('batch_size', 16, 64, step=16),
        'regularizer': trial.suggest_categorical('regularizer', ['l1', 'l2']),
        'weight_decay_rate': trial.suggest_loguniform('weight_decay_rate', 1e-6, 1e-2),
        'optimizer': trial.suggest_categorical('optimizer', ['adam', 'sgd'])
    }

    print(f"\nHyperparameters:\n{hyperparameters}")
    
    model = MultiInputLSTM(  # Creazione del modello con gli iperparametri e spostamento sul dispositivo (cpu o gpu)
        input_size_1=X1_train.shape[2], 
        input_size_2=X2_train.shape[2], 
        input_size_3=X3_train.shape[2], 
        hidden_size_1=hyperparameters['hidden_size_1'],
        hidden_size_2=hyperparameters['hidden_size_2'],
        hidden_size_3=hyperparameters['hidden_size_3'],
        num_classes=num_classes, 
        dropout_rate=hyperparameters['dropout_rate']
    ).to(device)
    
    criterion = nn.BCELoss()  # Funzione di loss Binary Cross Entropy
    if hyperparameters['regularizer'] == 'l2':  # Definizione dell'ottimizzatore in base al regolarizzatore
        optimizer = optim.Adam(model.parameters(), lr=hyperparameters['learning_rate'], weight_decay=hyperparameters['weight_decay_rate']) if hyperparameters['optimizer'] == 'adam' else optim.SGD(model.parameters(), lr=hyperparameters['learning_rate'], weight_decay=hyperparameters['weight_decay_rate'])
    else:
        optimizer = optim.Adam(model.parameters(), lr=hyperparameters['learning_rate']) if hyperparameters['optimizer'] == 'adam' else optim.SGD(model.parameters(), lr=hyperparameters['learning_rate'])
    
    # Creazione dei dataloader per il training e la validazione
    train_dataset = CustomDataset(X1_train, X2_train, X3_train, y_train)
    train_loader = DataLoader(train_dataset, batch_size=hyperparameters['batch_size'], shuffle=False)
    val_dataset = CustomDataset(X1_val, X2_val, X3_val, y_val)
    val_loader = DataLoader(val_dataset, batch_size=hyperparameters['batch_size'], shuffle=False)

    # Addestramento del modello e valutazione
    model = train_model(model, train_loader, val_loader, criterion, optimizer, hyperparameters['regularizer'], hyperparameters['weight_decay_rate'], num_epochs=hyperparameters['num_epochs'], trial=trial)
    val_accuracy = evaluate_model(model, X1_val, X2_val, X3_val, y_val)

    # Se l'accuracy è migliore della migliore trovata finora, salvo il modello
    global best_accuracy
    if val_accuracy > best_accuracy:
        best_accuracy = val_accuracy
        save_model(model, os.path.join(util.getModelsPath(), 'LSTM_Combo3.pth'))

    # Report dell'Hyperband per la potatura
    '''trial.report(val_accuracy, step=hyperparameters['num_epochs'])
    if trial.should_prune():
        raise optuna.TrialPruned()'''

    return val_accuracy


def train_best_model(best_param, X1, X2, X3, y, X1_val, X2_val, X3_val, y_val, num_classes, save_path):
    """
    Funzione che addestra il modello con i migliori iperparametri trovati.

    Args:
    - best_param (dict): migliori iperparametri.
    - X1 (numpy.ndarray): features del primo ramo per il training.
    - X2 (numpy.ndarray): features del secondo ramo per il training.
    - X3 (numpy.ndarray): features del terzo ramo per il training.
    - y (numpy.ndarray): labels per il training.
    - X1_val (numpy.ndarray): features del primo ramo per la validazione.
    - X2_val (numpy.ndarray): features del secondo ramo per la validazione.
    - X3_val (numpy.ndarray): features del terzo ramo per la validazione.
    - y_val (numpy.ndarray): labels per la validazione.
    - num_classes (int): numero di classi.
    - save_path (str): percorso in cui salvare il modello.
    """

    # Conversione dei dati da numpy a tensori PyTorch e one-hot encoding delle labels
    y = torch.from_numpy(y).int().to(torch.long)
    y_val = torch.from_numpy(y_val).int().to(torch.long)
    y = torch.nn.functional.one_hot(y, num_classes=num_classes).float()
    y_val = torch.nn.functional.one_hot(y_val, num_classes=num_classes).float()

    model = MultiInputLSTM(  # Creazione del modello con i migliori iperparametri e spostamento sul dispositivo (cpu o gpu)
        input_size_1=X1.shape[2], 
        input_size_2=X2.shape[2], 
        input_size_3=X3.shape[2], 
        hidden_size_1=best_param['hidden_size_1'], 
        hidden_size_2=best_param['hidden_size_2'], 
        hidden_size_3=best_param['hidden_size_3'],
        num_classes=num_classes, 
        dropout_rate=best_param['dropout_rate']
    ).to(device)

    criterion = nn.BCELoss()  # Funzione di loss Binary Cross Entropy
    
    # Definizione dell'ottimizzatore in base al regolarizzatore
    optimizer = best_param['optimizer']
    regularizer = best_param['regularizer']
    weight_decay_rate = best_param['weight_decay_rate']
    learning_rate = best_param['learning_rate']
    if regularizer == 'l2':
        optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay_rate) if optimizer == 'adam' else optim.SGD(model.parameters(), lr=learning_rate, weight_decay=weight_decay_rate)
    else:
        optimizer = optim.Adam(model.parameters(), lr=learning_rate) if optimizer == 'adam' else optim.SGD(model.parameters(), lr=learning_rate)
    
    # Creazione dei dataloader per il training e la validazione
    train_dataset = CustomDataset(X1, X2, X3, y)
    train_loader = DataLoader(train_dataset, batch_size=best_param['batch_size'], shuffle=False)
    val_dataset = CustomDataset(X1_val, X2_val, X3_val, y_val)
    val_loader = DataLoader(val_dataset, batch_size=best_param['batch_size'], shuffle=False)

    train_model(model, train_loader, val_loader, criterion, optimizer, regularizer, weight_decay_rate, num_epochs=best_param['num_epochs'])  # Addestramento del modello
    save_model(model, os.path.join(save_path, 'LSTM_Combo3_new.pth'))  # Salvataggio del modello
    print("Modello salvato con successo")


def create_model(X1, X2, X3, y, X1_test, X2_test, X3_test, y_test, num_classes):
    """
    Funzione che crea il modello e ne ottimizza gli iperparametri.

    Args:
    - X1 (numpy.ndarray): features del primo ramo per il training.
    - X2 (numpy.ndarray): features del secondo ramo per il training.
    - X3 (numpy.ndarray): features del terzo ramo per il training.
    - y (numpy.ndarray): labels per il training.
    - X1_test (numpy.ndarray): features del primo ramo per la validazione.
    - X2_test (numpy.ndarray): features del secondo ramo per la validazione.
    - X3_test (numpy.ndarray): features del terzo ramo per la validazione.
    - y_test (numpy.ndarray): labels per la validazione.
    - num_classes (int): numero di classi.
    """

    pruner = optuna.pruners.HyperbandPruner(min_resource=1, max_resource=20, reduction_factor=3)
    study = optuna.create_study(direction='maximize', pruner=pruner)
    study.optimize(lambda trial: objective(trial, X1, X2, X3, y, X1_test, X2_test, X3_test, y_test, num_classes), n_trials=50)
    best_params = study.best_params
    print(f"\nBest params: {best_params}")
    best_params['X1_size'] = X1.shape[2]
    best_params['X2_size'] = X2.shape[2]
    best_params['X3_size'] = X3.shape[2]
    best_params['num_classes'] = num_classes
    np.save(os.path.join(util.getModelsPath(), 'best_params.npy'), best_params)
    print("Salvati in 'best_params.npy'")
    #print("\nAddestramento del modello con i migliori iperparametri...")
    #train_best_model(best_params, X1, X2, X3, y, X1_test, X2_test, X3_test, y_test, num_classes, util.getModelsPath())
    
    global best_accuracy
    best_accuracy = 0.0