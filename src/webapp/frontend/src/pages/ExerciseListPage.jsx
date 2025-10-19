import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './ExerciseListPage.css'; // Creeremo questo file per lo stile
import { useNavigate } from 'react-router-dom';
import '../Dashboard.css'; // Per importare lo stile del bottone logout

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

function ExerciseListPage() {
  const [selectedExercise, setSelectedExercise] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
  const navigate = useNavigate(); // Aggiungi questo hook
  const [selectedVideo, setSelectedVideo] = useState(null);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/'); // Reindirizza alla pagina di scelta (che poi reindirizzerà al login)
  };

  const handleSelectExercise = (exerciseName) => {
    setSelectedExercise(exerciseName);
    const videoFileSlug = exerciseVideoMap[exerciseName]; // Usa la mappa
    if (videoFileSlug) {
      setVideoUrl(`/videos/${videoFileSlug}.mp4`);
    } else {
      console.error(`Nome file video non trovato per l'esercizio: ${exerciseName}`);
      setVideoUrl(''); // Pulisce l'URL se non trova corrispondenza
    }
  };

  return (
    <div className="page-container">
      <div className="glass-card page-card">
        <header className="page-header">
          <h1>Galleria Esercizi</h1>
          
        </header>
        <div className="content-layout">
          <div className="exercise-menu">
            <ul className="exercise-list">
              {dailyExercises.map((item, index) => (
                <button 
                  key={index} 
                  className={selectedExercise === item ? 'exercise-item active-exercise' : 'exercise-item'}
                  onClick={() => handleSelectExercise(item)}
                >
                  {item}
                </button>
              ))}
            </ul>
          </div>
          
          <div className="video-player-panel">
            {/* --- CONDIZIONE CORRETTA: usa videoUrl --- */}
            {videoUrl ? (
              <div className="video-container">
                <video key={videoUrl} controls autoPlay loop muted>
                  <source src={videoUrl} type="video/mp4" />
                  Il tuo browser non supporta i video.
                </video>
                
              </div>
            ) : (
              <div className="video-placeholder">
                <p>Seleziona un esercizio dalla lista per vedere il tutorial.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ExerciseListPage;