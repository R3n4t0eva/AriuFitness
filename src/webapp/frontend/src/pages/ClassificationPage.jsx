import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import '../Dashboard.css';

const dailyExercises = [
  "Estensioni delle Braccia", "Estensioni delle Braccia sulla Testa", "Alzate Laterali", 
  "Squat da Seduto", "Alzata Gambe Laterale", "Addominali da Seduto"
];

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
  
  // 1. STATO MANCANTE AGGIUNTO
  const [isConnected, setIsConnected] = useState(false); 

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const ws = useRef(null);
  const navigate = useNavigate();
  const clientId = useRef(Date.now().toString());

  const handleFeedbackSubmit = (feedback) => {
    console.log(`Feedback esercizio: ${feedback}`);
    
    // 1. Prima di tutto, chiude il pop-up
    setIsFeedbackModalVisible(false);
  
    // 2. Calcola l'indice dell'esercizio successivo
    const nextIndex = currentExerciseIndex + 1;
  
    // 3. Controlla se ci sono ancora esercizi e, in caso affermativo, avanza
    if (nextIndex < dailyExercises.length) {
      setCurrentExerciseIndex(nextIndex); // <-- Questa è la riga che sblocca l'esercizio successivo
      
      // 4. Resetta lo stato per il nuovo esercizio
      setSelectedExercise(null);
      setReps(0);
      setKeypoints([]);
      setPhrase("Seleziona il prossimo esercizio per continuare.");
    }
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
      setReps(data.repetitions);
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
  }, [countdown]); // Questo hook dipende dal valore di countdown

  // --- FUNZIONI DI CONTROLLO ESERCIZIO E LOGOUT ---
  const handleLogout = () => {
    stopWebcam();
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleExerciseSelect = (exerciseName) => {
    if (!isWebcamActive) {
      alert("Per favore, attiva la webcam prima di iniziare un esercizio.");
      return;
    }
  
    console.log(`Esercizio selezionato: ${exerciseName}, avvio countdown...`);
    setSelectedExercise(exerciseName);
    setReps(0);
    setIsCountingActive(false);
    setCountdown(5);

    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
          type: 'reset_reps'
      }));
    }
  
    const videoFileSlug = exerciseVideoMap[exerciseName]; // Usa la mappa
    if (videoFileSlug) {
      const videoFileName = videoFileSlug + '.mp4';
      setSelectedTutorial(`/videos/${videoFileName}`);
    } else {
      console.error(`Nome file video non trovato per l'esercizio: ${exerciseName}`);
      setSelectedTutorial(null); // Nasconde il video se non c'è corrispondenza
    }
  
  };

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
              <p>La tua webcam è disattivata.</p>
              <button onClick={handleWebcamToggle} className="webcam-toggle-button">Attiva Webcam</button>
            </div>
          )}
          {isWebcamActive && (
            <button onClick={handleWebcamToggle} className="webcam-toggle-button inside-video">Disattiva Webcam</button>
          )}
        </div>

        {/* PANNELLO TUTORIAL CON VISIBILITÀ CONDIZIONALE */}
        <div id="tutorial-panel" className={`video-panel glass-card ${!selectedTutorial ? 'panel-hidden' : ''}`}>
          <div className="video-container">
            {selectedTutorial ? (
              <video key={selectedTutorial} controls autoPlay loop muted>
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
            <h3>RIPETIZIONI</h3>
            <button onClick={handleResetReps} className="reset-button">Azzera</button>
          </div>
          <p className="big-text">{reps}</p>
        </div>
        
        {/* Pannello Feedback */}
        <div id="feedback-panel" className="info-card glass-card trainer-feedback">
          <h3>FEEDBACK DEL TERAPISTA</h3>
          <p>{phrase}</p>
        </div>
      </div>

      {/* Sezione inferiore scorrevole */}
      <div id="workout-list-panel" className="info-card glass-card workout-list-card">
        <h3>ALLENAMENTO GIORNALIERO</h3>
        <ul className="exercise-list">
          {dailyExercises.map((item, index) => (
            <button
              key={index}
              className={selectedExercise === item ? 'exercise-item active-exercise' : 'exercise-item'}
              onClick={() => handleExerciseSelect(item)}
              disabled={index !== currentExerciseIndex}
            >
              {item}
            </button>
          ))}
        </ul>
        {selectedExercise && (
          <div className="action-buttons-container">
            {currentExerciseIndex < dailyExercises.length - 1 && (
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