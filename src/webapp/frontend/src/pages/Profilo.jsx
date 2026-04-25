import React, { useMemo, useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../SupabaseClient';
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
  const userEmail = useMemo(() => {
    const cached = localStorage.getItem('user');
    return cached ? JSON.parse(cached)?.email : null;
  }, []);

  // Stati per i dati da Supabase
  const [userProfileData, setUserProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  // Stati per editing
  const [isEditing, setIsEditing] = useState(false);
  const [editNome, setEditNome] = useState('');
  const [editCognome, setEditCognome] = useState('');
  const [editDobIso, setEditDobIso] = useState('');
  const [editError, setEditError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Carica i dati del profilo da Supabase
  useEffect(() => {
    const loadProfileData = async () => {
      if (!userEmail) {
        setLoadError('Email non trovata');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const { data, error } = await supabase
          .from('profili')
          .select('email, nome, cognome, data_nascita')
          .eq('email', userEmail)
          .single();

        if (error) throw error;

        setUserProfileData(data);
        // Inizializza i campi di editing
        setEditNome(data?.nome || '');
        setEditCognome(data?.cognome || '');
        setEditDobIso(toIsoDate(data?.data_nascita || ''));
        setLoadError(null);
      } catch (err) {
        console.error('Errore nel caricamento del profilo:', err);
        setLoadError('Errore nel caricamento del profilo');
        setUserProfileData(null);
      } finally {
        setLoading(false);
      }
    };

    loadProfileData();
  }, [userEmail]);

  if (!token) {
    navigate('/login');
    return null;
  }

  if (loading) {
    return (
      <div className="form-page-container profile-center">
        <div className="form-card profile-card">
          <p style={{ textAlign: 'center' }}>Caricamento profilo...</p>
        </div>
      </div>
    );
  }

  if (loadError || !userProfileData) {
    return (
      <div className="form-page-container profile-center">
        <div className="form-card profile-card">
          <p style={{ textAlign: 'center', color: '#ed3434' }}>{loadError || 'Profilo non trovato'}</p>
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <button className="form-button" onClick={() => navigate('/')} type="button">
              Torna alla Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  const nome = userProfileData?.nome || '';
  const cognome = userProfileData?.cognome || '';
  const dataNascita = safeDate(userProfileData?.data_nascita || '');
  const email = userProfileData?.email || '';

  const handleStartEdit = () => {
    setEditError('');
    setEditNome(userProfileData?.nome || '');
    setEditCognome(userProfileData?.cognome || '');
    setEditDobIso(toIsoDate(userProfileData?.data_nascita || ''));
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setEditError('');
    setIsEditing(false);
  };

  const handleSave = async () => {
    const nomeTrim = (editNome || '').trim();
    const cognomeTrim = (editCognome || '').trim();
    const dobIso = (editDobIso || '').trim();

    if (!nomeTrim) return setEditError('Inserisci il nome.');
    if (!cognomeTrim) return setEditError('Inserisci il cognome.');
    if (!dobIso) return setEditError('Inserisci la data di nascita.');
    if (!isAdultIsoDate(dobIso)) return setEditError('Devi essere maggiorenne (almeno 18 anni).');

    try {
      setIsSaving(true);
      setEditError('');

      // Aggiorna Supabase
      const { error } = await supabase
        .from('profili')
        .update({
          nome: nomeTrim,
          cognome: cognomeTrim,
          data_nascita: dobIso,
        })
        .eq('email', email);

      if (error) throw error;

      // Aggiorna lo state locale
      setUserProfileData({
        ...userProfileData,
        nome: nomeTrim,
        cognome: cognomeTrim,
        data_nascita: dobIso,
      });

      setIsEditing(false);
    } catch (err) {
      console.error('Errore nel salvataggio:', err);
      setEditError(err?.message || 'Salvataggio fallito.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="classcard">
    <div className="form-page-container profile-center">
      <div className="form-card profile-card">
        <h2>Profilo</h2>
        <p className="form-subtitle">Dati del tuo account</p>
  
        <div className="profile-avatar">
          {userProfileData?.avatar_url
            ? <img src={userProfileData.avatar_url} alt="avatar" />
            : <span>{getInitials(userProfileData)}</span>}
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
                <button className="form-button form-button--secondary" onClick={handleCancelEdit} type="button" disabled={isSaving}>
                  Annulla
                </button>
                <button className="form-button" onClick={handleSave} type="button" disabled={isSaving}>
                  {isSaving ? 'Salvataggio...' : 'Salva'}
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
