import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css'; // Creeremo questo file per lo stile

function HomePage() {
  return (
    <div className="home-container">
      <div className="glass-card home-card">
        <h1>Benvenuto in FitnessAI!</h1>
        <p className="home-subtitle">Cosa vuoi fare oggi?</p>
        
        <div className="button-container">
          <Link to="/allenamento" className="choice-button">
            <span className="button-title">Inizia Allenamento</span>
            <span className="button-description">Avvia la sessione live con la webcam per il riconoscimento degli esercizi.</span>
          </Link>
          
          <Link to="/visualizza-esercizi" className="choice-button">
            <span className="button-title">Visualizza Esercizi</span>
            <span className="button-description">Esplora la lista degli esercizi disponibili e guarda i video tutorial.</span>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default HomePage;