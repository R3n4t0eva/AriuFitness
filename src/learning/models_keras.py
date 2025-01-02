import numpy as np
import tensorflow as tf
import os
import util
from data.data_augmentation_old import Videos
from keras.layers import LSTM, Dense, Dropout, Input, Concatenate
from keras.optimizers import Adam, SGD
from keras.models import Model
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
import kerastuner as kt


class MetricsCallback(tf.keras.callbacks.Callback):
    """
    Classe per il calcolo delle metriche di precision, recall e F1 score alla fine di ogni epoca.
    """
    
    def __init__(self, validation_data):
        """
        Costruttore della classe. Inizializza i dati di validazione.

        Args:
            validation_data (tuple): Dati di validazione.
        """
        
        super(MetricsCallback, self).__init__()
        self.validation_data = validation_data

    def on_epoch_end(self, epoch, logs=None):
        """
        Funzione chiamata alla fine di ogni epoca. Calcola le metriche di precision, recall e F1 score.
        Le metriche vengono calcolate utilizzando le funzioni di sklearn, stampate a video e salvate nei logs.

        Args:
            epoch (int): Numero dell'epoca.
            logs (dict): Dizionario dei logs.
        """

        # Ottengo i dati di validazione
        X_val, y_val = self.validation_data

        # Predico la classe
        #y_pred = np.argmax(self.model.predict(X_val), axis=1)
        # y_pred è un vettore in cui l'argomento magiore assume valore 1 e tutti gli altri 0
        y_pred = self.model.predict(X_val)
        print(y_pred)
        y_pred = (y_pred == y_pred.max(axis=1)[:, None]).astype(int)
        print(y_pred)
        print(y_val)

        # Calcolo precision, recall e F1 score utilizzando le funzioni di sklearn
        accuracy = accuracy_score(y_val, y_pred)
        precision = precision_score(y_val, y_pred, average='weighted')
        recall = recall_score(y_val, y_pred, average='weighted')
        f1 = f1_score(y_val, y_pred, average='weighted')

        # Stampo le metriche
        print(f"Epoch {epoch + 1}: Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1 Score: {f1:.4f}")

        # Salvo le metriche nei logs
        logs['test_accuracy'] = accuracy
        logs['test_precision'] = precision
        logs['test_recall'] = recall
        logs['test_f1score'] = f1


