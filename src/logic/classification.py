import time
from typing import Any, Callable, Optional


class Classification:
    """
    Implementazione "demo" senza AI/modello.

    Mantiene la stessa interfaccia usata da GUI Desktop e WebSocket,
    ma genera output fittizio (ripetizioni/feedback/keypoints) per consentire
    di valutare l'estetica dell'app senza dipendenze ML.
    """

    def __init__(self, model_path: Optional[str] = None):
        self._active_exercise_label: Optional[str] = None
        self._reps: int = 0
        self._last_rep_ts: float = time.time()

    def set_active_exercise(self, exercise_name: str):
        self._active_exercise_label = exercise_name
        self._reps = 0
        self._last_rep_ts = time.time()

    # Alias usato dalla GUI desktop in alcune versioni
    def set_exercise(self, exercise_name: str):
        self.set_active_exercise(exercise_name)

    def reset_current_reps(self):
        self._reps = 0
        self._last_rep_ts = time.time()

    def stop_exercise(self):
        self._active_exercise_label = None
        self._reps = 0

    def classify(self, frame: Any, callback: Optional[Callable[..., None]] = None):
        # Simula un incremento di ripetizioni ~1/sec quando un esercizio è attivo
        now = time.time()
        if self._active_exercise_label:
            if now - self._last_rep_ts >= 1.0:
                self._reps += 1
                self._last_rep_ts = now
            exercise_name = self._active_exercise_label
            phrase = "Modalità demo: rilevamento disattivato."
        else:
            exercise_name = "Seleziona un esercizio"
            phrase = "Modalità demo: seleziona un esercizio per vedere l'UI in azione."

        reps = self._reps
        keypoints = []  # nessun keypoint in demo mode

        if callback:
            callback(frame_w=frame, exercise=exercise_name, rep=reps, trainer_phrase=phrase, keypoints=keypoints)
            return None
        return exercise_name, reps, phrase, keypoints