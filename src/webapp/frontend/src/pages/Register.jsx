import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom'; // <-- Assicurati che Link sia qui
import './Form.css';
import { supabase } from '../SupabaseClient'; // Importa il client Supabase

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
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validazione maggiorenne 
    const birthDate = new Date(formData.data_nascita);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    if (today < new Date(birthDate.setFullYear(today.getFullYear()))) age--;

    if (age < 18) {
      setError('Devi essere maggiorenne per registrarti.');
      return;
    }

    // --- VALIDAZIONE PASSWORD ---
    const password = formData.password;
    
    // Requisiti: 8 caratteri, 1 Maiuscola, 1 Minuscola, 1 Numero, 1 Segno Speciale
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;

    if (!passwordRegex.test(password)) {
      setError(
        'La password deve contenere almeno 8 caratteri, una maiuscola, una minuscola, un numero e un carattere speciale (@$!%*?&).'
      );
      return;
    }

    try {
      // STEP 1: Registrazione ufficiale su Supabase Auth
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: formData.email,
        password: formData.password,
      });

      if (authError) throw authError;

      // STEP 2: Inserimento dati extra nella tabella 'profili'
      if (authData.user) {
        const { error: profileError } = await supabase
          .from('profili')
          .insert([
            {
              id: authData.user.id,
              email: formData.email,
              nome: formData.nome,
              cognome: formData.cognome,
              data_nascita: formData.data_nascita
            },
          ]);

        if (profileError) throw profileError;
      }

      alert('Registrazione completata! Controlla la mail (se attiva) o vai al login.');
      navigate('/login');

    } catch (err) {
      console.error('Errore:', err);
      setError(err.message || 'Errore durante la registrazione');
    }
  };
  
    const togglePasswordVisibility = () => {
      setShowPassword(!showPassword);
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
                    
                    <div className="password-container">
                    <input type={showPassword ? 'text' : 'password'} name="password" placeholder="Password" onChange={handleChange} required />
                    <button type="button" className="show-password-button" onClick={togglePasswordVisibility}>
                      {showPassword ? "Nascondi" : "Mostra"}
                    </button>
                    </div>
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