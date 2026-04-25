import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import '../Dashboard.css';

const DEFAULT_TARGET_REPS = 10;

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
  
  // 2. STATO PER TRACCIARE GLI ESERCIZI COMPLETATI
  const [completedExercises, setCompletedExercises] = useState([]);
  const [exerciseStartTime, setExerciseStartTime] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

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
      console.log("Esercizi ricevuti da navigazione:", fromNav);
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
    
    // Registra i dati dell'esercizio completato
    recordExerciseCompletion(feedback);
    
    setIsFeedbackModalVisible(false);

    if (feedback === 'difficile') {
      setPendingAdvanceAfterDifficult(true);
      setIsContinueAfterDifficultModalVisible(true);
      return;
    }

    advanceAfterExerciseFeedback();
  };

  // --- FUNZIONE PER REGISTRARE IL COMPLETAMENTO DI UN ESERCIZIO ---
  const recordExerciseCompletion = (userFeedback) => {
    if (currentExerciseIndex >= selectedExercises.length) return;
    
    const currentExercise = selectedExercises[currentExerciseIndex];
    const timeTaken = exerciseStartTime ? (Date.now() - exerciseStartTime) / 1000 : 0;
    const avgTime = reps > 0 ? timeTaken / reps : 0;
    
    // Usa l'intero oggetto esercizio più i dati di performance
    const exerciseData = {
      ...currentExercise,
    };
    
    setCompletedExercises([...completedExercises, exerciseData]);
    console.log(`Esercizio registrato:`, exerciseData);
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

  const handleFinishWorkout = async (feedback) => {
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
  }, [isWebcamActive]);
  

  useEffect(() => {
    // Se il countdown non è attivo, non fare nulla
    if (countdown === null) return;
  
    // Se il countdown arriva a 0, avvia l'esercizio
    if (countdown === 0) {
      setCountdown(null); // Nasconde il countdown
      setIsCountingActive(true); // Attiva il conteggio delle ripetizioni
      setExerciseStartTime(Date.now()); // Registra l'inizio dell'esercizio

      return;
    }
  
    // Se il countdown è > 0, imposta un timer per scalarlo di 1 dopo un secondo
    const timer = setTimeout(() => {
      setCountdown(countdown - 1);
    }, 1000);
  
    // Pulisce il timer se il componente viene smontato
    return () => clearTimeout(timer);
  }, [countdown, selectedExercise]); // Dipende anche dall'esercizio selezionato

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
    const nextExercise = selectedExercises[nextIndex];
    handleExerciseSelect(nextExercise);
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

  const handleExerciseSelect = (exercise) => {
    // exercise è ora l'oggetto completo dell'esercizio
    if (exercise && exercise.id && exercise.nome) {
      setSelectedExercise(exercise);
      // Carica il video tutorial dall'oggetto esercizio
      if (exercise.video_tut_url) {
        setSelectedTutorial(exercise.video_tut_url);
      }
      resetExerciseRuntimeState();
    }
  };

  const handleStartExercise = () => {
    if (!selectedExercise || !isWebcamActive) {
      return;
    }
    setIsStartLocked(true);
    setCountdown(5);
  };

  // --- JSX RENDER ---
  // In ClassificationPage.jsx

  return (
    <div className="dashboard-container">
      {/* Sezione superiore fissa */}
      <div className="main-view-grid">
        {/* Pannello Webcam */}
        <div className="video-panel glass-card" style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'flex-start',
            position: 'relative',
            minHeight: '300px',
          }}>

          {/* Contenitore della webcam (parte grande) */}
          <div style={{ flex: 1, width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden', borderRadius: '12px 12px 0 0' }}>
  
            {/* Overlay info Esercizio: Sopra al centro */}
            {selectedExercise && (
              <div style={{
                position: 'absolute',
                top: '15px',
                left: '50%',
                transform: 'translateX(-50%)',
                zIndex: 10,
                textAlign: 'center',
                background: 'rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(8px)',
                padding: '8px 20px',
                borderRadius: '20px',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                width: 'fit-content',
                whiteSpace: 'nowrap'
              }}>
                <div style={{ fontWeight: 800, fontSize: '1.1rem', color: '#1a1a1a', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {selectedExercise.nome}
                </div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, opacity: 0.8, color: '#333' }}>
                  Target: {currentTargetReps} ripetizioni
                </div>
              </div>
            )}

            {/* Video della webcam */}
            <div className={`video-container ${!isWebcamActive ? 'hidden' : ''}`}>
              <video ref={videoRef} autoPlay playsInline muted className="webcam-feed" />
              <canvas ref={overlayCanvasRef} className="overlay-canvas" />
              <canvas ref={canvasRef} style={{ display: 'none' }} />
            </div>

            {/* Placeholder quando webcam è spenta */}
            {!isWebcamActive && (
              <div className="webcam-placeholder">
                <p>{webcamWarningMessage || 'La tua webcam è disattivata.'}</p>
              </div>
            )}
          </div>

          {/* Contenitore pulsanti (parte piccola) */}
          <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: 10, borderTop: '1px solid rgba(0,0,0,0.1)' }}>
            {/* Riga 1: Pulsante Attiva/Disattiva Webcam */}
            {isWebcamActive && (
              <button onClick={handleWebcamToggle} className="webcam-toggle-button inside-video">Disattiva Webcam</button>
            )}
            {!isWebcamActive && (
              <button onClick={handleWebcamToggle} className="webcam-toggle-button">Attiva Webcam</button>
            )}

            {/* Riga 2: Pulsante Inizia */}
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
            ) : null}

            {isCompletedVisible && (
              <div style={{ fontWeight: 900, color: '#2a9d8f', textAlign: 'center' }}>
                Complimenti!
              </div>
            )}
            {!isWebcamActive && webcamWarningMessage && (
              <div style={{ fontWeight: 800, color: '#e76f51', textAlign: 'center' }}>
                {webcamWarningMessage}
              </div>
            )}
          </div>
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
          <h3>FEEDBACK DEL COACH</h3>
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
              key={item.id}
              className={selectedExercise?.id === item.id ? 'exercise-item active-exercise' : 'exercise-item'}
              onClick={() => handleExerciseSelect(item)}
              disabled={index !== currentExerciseIndex || countdown !== null || isCountingActive}
            >
              {item.nome}
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