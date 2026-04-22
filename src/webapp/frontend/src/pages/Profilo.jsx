import React, { useMemo, useState } from 'react';
import axios from 'axios';
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

function toIsoDate(value) {
  if (typeof value !== 'string') return '';
  const v = value.trim();
  if (!v) return '';
  if (/^\d{4}-\d{2}-\d{2}$/.test(v)) return v;
  const m = v.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return '';
  return `${m[3]}-${m[2]}-${m[1]}`;
}

function formatIsoDate(d) {
  const yyyy = String(d.getFullYear()).padStart(4, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

function adultIsoMaxDate() {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setFullYear(d.getFullYear() - 18);
  return formatIsoDate(d);
}

function isAdultIsoDate(iso) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(iso)) return false;
  const [y, m, d] = iso.split('-').map((x) => Number(x));
  const date = new Date(y, m - 1, d);
  if (Number.isNaN(date.getTime())) return false;
  // Controllo che non "ribalti" la data (es. 2024-02-31 -> marzo)
  if (date.getFullYear() !== y || date.getMonth() !== m - 1 || date.getDate() !== d) return false;

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const adultCutoff = new Date(today);
  adultCutoff.setFullYear(adultCutoff.getFullYear() - 18);
  return date <= adultCutoff;
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

  const initialNome = user?.nome || user?.first_name || user?.name || '';
  const initialCognome = user?.cognome || user?.last_name || '';
  const initialDobIso = toIsoDate(user?.data_nascita || user?.birthdate || '');

  const [isEditing, setIsEditing] = useState(false);
  const [editNome, setEditNome] = useState(initialNome);
  const [editCognome, setEditCognome] = useState(initialCognome);
  const [editDobIso, setEditDobIso] = useState(initialDobIso);
  const [editError, setEditError] = useState('');

  if (!token) {
    navigate('/login');
    return null;
  }

  const nome = initialNome;
  const cognome = initialCognome;
  const dataNascita = safeDate(user?.data_nascita || user?.birthdate || '');
  const email = user?.email || '';

  const handleStartEdit = () => {
    setEditError('');
    setEditNome(initialNome);
    setEditCognome(initialCognome);
    setEditDobIso(initialDobIso);
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setEditError('');
    setIsEditing(false);
  };

  const handleSave = () => {
    const nomeTrim = (editNome || '').trim();
    const cognomeTrim = (editCognome || '').trim();
    const dobIso = (editDobIso || '').trim();

    if (!nomeTrim) return setEditError('Inserisci il nome.');
    if (!cognomeTrim) return setEditError('Inserisci il cognome.');
    if (!dobIso) return setEditError('Inserisci la data di nascita.');
    if (!isAdultIsoDate(dobIso)) return setEditError('Devi essere maggiorenne (almeno 18 anni).');

    (async () => {
      try {
        const r = await axios.put(
          'http://127.0.0.1:8000/users/me',
          { nome: nomeTrim, cognome: cognomeTrim, data_nascita: dobIso },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        localStorage.setItem('user', JSON.stringify(r.data));
        setIsEditing(false);
        window.location.reload();
      } catch (err) {
        const msg = err?.response?.data?.detail || 'Salvataggio fallito.';
        setEditError(String(msg));
      }
    })();
  };

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
            {isEditing ? (
              <div className="profile-row">
                <span className="profile-label">Nome</span>
                <span className="profile-value">
                  <input
                    className="profile-input"
                    type="text"
                    value={editNome}
                    onChange={(e) => setEditNome(e.target.value)}
                    autoComplete="given-name"
                    required
                  />
                </span>
              </div>
            ) : (
              <Row label="Nome" value={nome} />
            )}

            {isEditing ? (
              <div className="profile-row">
                <span className="profile-label">Cognome</span>
                <span className="profile-value">
                  <input
                    className="profile-input"
                    type="text"
                    value={editCognome}
                    onChange={(e) => setEditCognome(e.target.value)}
                    autoComplete="family-name"
                    required
                  />
                </span>
              </div>
            ) : (
              <Row label="Cognome" value={cognome} />
            )}

            {isEditing ? (
              <div className="profile-row">
                <span className="profile-label">Data di nascita</span>
                <span className="profile-value">
                  <input
                    className="profile-input"
                    type="date"
                    value={editDobIso}
                    onChange={(e) => setEditDobIso(e.target.value)}
                    max={adultIsoMaxDate()}
                    required
                  />
                </span>
              </div>
            ) : (
              <Row label="Data di nascita" value={dataNascita} />
            )}
            <Row label="Email" value={email} />
          </div>

          {isEditing && editError ? <p className="error-message">{editError}</p> : null}
  
          <div className="profile-actions">
            {isEditing ? (
              <>
                <button className="form-button form-button--secondary" onClick={handleCancelEdit} type="button">
                  Annulla
                </button>
                <button className="form-button" onClick={handleSave} type="button">
                  Salva
                </button>
              </>
            ) : (
              <>
                <button className="form-button form-button--secondary" onClick={handleStartEdit} type="button">
                  Modifica
                </button>
                <button className="form-button" onClick={() => navigate('/')} type="button">
                  Torna alla Home
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
  
}
