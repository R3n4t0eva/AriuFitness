// src/pages/Profilo.jsx
import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import './Form.css'; // riuso stile esistente (form-page-container, form-card, form-button, ...)

function getInitials(user) {
  const name = (user?.nome || user?.first_name || user?.name || '').trim();
  const surname = (user?.cognome || user?.last_name || '').trim();
  if (name || surname) return `${name?.[0] || ''}${surname?.[0] || ''}`.toUpperCase();
  const email = user?.email || '';
  const first = email.split('@')[0] || 'U';
  return first.slice(0, 2).toUpperCase();
}

function safeDate(it) {
  // accetta "YYYY-MM-DD" e lo rende "DD/MM/YYYY"; altrimenti lascia com'è
  if (typeof it !== 'string') return it;
  const m = it.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return it;
  return `${m[3]}/${m[2]}/${m[1]}`;
}

function Row({ label, value }) {
  if (!value) return null; // non mostrare la riga se il campo manca
  return (
    <div className="profile-row">
      <span className="profile-label">{label}</span>
      <span className="profile-value">{value}</span>
    </div>
  );
}

export default function Profilo() {
  const navigate = useNavigate();
  const token = useMemo(() => localStorage.getItem('token'), []);
  const user = useMemo(() => {
    const cached = localStorage.getItem('user');
    return cached ? JSON.parse(cached) : null;
  }, []);

  if (!token) {
    navigate('/login');
    return null;
  }

  const nome = user?.nome || user?.first_name || user?.name || '';
  const cognome = user?.cognome || user?.last_name || '';
  const dataNascita = safeDate(user?.data_nascita || user?.birthdate || '');
  const email = user?.email || '';

  return (
    <div className="classcard">
    <div className="form-page-container profile-center">
      <div className="form-card profile-card">
        <h2>Profilo</h2>
        <p className="form-subtitle">Dati del tuo account</p>
  
        <div className="profile-avatar">
          {user?.avatar_url
            ? <img src={user.avatar_url} alt="avatar" />
            : <span>{getInitials(user)}</span>}
        </div>
  
        {/* Riquadro interno con lo stesso stile tipografico e colore della glass card */}
        
          <div className="profile-info-grid">
            <Row label="Nome" value={nome} />
            <Row label="Cognome" value={cognome} />
            <Row label="Data di nascita" value={dataNascita} />
            <Row label="Email" value={email} />
          </div>
  
          <div className="profile-actions">
            <button className="form-button" onClick={() => navigate('/')}>
              Torna alla Home
            </button>
          </div>
        </div>
      </div>
    </div>
  );
  
}