class HyperLSTMCombo3(kt.HyperModel):
    """
    Classe per la definizione del modello da ottimizzare con Keras Tuner.
    """

    def __init__(self, X1, X2, X3, num_classes):
        """
        Costruttore della classe. Inizializza i dati e il numero di classi.

        Args:
            X1 (np.array): Dati dei keypoints.
            X2 (np.array): Dati dell'optical flow.
            X3 (np.array): Dati degli angoli.
            num_classes (int): Numero di classi.
        """

        self.X1 = X1
        self.X2 = X2
        self.X3 = X3
        self.num_classes = num_classes

    def build(self, hp):
        """
        Funzione per la costruzione del modello da ottimizzare.
        Viene definito un modello LSTM a tre rami, uno per ogni tipo di dato.

        Args:
            hp (HyperParameters): Iperparametri da ottimizzare.

        Returns:
            model (Model): Modello da ottimizzare.
        """

        input_keypoints = Input(shape=(self.X1.shape[1], self.X1.shape[2]))
        input_opticalflow = Input(shape=(self.X2.shape[1], self.X2.shape[2]))
        input_angles = Input(shape=(self.X3.shape[1], self.X3.shape[2]))

        # definisco gli iperparametri
        lstm_units_1 = hp.Int('lstm_units_1', min_value=32, max_value=96, step=32)                      # unità del primo layer LSTM
        lstm_units_2 = hp.Int('lstm_units_2', min_value=32, max_value=96, step=32)                      # unità del secondo layer LSTM
        dropout_rate = hp.Float('dropout_rate', 0.2, 0.5, step=0.1)                                     # rate di dropout
        dense_units = hp.Int('dense_units', min_value=32, max_value=96, step=32)                        # unità del layer dense
        optimizer = hp.Choice('optimizer', values=['adam', 'sgd'])                                      # ottimizzatore
        regularizer = hp.Choice('regularizer', values=['l1', 'l2'])                                     # regolarizzatore
        learning_rate = hp.Float('learning_rate', min_value=1e-4, max_value=1e-2, sampling='linear')    # learning rate

        # Setto il learning rate dell'ottimizzatore
        if optimizer == 'adam':
            optimizer = Adam(learning_rate=learning_rate)
        elif optimizer == 'sgd':
            optimizer = SGD(learning_rate=learning_rate)
        
        # Definizione dei rami LSTM: ognuno dei tre rami è composto da due layer LSTM seguiti da un layer di dropout
        kp = LSTM(units=lstm_units_1, return_sequences=True, kernel_regularizer=regularizer)(input_keypoints)
        kp = Dropout(dropout_rate)(kp)
        kp = LSTM(units=lstm_units_2, return_sequences=False, kernel_regularizer=regularizer)(kp)
        kp = Dropout(dropout_rate)(kp)

        of = LSTM(units=lstm_units_1, return_sequences=True, kernel_regularizer=regularizer)(input_opticalflow)
        of = Dropout(dropout_rate)(of)
        of = LSTM(units=lstm_units_2, return_sequences=False, kernel_regularizer=regularizer)(of)
        of = Dropout(dropout_rate)(of)

        an = LSTM(units=lstm_units_1, return_sequences=True, kernel_regularizer=regularizer)(input_angles)
        an = Dropout(dropout_rate)(an)
        an = LSTM(units=lstm_units_2, return_sequences=False, kernel_regularizer=regularizer)(an)
        an = Dropout(dropout_rate)(an)

        # Concatenazione dei rami LSTM
        concatenated = Concatenate()([kp, of, an])
        # Dense layer
        dense = Dense(units=dense_units, activation='relu')(concatenated)
        # Output layer
        output = Dense(self.num_classes, activation='sigmoid')(dense)
        # Modello
        model = Model(inputs=[input_keypoints, input_opticalflow, input_angles], outputs=output)

        # Compila il modello
        model.compile(
            optimizer=optimizer,
            #loss='sparse_categorical_crossentropy',  # Funzione di perdita per multi-class
            loss='binary_crossentropy',  # Funzione di perdita per multi-label
            metrics=['accuracy']  # Metriche da monitorare
        )

        return model
    
    def fit(self, hp, model, *args, **kwargs):
        """
        Funzione che adatta il metodo fit di Keras Tuner per rendere la batch size un iperparametro.
        """
        
        return model.fit(*args, batch_size=hp.Int('batch_size', 16, 64, step=16), **kwargs)
    


# ======================= RICERCA DEGLI IPERPARAMETRI E ADDESTRAMENTO DEL MODELLO =========================== #

def create_model(X1, X2, X3, y, X1_test, X2_test, X3_test, y_test, num_classes):
    """
    Funzione per la ricerca degli iperparametri e l'addestramento del modello LSTM a tre rami.

    Args:
        X1 (np.array): Dati dei keypoints.
        X2 (np.array): Dati dell'optical flow.
        X3 (np.array): Dati degli angoli.
        y (np.array): Etichette.
        num_classes (int): Numero di classi.

    Returns:
        best_model (Model): Modello addestrato con i migliori iperparametri.
    """

    # codifica one-hot delle etichette
    y = tf.keras.utils.to_categorical(y, num_classes)
    y_test = tf.keras.utils.to_categorical(y_test, num_classes)

    # Inizializza il tuner
    tuner = kt.Hyperband(
        HyperLSTMCombo3(X1, X2, X3, num_classes),
        objective=kt.Objective('test_accuracy', direction='max'),
        max_epochs=20,
        hyperband_iterations=2,
        directory=os.path.join(util.getModelsPath(), 'LSTM_Combo3_optimization'),
        project_name='best_hyperparameters'
    )

    # Definisco l'EarlyStopping
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss',
        mode='auto',
        patience=10,
        restore_best_weights=True
    )

    # Creo i dati di validazione
    validation_data = ([X1_test, X2_test, X3_test], y_test)

    # Definisco il calcolo delle metriche come funzione di callback
    metrics_callback = MetricsCallback(validation_data)

    # Esegui la ricerca degli iperparametri
    tuner.search([X1, X2, X3], y, 
                epochs=30,
                validation_data=validation_data,
                callbacks=[early_stopping, metrics_callback])

    # Visualizza i risultati della ricerca
    tuner.results_summary()

    # ottieni il modello migliore
    best_model = tuner.get_best_models(num_models=1)[0]

    # Salva il modello
    best_model.save(os.path.join(util.getModelsPath(), "LSTM_Combo3_new.h5"))

    return best_model
