import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layers2, Lock, Mail, ArrowRight, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleToggleMode = () => {
    setIsRegister(!isRegister);
    setError('');
    setSuccessMsg('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);

    try {
      if (isRegister) {
        // Register calling POST /api/v1/auth/register
        await api.post('/auth/register', {
          email,
          password,
          full_name: fullName,
        });

        // Automatically log in with newly created credentials
        await login(email, password);
        navigate('/');
      } else {
        // Sign in
        await login(email, password);
        navigate('/');
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg || JSON.stringify(d)).join(', '));
      } else if (err?.message) {
        setError(err.message);
      } else {
        setError(isRegister ? 'Registration failed' : 'Invalid email or password');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-main)',
        padding: '1.5rem',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 420,
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-md)',
          padding: '2.5rem 2rem',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div
            style={{
              width: 44,
              height: 44,
              margin: '0 auto 1rem',
              borderRadius: 'var(--radius-md)',
              background: 'var(--primary)',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Layers2 size={24} />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem' }}>Brightloop</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Subscription & Recurring Billing Management
          </p>
        </div>

        {/* Tab switch between Sign In and Create Account */}
        <div
          style={{
            display: 'flex',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--bg-subtle)',
            padding: '4px',
            marginBottom: '1.5rem',
          }}
        >
          <button
            type="button"
            onClick={() => {
              setIsRegister(false);
              setError('');
              setSuccessMsg('');
            }}
            style={{
              flex: 1,
              padding: '0.5rem',
              fontSize: '0.875rem',
              fontWeight: !isRegister ? 600 : 500,
              borderRadius: 'var(--radius-sm)',
              backgroundColor: !isRegister ? 'var(--bg-card)' : 'transparent',
              color: !isRegister ? 'var(--text-primary)' : 'var(--text-muted)',
              boxShadow: !isRegister ? 'var(--shadow-sm)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setIsRegister(true);
              setError('');
              setSuccessMsg('');
            }}
            style={{
              flex: 1,
              padding: '0.5rem',
              fontSize: '0.875rem',
              fontWeight: isRegister ? 600 : 500,
              borderRadius: 'var(--radius-sm)',
              backgroundColor: isRegister ? 'var(--bg-card)' : 'transparent',
              color: isRegister ? 'var(--text-primary)' : 'var(--text-muted)',
              boxShadow: isRegister ? 'var(--shadow-sm)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div
            style={{
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-md)',
              background: 'var(--danger-bg)',
              color: 'var(--danger-text)',
              fontSize: '0.875rem',
              marginBottom: '1.25rem',
              border: '1px solid rgba(239, 68, 68, 0.2)',
            }}
          >
            {error}
          </div>
        )}

        {successMsg && (
          <div
            style={{
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-md)',
              background: 'var(--success-bg)',
              color: 'var(--success-text)',
              fontSize: '0.875rem',
              marginBottom: '1.25rem',
              border: '1px solid rgba(16, 185, 129, 0.2)',
            }}
          >
            {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {isRegister && (
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  className="form-input"
                  style={{ paddingLeft: '2.3rem' }}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="John Doe"
                  required
                />
                <User
                  size={16}
                  color="var(--text-muted)"
                  style={{ position: 'absolute', left: 12, top: 12 }}
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                className="form-input"
                style={{ paddingLeft: '2.3rem' }}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                required
              />
              <Mail
                size={16}
                color="var(--text-muted)"
                style={{ position: 'absolute', left: 12, top: 12 }}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                className="form-input"
                style={{ paddingLeft: '2.3rem' }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
              />
              <Lock
                size={16}
                color="var(--text-muted)"
                style={{ position: 'absolute', left: 12, top: 12 }}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.7rem', marginTop: '0.5rem' }}
            disabled={loading}
          >
            {loading
              ? isRegister
                ? 'Creating account...'
                : 'Authenticating...'
              : isRegister
              ? 'Create Account'
              : 'Sign In'}
            <ArrowRight size={16} />
          </button>
        </form>

        <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          {isRegister ? (
            <span>
              Already have an account?{' '}
              <button
                type="button"
                onClick={handleToggleMode}
                style={{ color: 'var(--primary)', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Sign In
              </button>
            </span>
          ) : (
            <span>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={handleToggleMode}
                style={{ color: 'var(--primary)', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Create Account
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
