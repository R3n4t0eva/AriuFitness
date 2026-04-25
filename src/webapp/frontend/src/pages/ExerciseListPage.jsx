import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './ExerciseListPage.css'; // Creeremo questo file per lo stile
import { useNavigate } from 'react-router-dom';
import '../Dashboard.css'; // Per importare lo stile del bottone logout
import { supabase } from '../SupabaseClient';

function ExerciseListPage() {
  const [selectedExercise, setSelectedExercise] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
  const navigate = useNavigate();
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('Tutti');
  const [addedExercises, setAddedExercises] = useState([]);
  const [exercises, setExercises] = useState([]);
  const [categories, setCategories] = useState(['Tutti']);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedExerciseDetails, setSelectedExerciseDetails] = useState(null);
  const [showDescriptionModal, setShowDescriptionModal] = useState(false);

  // Carica gli esercizi dal database
  useEffect(() => {
    const loadExercises = async () => {
      try {
        setLoading(true);
        const { data, error } = await supabase
          .from('esercizi')
          .select('id, nome, zona_allenamento, video_tut_url, palla, descrizione');

        if (error) {
          throw error;
        }

        if (data) {
          setExercises(data);
          // Estrai le categorie uniche dai dati
          const uniqueCategories = [...new Set(data.map(ex => ex.zona_allenamento).filter(Boolean))];
          setCategories(['Tutti', ...uniqueCategories.sort()]);
        }
        setError(null);
      } catch (err) {
        console.error('Errore nel caricamento degli esercizi:', err);
        setError('Errore nel caricamento degli esercizi');
      } finally {
        setLoading(false);
      }
    };

    loadExercises();
  }, []);

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

  const handleSelectExercise = (exercise) => {
    setSelectedExercise(exercise.nome);
    setSelectedExerciseDetails(exercise);
    if (exercise.video_tut_url) {
      setVideoUrl(exercise.video_tut_url);
    } else {
      console.warn(`URL video non trovato per l'esercizio: ${exercise.nome}`);
      setVideoUrl('');
    }
  };

  const handleAddExercise = () => {
    if (!selectedExerciseDetails) return;
    setAddedExercises((prev) => {
      // Controlla se l'esercizio è già stato aggiunto (tramite ID)
      if (prev.some((ex) => ex.id === selectedExerciseDetails.id)) return prev;
      const next = [...prev, selectedExerciseDetails];
      persistSelectedExercises(next);
      return next;
    });
  };

  const handleRemoveExercise = (exerciseId) => {
    setAddedExercises((prev) => {
      const next = prev.filter((ex) => ex.id !== exerciseId);
      persistSelectedExercises(next);
      return next;
    });
  };

  // Filtra gli esercizi in base alla categoria selezionata
  const filteredExercises = exercises.filter((exercise) => {
    if (selectedCategory === 'Tutti') return true;
    return exercise.zona_allenamento === selectedCategory;
  });

  return (
    <div className="page-container">
      <div className="glass-card page-card">
        <header className="page-header">
          <h1>Galleria Esercizi</h1>
          
        </header>
        {loading ? (
          <div style={{ padding: 20, textAlign: 'center' }}>
            <p>Caricamento esercizi...</p>
          </div>
        ) : error ? (
          <div style={{ padding: 20, textAlign: 'center', color: '#ed3434' }}>
            <p>{error}</p>
          </div>
        ) : (
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
                {filteredExercises.map((exercise) => (
                  <li
                    key={exercise.id}
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
                        selectedExercise === exercise
                          ? 'exercise-item active-exercise'
                          : 'exercise-item'
                      }
                      onClick={() => handleSelectExercise(exercise)}
                      style={{ flex: 1 }}
                    >
                      {exercise.nome}
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
                  {addedExercises.map((exercise) => (
                    <li
                      key={exercise.id}
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
                      <span>{exercise.nome}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveExercise(exercise.id)}
                        aria-label={`Rimuovi ${exercise.nome}`}
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
                <div style={{ marginTop: 12, display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                  {selectedExerciseDetails?.palla && (
                    <div style={{
                      flex: 1,
                      padding: 12,
                      borderRadius: 8,
                      background: 'rgba(59, 130, 246, 0.15)',
                      border: '2px solid #3b82f6',
                    }}>
                      <p style={{ margin: 0, marginBottom: 6, fontSize: 12, opacity: 0.8 }}>
                        Dimensioni palla da usare:
                      </p>
                      <p style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#3b82f6' }}>
                        {selectedExerciseDetails.palla + " cm"}
                      </p>
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      type="button"
                      onClick={() => handleAddExercise()}
                      disabled={!selectedExercise || addedExercises.some((ex) => ex.id === selectedExerciseDetails?.id)}
                      style={{
                        padding: '10px 14px',
                        borderRadius: 12,
                        border: 'none',
                        background: '#8b5a3c',
                        color: 'white',
                        cursor:
                          !selectedExercise || addedExercises.some((ex) => ex.id === selectedExerciseDetails?.id)
                            ? 'not-allowed'
                            : 'pointer',
                        opacity:
                          !selectedExercise || addedExercises.some((ex) => ex.id === selectedExerciseDetails?.id) ? 0.6 : 1,
                        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)',
                        fontWeight: 500,
                        minWidth: 100,
                      }}
                    >
                      Aggiungi
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowDescriptionModal(true)}
                      title="Leggi la descrizione dell'esercizio"
                      style={{
                        width: 30,
                        height: 50,
                        borderRadius: '50%',
                        border: '2px solid #3437ed',
                        background: '#3437ed',
                        color: 'white',
                        cursor: 'pointer',
                        fontSize: 20,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      ⓘ
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="video-placeholder">
                <p>Seleziona un esercizio dalla lista per vedere il tutorial.</p>
              </div>
            )}
          </div>
        </div>        )}
        
        {/* Modal per la descrizione dell'esercizio */}
        {showDescriptionModal && selectedExerciseDetails && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
              padding: 16,
            }}
            onClick={() => setShowDescriptionModal(false)}
          >
            <div
              style={{
                background: 'white',
                borderRadius: 12,
                padding: 24,
                maxWidth: 500,
                width: '100%',
                maxHeight: '80vh',
                overflowY: 'auto',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h2 style={{ margin: 0, color: '#333' }}>
                  {selectedExerciseDetails.nome}
                </h2>
                <button
                  type="button"
                  onClick={() => setShowDescriptionModal(false)}
                  style={{
                    background: 'none',
                    border: 'none',
                    fontSize: 24,
                    cursor: 'pointer',
                    color: '#999',
                  }}
                >
                  ✕
                </button>
              </div>
              
              <div style={{ marginBottom: 16 }}>
                <h3 style={{ margin: '0 0 8px 0', color: '#8b5a3c', fontSize: 14 }}>
                  Descrizione
                </h3>
                <p style={{ margin: 0, color: '#555', lineHeight: 1.6 }}>
                  {selectedExerciseDetails.descrizione || 'Nessuna descrizione disponibile.'}
                </p>
              </div>
              
              {selectedExerciseDetails.palla && (
                <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 8 }}>
                  <h3 style={{ margin: '0 0 8px 0', color: '#8b5a3c', fontSize: 14 }}>
                    Attrezzo utilizzato
                  </h3>
                  <p style={{ margin: 0, color: '#555', fontWeight: 500 }}>
                    {selectedExerciseDetails.palla}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ExerciseListPage;