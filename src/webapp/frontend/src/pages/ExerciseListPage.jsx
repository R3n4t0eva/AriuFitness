import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './ExerciseListPage.css'; // Creeremo questo file per lo stile
import { useNavigate } from 'react-router-dom';
import '../Dashboard.css'; // Per importare lo stile del bottone logout

//in seguito verrà probabilmente cambiato con una chiamata a database o API
const dailyExercises = [
  "Medicine Ball Goblet Squat", "Affondi con palla medica", "Medicine Ball Burpees (con push-up sulla spalla)",
   "Russian Twist", "Medicine Ball Sit-Up Throw", "Medicine Ball Chest Press Sit-Up", "Medicine Ball Halos", 
   "Russian Twist (versione con piedi a terra)", "Wall Sit with Medicine Ball Rotation", "Long-Lever Russian Twist", 
   "Medicine Ball Burpee", "Medicine Ball Thrusters", "Medicine Ball Sit-Up", "Pelvic Tilts", 
   "Kneeling Stability Stretch", "Side Lean with Leg Support", "Arm Raises on Fitball", 
   "Fitball Lateral Shifts", "Hamstring Curls on Fitball", "Fitball V-Pass", "Fitball Back Extensions", 
   "Fitball Lat Stretch", "Fitball Glute Bridge", "Fitball Overhead Roll-Ups", "Stability Ball Active Sitting", 
   "Overhead Ball Side Bends", "Stability Ball Crunches", "Fitball Elevated Leg Crunches"
];

//in seguito verrà probabilmente cambiato con una chiamata a database o API
const exerciseVideoMap = {
    "Medicine Ball Goblet Squat": "Medicine Ball Goblet Squat",
    "Affondi con palla medica": "Affondi con palla medica",
    "Medicine Ball Burpees (con push-up sulla spalla)": "Medicine Ball Burpees (con push-up sulla spalla) ",
    "Russian Twist": "Russian Twist",
    "Medicine Ball Sit-Up Throw": "Medicine Ball sit-up throw",
    "Medicine Ball Chest Press Sit-Up": "Medicine Ball Chest Press Sit-Up",
    "Medicine Ball Halos": "Medicine Ball Halos",
    "Russian Twist (versione con piedi a terra)": "Russian Twist con piedi a terra",
    "Wall Sit with Medicine Ball Rotation": "Wall Sit with Medicine Ball Rotation",
    "Long-Lever Russian Twist": "Long-Lever Russian Twist",
    "Medicine Ball Burpee": "Medicine Ball Burpee",
    "Medicine Ball Thrusters": "Medicine Ball Thrusters",
    "Medicine Ball Sit-Up": "Medicine Ball Sit-Up",
    "Pelvic Tilts": "Pelvic Tilts",
    "Kneeling Stability Stretch": "Kneeling Stability Stretch",
    "Side Lean with Leg Support": "Side Lean with Leg Support",
    "Arm Raises on Fitball": "Arm Raises on Fitball",
    "Fitball Lateral Shifts": "Fitball Lateral Shifts",
    "Hamstring Curls on Fitball": "Hamstring Curls on Fitball",
    "Fitball V-Pass": "Fitball V-Pass",
    "Fitball Back Extensions": "Fitball Back Extensions",
    "Fitball Lat Stretch": "Fitball Lat Stretch",
    "Fitball Glute Bridge": "Fitball Glute Bridge",
    "Fitball Overhead Roll-Ups": "Fitball Overhead Roll-Ups",
    "Stability Ball Active Sitting": "Stability Ball Active Sitting",
    "Overhead Ball Side Bends": "Overhead Ball Side Bends",
    "Stability Ball Crunches": "Stability Ball Crunches",
    "Fitball Elevated Leg Crunches": "Fitball Elevated Leg Crunches"
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