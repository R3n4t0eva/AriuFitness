import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './GlobalHeader.css';

const GlobalHeader = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const showAuthButtons = location.pathname !== '/login' && location.pathname !== '/register';

  const [user, setUser] = useState(null);
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const cached = localStorage.getItem('user');
    if (cached) setUser(JSON.parse(cached));
  }, []);

  useEffect(() => {
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('click', onClick);
    return () => document.removeEventListener('click', onClick);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const initials = (u) => {
    const name = (u?.nome || u?.first_name || u?.name || '').trim();
    const surname = (u?.cognome || u?.last_name || '').trim();
    const n = name?.[0] || '';
    const s = surname?.[0] || (n ? '' : (u?.email?.[0] || 'U'));
    return (n + s).toUpperCase();
  };
  
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <header className="global-header">
      <div className="brand-section">
        <div className="app-logo">AI</div>
        <span className="app-title-global">FITNESS AI</span>
      </div>

      {showAuthButtons && (
        <div className="header-buttons">
          <Link to="/" className="back-button">Home</Link>

          {localStorage.getItem('token') ? (
            <div className="profile-wrap" ref={menuRef}>
              <button
                aria-label="Apri menu profilo"
                className="avatar-btn"
                onClick={() => setOpen(v => !v)}
              >
                {user?.avatar_url
                  ? <img src={user.avatar_url} alt="avatar" />
                  : <span>{initials(user)}</span>
                }
              </button>

              {open && (
                <div className="gh-menu">
                  <div className="gh-user-row">
                    <div className="gh-avatar small">
                      {user?.avatar_url ? <img src={user.avatar_url} alt="avatar" /> : <span>{initials(user)}</span>}
                    </div>
                    <div className="gh-user-info">
                      <div className="gh-name">Utente</div>
                      <div className="gh-email">{user?.email ?? '—'}</div>
                    </div>
                  </div>

                  <div className="gh-divider" />

                  <Link to="/profilo" className="menu-btn" onClick={() => setOpen(false)}>
                    Profilo
                  </Link>
                  <button className="menu-btn danger" onClick={logout}>
                    Logout
                  </button>
                </div>
              )}

            </div>
          ) : (
            // se non loggato, mantieni solo Home (o potresti aggiungere link Login/Register)
            <button onClick={handleLogout} className="logout-button">Logout</button>
          )}
        </div>
      )}
    </header>
  );
};

export default GlobalHeader;