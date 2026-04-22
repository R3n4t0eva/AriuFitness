import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import '../Dashboard.css';

const DEFAULT_TARGET_REPS = 10;

const exerciseVideoMap = {
  "Estensioni delle Braccia": "arms_extension",
  "Estensioni delle Braccia sulla Testa": "arms_up",
  "Alzate Laterali": "arms_lateral",
  "Squat da Seduto": "chair_raises",
  "Alzata Gambe Laterale": "leg_lateral",
  "Addominali da Seduto": "seated_crunch"
};

const exerciseApiMap = {
  "Estensioni delle Braccia": "arms_extension",
  "Estensioni delle Braccia sulla Testa": "arms_up",
  "Alzate Laterali": "arms_lateral",
  "Squat da Seduto": "chair_raises",
  "Alzata Gambe Laterale": "leg_lateral",
  "Addominali da Seduto": "seated_crunch"
};

function ClassificationPage() {
  // --- STATI E REF ---
  const [reps, setReps] = useState(0);
  const [phrase, setPhrase] = useState('Seleziona un esercizio e attiva la webcam per iniziare.');
  const [selectedExercise, setSelectedExercise] = useState(null);
  const [selectedExercises, setSelectedExercises] = useState([]);
  const [keypoints, setKeypoints] = useState([]);
  const [isWebcamActive, setIsWebcamActive] = useState(false);
  const [stream, setStream] = useState(null);
  const [selectedTutorial, setSelectedTutorial] = useState(null);
  const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
  const [isFeedbackModalVisible, setIsFeedbackModalVisible] = useState(false);  
  const [isWorkoutFeedbackModalVisible, setIsWorkoutFeedbackModalVisible] = useState(false);
  const [workoutComment, setWorkoutComment] = useState("");
  const [countdown, setCountdown] = useState(null); // Gestisce il numero del countdown (5, 4, 3...)
  const [isCountingActive, setIsCountingActive] = useState(false); // true solo dopo il countdown
  const [isCompletedVisible, setIsCompletedVisible] = useState(false);
  const [isStartLocked, setIsStartLocked] = useState(false);
  const [webcamWarningMessage, setWebcamWarningMessage] = useState("");
  const [isContinueAfterDifficultModalVisible, setIsContinueAfterDifficultModalVisible] = useState(false);
  const [pendingAdvanceAfterDifficult, setPendingAdvanceAfterDifficult] = useState(false);
  
  // 1. STATO MANCANTE AGGIUNTO
  const [isConnected, setIsConnected] = useState(false); 

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const tutorialVideoRef = useRef(null);
  const ws = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const clientId = useRef(Date.now().toString());
  const isCountingActiveRef = useRef(false);

  useEffect(() => {
    isCountingActiveRef.current = isCountingActive;
  }, [isCountingActive]);

  const pauseTutorialVideo = () => {
    if (!tutorialVideoRef.current) return;
    try {
      tutorialVideoRef.current.pause();
    } catch (e) {
      // ignore
    }
  };

  const resetExerciseRuntimeState = () => {
    setCountdown(null);
    setIsCountingActive(false);
    setIsStartLocked(false);
    setIsCompletedVisible(false);
  };

  useEffect(() => {
    const fromNav = location?.state?.selectedExercises;
    if (Array.isArray(fromNav) && fromNav.length > 0) {
      setSelectedExercises(fromNav);
      setCurrentExerciseIndex(0);
      setSelectedExercise(null);
      return;
    }

    try {
      const raw = localStorage.getItem('selectedExercises');
      const parsed = raw ? JSON.parse(raw) : [];
      if (Array.isArray(parsed)) {
        setSelectedExercises(parsed);
        setCurrentExerciseIndex(0);
        setSelectedExercise(null);
      }
    } catch (e) {
      console.warn('selectedExercises non valido in localStorage', e);
      setSelectedExercises([]);
    }
  }, [location?.state]);

  const advanceAfterExerciseFeedback = () => {
    const nextIndex = currentExerciseIndex + 1;

    if (nextIndex < selectedExercises.length) {
      setCurrentExerciseIndex(nextIndex);
      setSelectedExercise(null);
      setReps(0);
      setKeypoints([]);
      setPhrase("Seleziona il prossimo esercizio per continuare.");
      resetExerciseRuntimeState();
      return;
    }

    // Se era l'ultimo esercizio, consideriamo la sessione finita
    setCurrentExerciseIndex(selectedExercises.length);
    setSelectedExercise(null);
    setSelectedTutorial(null);
    resetExerciseRuntimeState();
    setPhrase('Hai Finito!');
  };

  const handleFeedbackSubmit = (feedback) => {
    console.log(`Feedback esercizio: ${feedback}`);
    setIsFeedbackModalVisible(false);

    if (feedback === 'difficile') {
      setPendingAdvanceAfterDifficult(true);
      setIsContinueAfterDifficultModalVisible(true);
      return;
    }

    advanceAfterExerciseFeedback();
  };

  const handleContinueAfterDifficultYes = () => {
    setIsContinueAfterDifficultModalVisible(false);
    if (pendingAdvanceAfterDifficult) {
      setPendingAdvanceAfterDifficult(false);
      advanceAfterExerciseFeedback();
    }
  };

  const handleContinueAfterDifficultNo = () => {
    setIsContinueAfterDifficultModalVisible(false);
    setPendingAdvanceAfterDifficult(false);
    stopWebcam();
    navigate('/');
  };

  const handleFinishWorkout = (feedback) => {
    // Se il feedback è un commento e non una faccina, usa il testo del commento
    const finalFeedback = feedback === 'comment' ? workoutComment : feedback;
    console.log(`Feedback finale allenamento: ${finalFeedback}`);
    
    // Chiudi il pop-up
    setIsWorkoutFeedbackModalVisible(false);
    
    // Spegni la webcam e altre pulizie se necessario
    stopWebcam();
    
    // Reindirizza l'utente alla pagina principale
    navigate('/');
  };
  
  // --- HOOK PER LA CONNESSIONE WEBSOCKET ---
  useEffect(() => {
    ws.current = new WebSocket(`ws://127.0.0.1:8000/ws/classify/${clientId.current}`);
    ws.current.onopen = () => {
      console.log("WebSocket connected!");
      setIsConnected(true);
    };
    ws.current.onclose = () => {
      console.log("WebSocket disconnected!");
      setIsConnected(false);
    };
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (isCountingActiveRef.current) {
        setReps(data.repetitions);
      }
      setPhrase(data.phrase);
      if (data.keypoints) {
        setKeypoints(data.keypoints);
      }
    };

    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  // --- FUNZIONI DI CONTROLLO WEBCAM ---
  const startWebcam = async () => {
    console.log("Tento di avviare la webcam. videoRef.current è:", videoRef.current);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      setStream(stream);
      if (videoRef.current) {
        console.log("videoRef trovato, imposto lo srcObject...");
        videoRef.current.srcObject = stream;
      } else {
        console.error("ERRORE: videoRef.current è nullo! Impossibile mostrare il video.");
      }
      setIsWebcamActive(true);
    } catch (err) {
      console.error("Errore nell'accesso alla webcam:", err);
      setPhrase("Accesso alla webcam negato. Controlla i permessi del browser.");
    }
  };  

  const stopWebcam = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    setIsWebcamActive(false);
    setStream(null);
    setKeypoints([]);
  };

  const handleWebcamToggle = () => {
    if (isWebcamActive) {
      stopWebcam();
    } else {
      startWebcam();
    }
  };

  useEffect(() => {
    // Se la webcam viene spenta durante l'esercizio, fermiamo tutorial e mettiamo in pausa la sessione.
    if (isWebcamActive) {
      setWebcamWarningMessage("");
      return;
    }

    const wasInExercise = isStartLocked || countdown !== null || isCountingActive;
    if (!wasInExercise) return;

    pauseTutorialVideo();
    resetExerciseRuntimeState();
    const msg = 'Attenzione! Non riusciamo a rilevare la videocamera!';
    setWebcamWarningMessage(msg);
    setPhrase(msg);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isWebcamActive]);
  
  // --- 2. HOOK PER L'INVIO DEI FRAME (UNICO E CORRETTO) ---
   // --- 2. HOOK PER L'INVIO DEI FRAME (UNICO E CORRETTO) ---
   useEffect(() => {
    // Non fare nulla se la webcam non è attiva o il websocket non è connesso
    if (!isWebcamActive || !isConnected) return;

    const sendFrame = () => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        const canvas = canvasRef.current;
        const video = videoRef.current;
        if (canvas && video && video.videoWidth > 0) {
          const context = canvas.getContext('2d');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          context.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
          const data = canvas.toDataURL('image/jpeg', 0.8);
          console.log("Sto inviando un frame al backend...");
          ws.current.send(data);
        }
      }
    };

    const intervalId = setInterval(sendFrame, 100);
    return () => clearInterval(intervalId);
  }, [isWebcamActive, isConnected]); // Si attiva solo se webcam e connessione sono attive

  // --- HOOK PER DISEGNARE I KEYPOINT ---
  useEffect(() => {
    const video = videoRef.current;
    const canvas = overlayCanvasRef.current;
    
    if (!video || !canvas || keypoints.length === 0 || video.videoWidth === 0) {
      return;
    }

    const { videoWidth, videoHeight, clientWidth, clientHeight } = video;

    canvas.width = clientWidth;
    canvas.height = clientHeight;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scale = Math.min(clientWidth / videoWidth, clientHeight / videoHeight);
    const renderedWidth = videoWidth * scale;
    const renderedHeight = videoHeight * scale;
    const offsetX = (clientWidth - renderedWidth) / 2;
    const offsetY = (clientHeight - renderedHeight) / 2;

    ctx.fillStyle = '#2a9d8f';
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 2;

    keypoints.forEach(point => {
      if (point.x > 0 && point.y > 0) {
        // --- NESSUNA LOGICA DI SPECCHIO QUI ---
        // Calcoliamo semplicemente la posizione diretta
        const finalX = (point.x * renderedWidth) + offsetX;
        const finalY = (point.y * renderedHeight) + offsetY;
        
        ctx.beginPath();
        ctx.arc(finalX, finalY, 5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
      }
    });
  }, [keypoints]);

  useEffect(() => {
    // Se il countdown non è attivo, non fare nulla
    if (countdown === null) return;
  
    // Se il countdown arriva a 0, avvia l'esercizio
    if (countdown === 0) {
      setCountdown(null); // Nasconde il countdown
      setIsCountingActive(true); // Attiva il conteggio delle ripetizioni
      
      // Invia il comando al backend per iniziare a contare
      if (ws.current?.readyState === WebSocket.OPEN && selectedExercise) {
        ws.current.send(JSON.stringify({
          type: 'start_exercise',
          exercise_name: selectedExercise
        }));
      }
      return;
    }
  
    // Se il countdown è > 0, imposta un timer per scalarlo di 1 dopo un secondo
    const timer = setTimeout(() => {
      setCountdown(countdown - 1);
    }, 1000);
  
    // Pulisce il timer se il componente viene smontato
    return () => clearTimeout(timer);
  }, [countdown, selectedExercise]); // Dipende anche dall'esercizio selezionato

  // --- FUNZIONI DI CONTROLLO ESERCIZIO E LOGOUT ---
  const handleLogout = () => {
    stopWebcam();
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleExerciseSelect = (exerciseName) => {
    setSelectedExercise(exerciseName);
    setReps(0);
    setIsCountingActive(false);
    setCountdown(null);
    setIsCompletedVisible(false);
    setIsStartLocked(false);

    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'reset_reps' }));
    }

    const videoFileSlug = exerciseVideoMap[exerciseName] ?? exerciseName;
    if (videoFileSlug) setSelectedTutorial(`/videos/${videoFileSlug}.mp4`);
    else setSelectedTutorial(null);
  };

  const handleStartExercise = () => {
    if (!isWebcamActive || !selectedExercise) return;
    if (isStartLocked) return;
    setIsStartLocked(true);
    setReps(0);
    setIsCountingActive(false);
    setIsCompletedVisible(false);
    setCountdown(5);

    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'reset_reps' }));
    }
  };

  const advanceToNextExercise = () => {
    const nextIndex = currentExerciseIndex + 1;
    if (nextIndex >= selectedExercises.length) {
      setCurrentExerciseIndex(selectedExercises.length);
      setSelectedExercise(null);
      setSelectedTutorial(null);
      setIsCountingActive(false);
      setCountdown(null);
      setIsStartLocked(false);
      setPhrase('Hai Finito!');
      return;
    }

    setCurrentExerciseIndex(nextIndex);
    const nextExerciseName = selectedExercises[nextIndex];
    handleExerciseSelect(nextExerciseName);
    setPhrase('Pronto per il prossimo esercizio. Premi Inizia quando vuoi partire.');
  };

  const currentTargetReps = DEFAULT_TARGET_REPS;
  const remainingReps = Math.max(currentTargetReps - reps, 0);

  useEffect(() => {
    if (!isCountingActive) return;
    if (!selectedExercise) return;
    if (reps < currentTargetReps) return;

    setIsCompletedVisible(true);
    setIsCountingActive(false);
    setCountdown(null);

    if (tutorialVideoRef.current) {
      try {
        tutorialVideoRef.current.pause();
      } catch (e) {
        // ignore
      }
    }

    const t = setTimeout(() => {
      setIsCompletedVisible(false);
      advanceToNextExercise();
    }, 1000);

    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reps, isCountingActive, selectedExercise]);

  // In ClassificationPage.jsx

  const handleResetReps = () => {
    console.log("Azzero le ripetizioni...");
    setReps(0); // Azzera subito le ripetizioni nell'interfaccia
    
    // Invia il comando al backend
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'reset_reps'
      }));
    }
  };

  const handleManualAddReps = (delta) => {
    setReps((prev) => prev + delta);
  };
  // --- JSX RENDER ---
  // In ClassificationPage.jsx

  return (
    <div className="dashboard-container">
      {/* Sezione superiore fissa */}
      <div className="main-view-grid">
        {/* Pannello Webcam */}
        <div className="video-panel glass-card">
  
          {/* Questo div aggiunge la classe 'hidden' solo se isWebcamActive è false */}
          <div className={`video-container ${!isWebcamActive ? 'hidden' : ''}`}>
            <video ref={videoRef} autoPlay playsInline muted className="webcam-feed" />
            <canvas ref={overlayCanvasRef} className="overlay-canvas" />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
          </div>

          {/* Il placeholder viene mostrato solo se isWebcamActive è false */}
          {!isWebcamActive && (
            <div className="webcam-placeholder">
              <img src="/videocamera.png" alt="Attiva webcam" className="webcam-icon-img" />
              <p>{webcamWarningMessage || 'La tua webcam è disattivata.'}</p>
              <button onClick={handleWebcamToggle} className="webcam-toggle-button">Attiva Webcam</button>
            </div>
          )}
          {isWebcamActive && (
            <button onClick={handleWebcamToggle} className="webcam-toggle-button inside-video">Disattiva Webcam</button>
          )}

          {/* Avvio esercizio: nello stesso box della webcam */}
          <div style={{ marginTop: 12, display: 'flex', gap: 10, alignItems: 'center', justifyContent: 'space-between' }}>
            {!isStartLocked && countdown === null && !isCountingActive ? (
              <button
                type="button"
                onClick={handleStartExercise}
                disabled={!isWebcamActive || !selectedExercise}
                className="webcam-toggle-button"
                style={{
                  opacity: !isWebcamActive || !selectedExercise ? 0.6 : 1,
                  cursor: !isWebcamActive || !selectedExercise ? 'not-allowed' : 'pointer',
                }}
              >
                Inizia
              </button>
            ) : (
              <div />
            )}
            <div style={{ opacity: 0.85, textAlign: 'right' }}>
              {selectedExercise ? (
                <>
                  <div style={{ fontWeight: 700 }}>{selectedExercise}</div>
                  <div style={{ fontSize: 12 }}>
                    Target: {currentTargetReps} ripetizioni
                  </div>
                </>
              ) : (
                <div style={{ fontSize: 12 }}>Seleziona un esercizio per partire</div>
              )}
            </div>
          </div>

          {isCompletedVisible && (
            <div style={{ marginTop: 10, fontWeight: 900, color: '#2a9d8f', textAlign: 'center' }}>
              Complimenti!
            </div>
          )}
          {!isWebcamActive && webcamWarningMessage && (
            <div style={{ marginTop: 10, fontWeight: 800, color: '#e76f51', textAlign: 'center' }}>
              {webcamWarningMessage}
            </div>
          )}
        </div>

        {/* PANNELLO TUTORIAL CON VISIBILITÀ CONDIZIONALE */}
        <div id="tutorial-panel" className={`video-panel glass-card ${!selectedTutorial ? 'panel-hidden' : ''}`}>
          <div className="video-container">
            {selectedTutorial ? (
              <video ref={tutorialVideoRef} key={selectedTutorial} controls autoPlay loop muted>
                <source src={selectedTutorial} type="video/mp4" />
              </video>
            ) : (
              <div className="video-placeholder">
                <p>Seleziona un esercizio per vedere il video tutorial</p>
              </div>
            )}
          </div>
        </div>

        {/* Pannello Ripetizioni */}
        <div id="reps-panel" className="info-card glass-card">
          <div className="info-card-header">
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
              <h3 style={{ margin: 0 }}>RIPETIZIONI</h3>
              {selectedExercise && (isStartLocked || countdown !== null || isCountingActive) ? (
                <span style={{ opacity: 0.85, fontWeight: 700, fontSize: 12 }}>
                  Ancora {remainingReps}
                </span>
              ) : null}
            </div>
            <button onClick={handleResetReps} className="reset-button">Azzera</button>
          </div>
          <p className="big-text">{reps}</p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 8, flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => handleManualAddReps(1)}
              disabled={!selectedExercise || countdown !== null || !isCountingActive}
              className="reset-button"
              style={{ cursor: !selectedExercise || !isCountingActive ? 'not-allowed' : 'pointer', opacity: !selectedExercise || !isCountingActive ? 0.6 : 1 }}
            >
              +1
            </button>
            <button
              type="button"
              onClick={() => handleManualAddReps(5)}
              disabled={!selectedExercise || countdown !== null || !isCountingActive}
              className="reset-button"
              style={{ cursor: !selectedExercise || !isCountingActive ? 'not-allowed' : 'pointer', opacity: !selectedExercise || !isCountingActive ? 0.6 : 1 }}
            >
              +5
            </button>
          </div>
        </div>
        
        {/* Pannello Feedback */}
        <div id="feedback-panel" className="info-card glass-card trainer-feedback">
          <h3>FEEDBACK DEL TERAPISTA</h3>
          <p>{phrase}</p>
        </div>
      </div>

      {/* Sezione inferiore scorrevole */}
      <div id="workout-list-panel" className="info-card glass-card workout-list-card">
        <h3>ESERCIZI SELEZIONATI</h3>
        {selectedExercises.length === 0 ? (
          <p style={{ marginTop: 8, opacity: 0.85 }}>
            Non hai selezionato esercizi. Vai in <Link to="/visualizza-esercizi">Galleria Esercizi</Link> e aggiungili.
          </p>
        ) : null}
        <ul className="exercise-list">
          {selectedExercises.map((item, index) => (
            <button
              key={index}
              className={selectedExercise === item ? 'exercise-item active-exercise' : 'exercise-item'}
              onClick={() => handleExerciseSelect(item)}
              disabled={index !== currentExerciseIndex || countdown !== null || isCountingActive}
            >
              {item}
            </button>
          ))}
        </ul>
        {isCompletedVisible && (
          <div style={{ marginTop: 10, fontWeight: 800, color: '#2a9d8f' }}>
            Completato!
          </div>
        )}
        {selectedExercises.length > 0 && currentExerciseIndex >= selectedExercises.length && (
          <div style={{ marginTop: 10, fontWeight: 800 }}>
            Hai Finito!
          </div>
        )}
        {selectedExercise && (
          <div className="action-buttons-container">
            {currentExerciseIndex < selectedExercises.length - 1 && (
              <button className="finish-exercise-button" onClick={() => setIsFeedbackModalVisible(true)}>
                Prossimo Esercizio
              </button>
            )}
            <button className="finish-workout-button" onClick={() => setIsWorkoutFeedbackModalVisible(true)}>
              Termina Allenamento
            </button>
          </div>
        )}
      </div>
      
      

      {isFeedbackModalVisible && (
        <div className="modal-overlay">
          <div className="glass-card modal-content">
            <h3>Come ti sei sentito durante l'esercizio?</h3>
            <div className="feedback-faces">
              <span onClick={() => handleFeedbackSubmit('difficile')}>😞</span>
              <span onClick={() => handleFeedbackSubmit('medio')}>😐</span>
              <span onClick={() => handleFeedbackSubmit('facile')}>😊</span>
            </div>
          </div>
        </div>
      )}

      {isWorkoutFeedbackModalVisible && (
        <div className="modal-overlay">
          <div className="glass-card modal-content">
            <h2>FINE ALLENAMENTO!</h2>
            <h3>Come è stato l'allenamento?</h3>
            <div className="feedback-faces">
              <span onClick={() => handleFinishWorkout('difficile')}>😞</span>
              <span onClick={() => handleFinishWorkout('medio')}>😐</span>
              <span onClick={() => handleFinishWorkout('facile')}>😊</span>
            </div>
            <p className="feedback-separator">oppure lascia un commento</p>
            <textarea 
              className="feedback-comment"
              placeholder="Scrivi qui il tuo commento..."
              value={workoutComment}
              onChange={(e) => setWorkoutComment(e.target.value)}
            ></textarea>
            <button 
              className="form-button"
              onClick={() => handleFinishWorkout('comment')}
            >
              Invia Commento
            </button>
          </div>
        </div>
      )}

      {isContinueAfterDifficultModalVisible && (
        <div className="modal-overlay">
          <div className="glass-card modal-content">
            <h3>Sei sicuro di riuscire a continuare?</h3>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 14, flexWrap: 'wrap' }}>
              <button className="form-button" onClick={handleContinueAfterDifficultYes}>
                Si, posso continuare
              </button>
              <button className="finish-workout-button" onClick={handleContinueAfterDifficultNo}>
                No, voglio fermarmi
              </button>
            </div>
          </div>
        </div>
      )}

      {countdown !== null && (
        <div className="countdown-overlay">
          <p className="countdown-text">Il tuo esercizio inizia tra</p>
          <div className="countdown-number">{countdown > 0 ? countdown : 'VIA!'}</div>
        </div>
      )}
    </div>
  );
}

export default ClassificationPage;