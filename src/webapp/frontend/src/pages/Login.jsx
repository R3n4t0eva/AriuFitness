import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom'; // <-- Assicurati che Link sia qui
import './Form.css';

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
      const params = new URLSearchParams();
      params.append('username', formData.username);
      params.append('password', formData.password);
    
      try {
        const response = await axios.post('http://127.0.0.1:8000/token', params);
        const token = response.data.access_token;
        localStorage.setItem('token', token);
        localStorage.setItem('token', response.data.access_token);
        const cached = localStorage.getItem('user');
        if (!cached) {
          localStorage.setItem('user', JSON.stringify({ email: formData.username }));
        }
        navigate('/');
        window.location.reload();
        let user = null;
        try {
          const r1 = await axios.get('http://127.0.0.1:8000/users/me', {
            headers: { Authorization: `Bearer ${token}` }
          });
          user = r1.data;
        } catch {
          try {
            const r2 = await axios.get('http://127.0.0.1:8000/me', {
              headers: { Authorization: `Bearer ${token}` }
            });
            user = r2.data;
          } catch {
            user = { email: formData.username }; // fallback minimo
          }
        }
        localStorage.setItem('user', JSON.stringify(user));
    
        navigate('/');
        window.location.reload();
      } catch (err) {
        setError(err.response?.data?.detail || 'Login failed.');
      }
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