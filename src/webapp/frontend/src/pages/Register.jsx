import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom'; // <-- Assicurati che Link sia qui
import './Form.css';

function Register() {
  const [formData, setFormData] = useState({
    nome: '',
    cognome: '',
    data_nascita: '',
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://127.0.0.1:8000/register', formData);
      const { password, ...user } = formData;
      localStorage.setItem('user', JSON.stringify(user));
      alert('Registration successful! Please log in.');
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed.');
    }
  };



    return (
        <div className="form-page-container">
            <div className="glass-card form-card">
                <h2>Crea il tuo account</h2>
                <form onSubmit={handleSubmit}>
                    {/* Corretto: type="text" e name="nome" */}
                    <input type="text" name="nome" placeholder="Nome" onChange={handleChange} required />
                    
                    {/* Corretto: type="text" e name="cognome" */}
                    <input type="text" name="cognome" placeholder="Cognome" onChange={handleChange} required />
                    
                    {/* Aggiunto: Campo per la data di nascita */}
                    <input type="date" name="data_nascita" placeholder="Date of Birth" onChange={handleChange} required />
                    
                    {/* Corretto: name="email" */}
                    <input type="email" name="email" placeholder="Email" onChange={handleChange} required />
                    
                    <input type="password" name="password" placeholder="Password" onChange={handleChange} required />
                    
                    <button type="submit" className="form-button">Registrati</button>
                </form>
                {error && <p className="error-message">{error}</p>}
                <p className="switch-form-text">
                Hai già un account? <Link to="/login" className="switch-form-link">Accedi</Link>
                </p>
            </div>
        </div>
    );
}

export default Register;