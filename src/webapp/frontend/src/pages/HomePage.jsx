import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';

function HomePage() {
  return (
    <div className="home-container">
      <div className="home-content">
        <img src="/divano.png" alt="Divano esercizio" className="home-image" />
        
        <Link to="/visualizza-esercizi" className="start-workout-button">
          Inizia l'allenamento
        </Link>
      </div>
    </div>
  );
}

export default HomePage;