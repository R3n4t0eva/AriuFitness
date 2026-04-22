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

// Categorie richieste: gambe e glutei, core e addominali, stretching e mobilità, full body ed esplosività
const exerciseCategoryMap = {
  // gambe e glutei
  "Medicine Ball Goblet Squat": "gambe e glutei",
  "Affondi con palla medica": "gambe e glutei",
  "Wall Sit with Medicine Ball Rotation": "gambe e glutei",
  "Hamstring Curls on Fitball": "gambe e glutei",
  "Fitball Glute Bridge": "gambe e glutei",
  "Fitball Lateral Shifts": "gambe e glutei",

  // core e addominali
  "Russian Twist": "core e addominali",
  "Russian Twist (versione con piedi a terra)": "core e addominali",
  "Long-Lever Russian Twist": "core e addominali",
  "Medicine Ball Sit-Up Throw": "core e addominali",
  "Medicine Ball Chest Press Sit-Up": "core e addominali",
  "Medicine Ball Sit-Up": "core e addominali",
  "Pelvic Tilts": "core e addominali",
  "Fitball V-Pass": "core e addominali",
  "Stability Ball Crunches": "core e addominali",
  "Fitball Elevated Leg Crunches": "core e addominali",
  "Fitball Overhead Roll-Ups": "core e addominali",
  "Fitball Back Extensions": "core e addominali",

  // stretching e mobilità
  "Kneeling Stability Stretch": "stretching e mobilità",
  "Side Lean with Leg Support": "stretching e mobilità",
  "Arm Raises on Fitball": "stretching e mobilità",
  "Fitball Lat Stretch": "stretching e mobilità",
  "Stability Ball Active Sitting": "stretching e mobilità",
  "Overhead Ball Side Bends": "stretching e mobilità",

  // full body ed esplosività
  "Medicine Ball Burpees (con push-up sulla spalla)": "full body ed esplosività",
  "Medicine Ball Burpee": "full body ed esplosività",
  "Medicine Ball Thrusters": "full body ed esplosività",
  "Medicine Ball Halos": "full body ed esplosività",
};

function ExerciseListPage() {
  const [selectedExercise, setSelectedExercise] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
  const navigate = useNavigate(); // Aggiungi questo hook
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('Tutti');
  const [addedExercises, setAddedExercises] = useState([]);

  const persistSelectedExercises = (list) => {
    try {
      localStorage.setItem('selectedExercises', JSON.stringify(list));
    } catch (e) {
      console.warn('Impossibile salvare selectedExercises in localStorage', e);
    }
  };

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

  const handleAddExercise = (exerciseName) => {
    setAddedExercises((prev) => {
      if (prev.includes(exerciseName)) return prev;
      const next = [...prev, exerciseName];
      persistSelectedExercises(next);
      return next;
    });
  };

  const handleRemoveExercise = (exerciseName) => {
    setAddedExercises((prev) => {
      const next = prev.filter((x) => x !== exerciseName);
      persistSelectedExercises(next);
      return next;
    });
  };

  const categories = [
    'Tutti',
    'gambe e glutei',
    'core e addominali',
    'stretching e mobilità',
    'full body ed esplosività',
  ];

  const filteredExercises = dailyExercises.filter((exerciseName) => {
    if (selectedCategory === 'Tutti') return true;
    return exerciseCategoryMap[exerciseName] === selectedCategory;
  });

  return (
    <div className="page-container">
      <div className="glass-card page-card">
        <header className="page-header">
          <h1>Galleria Esercizi</h1>
          
        </header>
        <div className="content-layout">
          <div className="exercise-menu">
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: 'block', marginBottom: 6 }}>
                Filtra per categoria
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                style={{ width: '100%', padding: 8, borderRadius: 8 }}
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
            <ul className="exercise-list">
              {filteredExercises.map((item, index) => (
                <li
                  key={`${item}-${index}`}
                  style={{
                    listStyle: 'none',
                    display: 'flex',
                    gap: 8,
                    alignItems: 'center',
                    marginBottom: 8,
                  }}
                >
                  <button
                    className={
                      selectedExercise === item
                        ? 'exercise-item active-exercise'
                        : 'exercise-item'
                    }
                    onClick={() => handleSelectExercise(item)}
                    style={{ flex: 1 }}
                  >
                    {item}
                  </button>
                </li>
              ))}
            </ul>

            <div style={{ marginTop: 16 }}>
              <h3 style={{ marginBottom: 8 }}>Lista esercizi aggiunti</h3>
              {addedExercises.length === 0 ? (
                <p style={{ opacity: 0.8, margin: 0 }}>
                  Nessun esercizio aggiunto.
                </p>
              ) : (
                <ul style={{ paddingLeft: 18, margin: 0 }}>
                  {addedExercises.map((name) => (
                    <li
                      key={name}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: 10,
                        marginBottom: 6,
                        paddingBottom: 6,
                        borderBottom: '1px solid #8b5a3c',
                      }}
                    >
                      <span>{name}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveExercise(name)}
                        aria-label={`Rimuovi ${name}`}
                        title="Rimuovi"
                        style={{
                          width: 28,
                          height: 28,
                          borderRadius: 6,
                          border: '1px solid #ed3434',
                          background: '#ed3434',
                          color: 'white',
                          cursor: 'pointer',
                          lineHeight: '26px',
                          textAlign: 'center',
                          padding: 0,
                          flex: '0 0 auto',
                        }}
                      >
                        x
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() =>
                  navigate('/allenamento', { state: { selectedExercises: addedExercises } })
                }
                disabled={addedExercises.length === 0}
                style={{
                  padding: '10px 14px',
                  borderRadius: 12,
                  border: '1px solid rgba(255,255,255,0.25)',
                  background: 'rgba(255,255,255,0.10)',
                  color: 'inherit',
                  cursor: addedExercises.length === 0 ? 'not-allowed' : 'pointer',
                  opacity: addedExercises.length === 0 ? 0.6 : 1,
                  boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)',
                }}
              >
                Inizia allenamento
              </button>
            </div>
          </div>
          
          <div className="video-player-panel">
            {/* --- CONDIZIONE CORRETTA: usa videoUrl --- */}
            {videoUrl ? (
              <>
                <div className="video-container">
                  <video key={videoUrl} controls autoPlay loop muted>
                    <source src={videoUrl} type="video/mp4" />
                    Il tuo browser non supporta i video.
                  </video>
                </div>
                <div style={{ marginTop: 12 }}>
                  <button
                    type="button"
                    onClick={() => handleAddExercise(selectedExercise)}
                    disabled={!selectedExercise || addedExercises.includes(selectedExercise)}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: 12,
                      border: 'none',
                      background: '#8b5a3c',
                      color: 'white',
                      cursor:
                        !selectedExercise || addedExercises.includes(selectedExercise)
                          ? 'not-allowed'
                          : 'pointer',
                      opacity:
                        !selectedExercise || addedExercises.includes(selectedExercise) ? 0.6 : 1,
                      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)',
                    }}
                  >
                    Aggiungi
                  </button>
                </div>
              </>
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