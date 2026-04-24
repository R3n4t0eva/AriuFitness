import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom'; // <-- Assicurati che Link sia qui
import './Form.css';
import { createClient } from '@supabase/supabase-js';

import { supabase } from '../SupabaseClient'; // Importa il client Supabase
function Login() {
    const [formData, setFormData] = useState({
        username: '', // L'endpoint /token si aspetta 'username'
        password: '',
    });
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };
    
    const handleSubmit = async (e) => {
      e.preventDefault();
      setError('');

      // 1. Esegui il login direttamente su Supabase
      const { data, error } = await supabase.auth.signInWithPassword({
        email: formData.username,
        password: formData.password,
      });

      if (error) {
        setError(error.message);
        return;
      }

      // 2. Supabase gestisce già il token per te
      const session = data.session;
      localStorage.setItem('token', session.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      navigate('/');
      window.location.reload();
    };

    return (
        <div className="form-page-container">
          <div className="glass-card form-card">
            {/* IL TITOLO WELCOME BACK TORNA QUI */}
            <h2>Welcome Back!</h2> 
            
            <p className="form-subtitle">Accedi per continuare il tuo viaggio</p>
            <form onSubmit={handleSubmit}>
              <input type="email" name="username" placeholder="Email" onChange={handleChange} required />
              <input type="password" name="password" placeholder="Password" onChange={handleChange} required />
              <button type="submit" className="form-button">Accedi</button>
            </form>
            {error && <p className="error-message">{error}</p>}
            <p className="switch-form-text">
              Non hai un account? <Link to="/register" className="switch-form-link">Registrati</Link>
            </p>
          </div>
        </div>
      );
}

export default Login;